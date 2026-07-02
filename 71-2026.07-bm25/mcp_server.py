"""
MCP server — exposes search_repo_knowledge as a callable tool.

Add to Claude Code (.claude/settings.json) or any MCP-compatible client:

    {
      "mcpServers": {
        "repo-bm25": {
          "command": "python",
          "args": ["/absolute/path/to/mcp_server.py"],
          "env": {
            "REPO_PATH": "/absolute/path/to/your/repo"
          }
        }
      }
    }

Or point at any repo at runtime using the repo_path tool argument.

Environment variables:
    REPO_PATH   Default repository root (defaults to cwd)
    BM25_TOP_K  Default number of results (defaults to 5)
"""

import json
import os
from pathlib import Path
from typing import Any

import fastmcp

import search_repo_knowledge as _srk

mcp = fastmcp.FastMCP(
    name="repo-bm25-search",
    instructions=(
        "Use search_repo_knowledge to explore an unfamiliar repository. "
        "Prefer this over listing directories or reading files speculatively. "
        "Good queries: dependency names, feature names, config keys, error strings, "
        "deployment targets, author names. "
        "Bad queries: single characters, stop words, very broad terms like 'code'."
    ),
)

_DEFAULT_REPO = os.getenv("REPO_PATH", ".")
_DEFAULT_TOP_K = int(os.getenv("BM25_TOP_K", "5"))


@mcp.tool()
def search_repo_knowledge(
    query: str,
    top_k: int = _DEFAULT_TOP_K,
    repo_path: str = _DEFAULT_REPO,
    rebuild: bool = False,
) -> str:
    """
    BM25 search over repository manifests, documentation, and recent git log.

    Use this instead of reading arbitrary files or listing directories.
    The index is built once on first call and cached for the session.

    Args:
        query:     What you're looking for. Use specific terms: library names,
                   config keys, feature names, error strings.
        top_k:     Number of results to return (1–10, default 5).
        repo_path: Absolute path to the repo root. Defaults to REPO_PATH env var.
        rebuild:   Set True to force a fresh index after file edits.

    Returns:
        Formatted string with ranked snippets, file paths, and BM25 scores.
    """
    top_k = max(1, min(top_k, 10))

    try:
        results = _srk.search_repo_knowledge(query, repo_path=repo_path, top_k=top_k, rebuild=rebuild)
    except ValueError as exc:
        return f"Index error: {exc}"

    if not results:
        return f"No results found for '{query}'. Try a more specific term or check REPO_PATH."

    lines = [f"BM25 results for '{query}' in {Path(repo_path).resolve()}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{'─' * 56}")
        lines.append(f"[{i}] {r['file']}  score={r['score']}  type={r['source_type']}")
        lines.append(f"{'─' * 56}")
        snippet = r["text"]
        lines.append(snippet[:800] + ("…" if len(snippet) > 800 else ""))
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def index_stats(repo_path: str = _DEFAULT_REPO) -> str:
    """
    Return statistics about the current BM25 index for a repository.
    Useful for debugging: shows total chunk count broken down by source type.
    """
    key = str(Path(repo_path).resolve())
    if key not in _srk._cache:
        idx = _srk.RepoKnowledgeIndex(key)
        idx.build()
        _srk._cache[key] = idx

    stats = _srk._cache[key].stats()
    return json.dumps(stats, indent=2)


if __name__ == "__main__":
    mcp.run()
