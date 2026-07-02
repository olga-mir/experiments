#!/usr/bin/env python3
"""
CLI for BM25 repo knowledge search.

Quick ad-hoc queries against any local repository:

    python cli.py "database connection pool" --repo /path/to/myrepo
    python cli.py "deploy kubernetes" --top-k 3 --json
    python cli.py "auth middleware" --stats        # show index stats first
"""

import argparse
import json
import sys
from pathlib import Path

import search_repo_knowledge as _srk
from search_repo_knowledge import search_repo_knowledge


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BM25 search over repo manifests, docs, and git log",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument(
        "--repo", "-r",
        default=".",
        metavar="PATH",
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        metavar="N",
        help="Number of results (default: 5)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild the index (useful after editing files)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print index statistics and exit",
    )
    parser.add_argument(
        "--snippet-len",
        type=int,
        default=500,
        metavar="N",
        help="Max characters to display per snippet (default: 500)",
    )
    args = parser.parse_args()

    repo_path = str(Path(args.repo).resolve())

    # Build (or retrieve from cache) the index
    if args.rebuild or repo_path not in _srk._cache:
        print(f"Building index for {repo_path} ...", file=sys.stderr)
        idx = _srk.RepoKnowledgeIndex(repo_path)
        try:
            idx.build()
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        _srk._cache[repo_path] = idx

    idx = _srk._cache[repo_path]

    if args.stats:
        stats = idx.stats()
        print(json.dumps(stats, indent=2))
        if not args.query:
            return 0

    if not args.query:
        parser.print_help()
        return 1

    results = idx.search(args.query, top_k=args.top_k)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    if not results:
        print(f"No results found for '{args.query}'.")
        return 0

    print(f"\nBM25 results for '{args.query}' in {repo_path}")
    for i, r in enumerate(results, 1):
        bar = "─" * 60
        print(f"\n{bar}")
        print(f"[{i}]  {r['file']}   score={r['score']}   type={r['source_type']}")
        print(bar)
        snippet = r["text"]
        if len(snippet) > args.snippet_len:
            snippet = snippet[: args.snippet_len] + " …"
        print(snippet)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
