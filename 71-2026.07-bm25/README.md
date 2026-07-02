# poc-repo-bm25-2026

BM25 search over a repository's manifests, docs, and git log — exposed as an MCP tool so long-horizon coding agents can orient themselves without dumping whole directories into their context window.

## Why this exists

Long-horizon coding agents fail in a predictable pattern: they `ls -la` everything, `cat` files speculatively, and fill their context with noise before writing a single line of code. The standard fix is a vector database with embeddings. This POC shows you get 80% of the benefit with none of the infra — just BM25 over the structural knowledge that already exists in every repo.

Indexed sources:

| Source | What it covers |
|--------|---------------|
| Root manifests | `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Makefile`, `Taskfile.yaml`, `.env.example`, `CLAUDE.md`, `AGENTS.md`, etc. |
| Root YAML / YML | CI configs, Helm values, kustomize overlays |
| Documentation | `*.md` at root, everything under `docs/`, `.claude/`, `.github/` |
| Git log | Last 60 commit subjects + bodies |

Not indexed: source code, lock files, binaries. The point is structural knowledge, not full-text search.

## Prerequisites

- Python 3.11+
- A git repository to point it at (it reads `git log` directly)
- Optional: Claude Code or any MCP-compatible client for the server integration

## Setup

```bash
cd <this-folder>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```
REPO_PATH=/absolute/path/to/the/repo/you/want/to/search
```

## Run it

### CLI — ad-hoc queries

```bash
# Search the repo this tool is pointed at
python3 cli.py "database connection pool"

# Point at a different repo inline
python3 cli.py "deploy to kubernetes" --repo ~/repos/my-service --top-k 3

# JSON output for piping
python3 cli.py "auth middleware" --json | jq '.[].file'

# Show index stats (chunk count by source type)
python3 cli.py --stats --repo ~/repos/my-service
```

### MCP server — Claude Code integration

Run the server:
```bash
REPO_PATH=/path/to/repo python3 mcp_server.py
```

Add to your project's `.claude/settings.json` (non-invasive — one block, no code changes):
```json
{
  "mcpServers": {
    "repo-bm25": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/poc-repo-bm25-2026/mcp_server.py"],
      "env": {
        "REPO_PATH": "/absolute/path/to/your/repo"
      }
    }
  }
}
```

After adding, Claude Code gains two new tools:
- `search_repo_knowledge(query, top_k, repo_path)` — ranked BM25 search
- `index_stats(repo_path)` — debug: chunk counts by source type

The MCP server instructions prompt the model to prefer this over directory listing.

### As a Python function

```python
from search_repo_knowledge import search_repo_knowledge

results = search_repo_knowledge(
    "kubernetes deployment resource limits",
    repo_path="/path/to/repo",
    top_k=5,
)
for r in results:
    print(f"{r['score']:.3f}  {r['file']}")
    print(r["text"][:300])
```

The index is built on first call and cached in-process for the lifetime of the interpreter — no warm-up overhead on subsequent queries.

## What to expect

Running against [github.com/olga-mir/playground](https://github.com/olga-mir/playground) — a Crossplane v2 + FluxCD + agentic orchestrator monorepo:

```
$ python3 cli.py "agentic deploy phase orchestrator" --repo ~/repos/playground

Building index for /repos/playground ...

BM25 results for 'agentic deploy phase orchestrator' in /repos/playground

────────────────────────────────────────────────────────────
[1]  docs/agentic-architecture.md   score=8.14   type=doc
────────────────────────────────────────────────────────────
[docs/agentic-architecture.md]
# Agentic Loop — Architecture

The orchestrator is a pure Python application (orchestrator/main.py) that drives cluster
provisioning through three phases: kind bootstrap → GKE control-plane → GKE apps-dev.
It uses DSPy + LiteLLM for all LLM reasoning...

────────────────────────────────────────────────────────────
[2]  .claude/agents/phase-checker.md   score=6.39   type=doc
────────────────────────────────────────────────────────────
[.claude/agents/phase-checker.md]
Evaluates cluster state against healthy criteria for the current phase.
Returns a structured JSON verdict: healthy | wait | diagnose | teardown...

