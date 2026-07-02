"""
BM25-based repo knowledge search.

Indexes manifests, docs, and recent git log for a repository.
No embeddings, no vector DB — just fast BM25 with a persistent in-process cache.

Usage:
    from search_repo_knowledge import search_repo_knowledge
    results = search_repo_knowledge("database connection pool", repo_path="/path/to/repo")
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import bm25s
from bm25s.tokenization import Tokenizer

# ── tuning knobs ─────────────────────────────────────────────────────────────
MAX_FILE_BYTES = 80_000   # skip files larger than this (avoids lock-files etc.)
CHUNK_CHARS = 600         # target characters per chunk
CHUNK_OVERLAP_CHARS = 80  # overlap between adjacent chunks
GIT_LOG_COMMITS = 60      # how many recent commits to index
# ─────────────────────────────────────────────────────────────────────────────

# Manifest filenames collected at the repo root (not recursed)
_ROOT_MANIFESTS = {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "requirements-prod.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "Taskfile.yaml",
    "Taskfile.yml",
    "Dockerfile",
    ".env.example",
    "AGENTS.md",       # agent instruction files are high-signal
    "CLAUDE.md",
    "GEMINI.md",
}

# Glob patterns for documentation (searched recursively under docs/)
_DOC_GLOBS_RECURSIVE = ["*.md", "*.rst", "*.txt"]
_DOC_DIRS = ["docs", "doc", ".claude", ".github"]


class RepoKnowledgeIndex:
    """BM25 index over a repository's structural knowledge."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.chunks: list[dict[str, Any]] = []
        self._bm25: bm25s.BM25 | None = None
        self._tokenizer: Tokenizer | None = None
        self._built = False
        self._seen_paths: set[str] = set()  # dedup across collectors

    # ── public API ────────────────────────────────────────────────────────────

    def build(self) -> "RepoKnowledgeIndex":
        """Collect content and build the BM25 index. Call once per repo."""
        self.chunks = []
        self._collect_root_manifests()
        self._collect_root_yaml()
        self._collect_docs()
        self._collect_git_log()

        if not self.chunks:
            raise ValueError(
                f"No indexable content found under {self.repo_path}. "
                "Check that the path is a git repo with at least one README or manifest."
            )

        self._tokenizer = Tokenizer(lower=False, splitter=_tokenize, stopwords=None)
        corpus_tokens = self._tokenizer.tokenize(
            [c["text"] for c in self.chunks], update_vocab=True, show_progress=False
        )
        self._bm25 = bm25s.BM25()
        self._bm25.index(corpus_tokens)
        self._built = True
        return self

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Return up to top_k ranked chunks for a query.

        Each result dict has:
            file        — relative path inside the repo (or "git-log")
            source_type — "manifest" | "config" | "doc" | "git-log"
            chunk_id    — stable identifier for the chunk
            text        — chunk text (prefixed with the file path)
            score       — BM25 score (float, higher = more relevant)
        """
        if not self._built:
            self.build()

        query_tokens = self._tokenizer.tokenize([query], update_vocab=False, show_progress=False)
        k = min(top_k, len(self.chunks))
        results_idx, scores_arr = self._bm25.retrieve(query_tokens, k=k)

        results = []
        for doc_idx, score in zip(results_idx[0], scores_arr[0]):
            if score > 0.0:
                chunk = dict(self.chunks[int(doc_idx)])
                chunk["score"] = round(float(score), 4)
                results.append(chunk)
        return results

    def stats(self) -> dict[str, Any]:
        """Return index stats for debugging."""
        by_type: dict[str, int] = {}
        for c in self.chunks:
            by_type[c["source_type"]] = by_type.get(c["source_type"], 0) + 1
        return {
            "repo": str(self.repo_path),
            "total_chunks": len(self.chunks),
            "by_source_type": by_type,
        }

    # ── private collectors ────────────────────────────────────────────────────

    def _collect_root_manifests(self):
        for name in _ROOT_MANIFESTS:
            path = self.repo_path / name
            if path.exists() and path.is_file():
                self._ingest_file(path, source_type="manifest")

    def _collect_root_yaml(self):
        """Index small YAML/YML files at repo root (CI configs, helm values, etc.)."""
        for pat in ("*.yaml", "*.yml"):
            for path in self.repo_path.glob(pat):
                if path.stat().st_size < MAX_FILE_BYTES:
                    self._ingest_file(path, source_type="config")

    def _collect_docs(self):
        """Index README at root, then recurse into known doc directories."""
        # Root-level markdown
        for path in self.repo_path.glob("*.md"):
            self._ingest_file(path, source_type="doc")

        # Known doc dirs
        for doc_dir_name in _DOC_DIRS:
            doc_dir = self.repo_path / doc_dir_name
            if doc_dir.exists() and doc_dir.is_dir():
                for pat in _DOC_GLOBS_RECURSIVE:
                    for path in doc_dir.rglob(pat):
                        if path.is_file():
                            self._ingest_file(path, source_type="doc")

    def _collect_git_log(self):
        """Index the last GIT_LOG_COMMITS commit subjects + bodies."""
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"--max-count={GIT_LOG_COMMITS}",
                    "--format=commit %H%nauthor %an%ndate %ad%n%s%n%n%b%n---END---",
                    "--date=short",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return  # git not available or repo not initialised

        if result.returncode != 0 or not result.stdout.strip():
            return

        for i, block in enumerate(result.stdout.split("\n---END---\n")):
            block = block.strip()
            if block:
                self.chunks.append(
                    {
                        "file": "git-log",
                        "source_type": "git-log",
                        "chunk_id": f"git-log:{i}",
                        "text": block,
                    }
                )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _ingest_file(self, path: Path, source_type: str):
        resolved = str(path.resolve())
        if resolved in self._seen_paths:
            return
        self._seen_paths.add(resolved)
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                return
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                return
        except OSError:
            return

        rel = str(path.relative_to(self.repo_path))
        for i, chunk in enumerate(_chunk(text)):
            self.chunks.append(
                {
                    "file": rel,
                    "source_type": source_type,
                    "chunk_id": f"{rel}:{i}",
                    # Prefix every chunk with the file path so the BM25 tokens
                    # include the path segments — improves filename-based queries.
                    "text": f"[{rel}]\n{chunk}",
                }
            )


# ── module-level helpers ──────────────────────────────────────────────────────

def _chunk(text: str) -> list[str]:
    """Split text into overlapping fixed-size chunks."""
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_CHARS])
        start += CHUNK_CHARS - CHUNK_OVERLAP_CHARS
    return chunks


def _tokenize(text: str) -> list[str]:
    """Lowercase + split on word boundaries; keep underscores and hyphens."""
    return [t for t in re.findall(r"[a-z0-9][a-z0-9_\-\.]*", text.lower()) if len(t) > 1]


# ── in-process cache + public function ───────────────────────────────────────

_cache: dict[str, RepoKnowledgeIndex] = {}


def search_repo_knowledge(
    query: str,
    repo_path: str = ".",
    top_k: int = 5,
    rebuild: bool = False,
) -> list[dict[str, Any]]:
    """
    Search repository knowledge (manifests, docs, git log) using BM25.

    Intended as an agent tool: call this instead of listing or reading
    arbitrary directories. The index is built once per process and cached.

    Args:
        query:     Natural language query, e.g. "database connection string"
        repo_path: Absolute or relative path to the git repo root.
        top_k:     Maximum number of results to return.
        rebuild:   Pass True to force a fresh index (e.g. after editing files).

    Returns:
        List of result dicts sorted by descending BM25 score.
        Empty list if no chunks score above zero.

    Example:
        >>> results = search_repo_knowledge("deployment steps kubernetes")
        >>> for r in results:
        ...     print(r["file"], r["score"])
        ...     print(r["text"][:200])
    """
    key = str(Path(repo_path).resolve())
    if rebuild or key not in _cache:
        index = RepoKnowledgeIndex(key)
        index.build()
        _cache[key] = index
    return _cache[key].search(query, top_k=top_k)