────────────────────────────────────────────────────────────
[3]  README.md   score=4.81   type=doc
────────────────────────────────────────────────────────────
[README.md]
# AI Orchestrator
The provisioning pipeline is driven by a Claude-powered agentic loop that monitors,
diagnoses, and fixes the cluster fleet without human intervention...
```

Another query showing CI/GitOps discovery:

```
$ python3 cli.py "flux bootstrap github actions" --repo ~/repos/playground

────────────────────────────────────────────────────────────
[1]  .github/workflows/flux-bootstrap.yml   score=7.22   type=doc
────────────────────────────────────────────────────────────
[.github/workflows/flux-bootstrap.yml]
name: Flux Bootstrap GKE Clusters
on:
  workflow_dispatch:
    inputs:
      cluster: ...

────────────────────────────────────────────────────────────
[2]  docs/flux-gitops.md   score=5.63   type=doc
────────────────────────────────────────────────────────────
...
```

Index build time on a ~80-file repo: ~120ms. Subsequent queries: <5ms.

**Coverage note for Kubernetes-heavy repos**: `_collect_root_yaml` indexes only root-level YAML files. Deep manifest trees (e.g. `kubernetes/clusters/…`) are not indexed by default. To include them, add `"kubernetes"` to `_DOC_DIRS` in `search_repo_knowledge.py` and extend `_DOC_GLOBS_RECURSIVE` with `"*.yaml"` — or add a dedicated `_collect_k8s_manifests` method that caps file size and skips lock/generated files.

## Key code sections

**Collector pipeline** (`search_repo_knowledge.py` lines 85–130): Three private methods — `_collect_root_manifests`, `_collect_root_yaml`, `_collect_docs` — each know exactly what they're looking for. Adding a new source type means adding one method and calling it from `build()`.

**Tokenizer** (`search_repo_knowledge.py` line 155): `[a-z0-9][a-z0-9_\-\.]*` — keeps underscores and hyphens so `pool_size`, `max-replicas`, and `go.mod` survive tokenization as single tokens. This is the single most impactful tuning point for code search.

**File prefix in chunk text** (`search_repo_knowledge.py` line 130): Every chunk is prefixed with `[relative/path]`. This means the path segments themselves are BM25 tokens — a query for "makefile" will rank `Makefile` chunks higher than docs that happen to mention it.

**MCP server instructions** (`mcp_server.py` line 19): The `instructions` parameter on `FastMCP` is injected into the system prompt. It tells the model when to use this tool and what makes a good vs. bad query. This is the integration point that changes agent behaviour without touching the target repo.

**In-process cache** (`search_repo_knowledge.py` line 163): `_cache: dict[str, RepoKnowledgeIndex]` — module-level dict keyed by resolved path. The MCP server is a long-running process, so the index is built once and reused across tool calls. Pass `rebuild=True` to invalidate.

## Extending

**Add source code search**: Extend `_collect_docs` to include `*.py` or `*.go` files under `src/`. Use a smaller `CHUNK_CHARS` (200–300) and filter by file size more aggressively.

**Swap in a reranker**: Replace `BM25Okapi` with a `CrossEncoder` from `sentence-transformers` in `search()` — the chunk collection and tokenization layers stay the same.

**Multiple repos**: The `_cache` dict supports any number of repos simultaneously. Pass different `repo_path` values to the MCP tool — each gets its own index.

**Wire into SWE-agent**: Define `search_repo_knowledge` as a bash-callable tool in your SWEEnv YAML manifest, pointing at `cli.py --json`. The JSON output is stable and scriptable.

## Source material

Derived from analysis of long-horizon coding agent architectures — specifically the insight from [CoderMind / MemDocAgent research](https://arxiv.org/abs/2402.01413) and the SWE-agent ACI paper that agents need structured retrieval interfaces rather than raw filesystem access.

Key insight that motivated this:
> "Force the agent to rely on a codebase semantic search instead of dumping whole directories into the prompt."

## Further reading

- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793)
- [OpenHands (OpenDevin)](https://github.com/All-Hands-AI/OpenHands)
- [rank-bm25 Python library](https://github.com/dorianbrown/rank_bm25)
- [FastMCP — Python MCP server framework](https://github.com/jlowin/fastmcp)
- [Model Context Protocol spec](https://modelcontextprotocol.io/)
