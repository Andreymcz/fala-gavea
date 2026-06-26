#!/usr/bin/env python
"""Offline (re)indexer for the project's own documentation (self-docs RAG).

Walks the configured corpus roots, chunks every .md, classifies role visibility,
and (re)builds the Chroma self-docs collection. The reusable `index_selfdocs`
function is shared by this CLI and the app startup hook (plan-000177 step 9).

Usage:
    uv run python scripts/reindex_selfdocs.py [--dry-run] [--roots a,b] [--if-empty]

Options:
    --dry-run     Walk + classify + print counts WITHOUT loading the model or
                  writing to Chroma. Also lists excluded sensitive files found.
    --roots a,b   Override corpus roots (comma-separated, repo-relative).
    --if-empty    Only (re)index when the collection is currently empty.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# Ensure the src package is importable when run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sentence_transformers import SentenceTransformer

from fala_gavea.infrastructure.chromadb.chroma_doc_search_client import ChromaDocSearchClient
from fala_gavea.infrastructure.docs.markdown_chunker import is_excluded, walk_corpus
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig


def repo_root() -> str:
    """Absolute path to the repo root (scripts/ lives at <repo>/scripts/)."""
    return str(Path(__file__).resolve().parent.parent)


def tally_corpus(roots: list[str], root: str) -> dict[str, object]:
    """Walk + classify WITHOUT loading the model. Used by --dry-run.

    Returns the public/internal split, by_doc_type counts, total chunk count,
    and the list of excluded sensitive .md files encountered under `roots`.
    """
    chunks = walk_corpus(roots, root)
    public = sum(1 for c in chunks if c.role_visibility == "public")
    internal = sum(1 for c in chunks if c.role_visibility == "internal")
    by_doc_type = Counter(c.doc_type for c in chunks)

    repo = Path(root)
    excluded: list[str] = []
    for r in roots:
        root_dir = repo / r
        if not root_dir.exists():
            continue
        for md_file in sorted(root_dir.rglob("*.md")):
            source_path = md_file.relative_to(repo).as_posix()
            if is_excluded(source_path):
                excluded.append(source_path)

    return {
        "indexed_chunks": len(chunks),
        "public": public,
        "internal": internal,
        "by_doc_type": dict(by_doc_type),
        "excluded": excluded,
        "roots": roots,
    }


def index_selfdocs(*, if_empty: bool = False, roots: list[str] | None = None) -> dict[str, object]:
    """(Re)index the self-docs corpus into the Chroma self-docs collection.

    Reusable by the CLI and the app startup hook. When `if_empty` is True and the
    collection already has rows, this short-circuits (no walk, no model load).
    """
    root = repo_root()
    config = SemanticConfig()
    corpus_roots = roots if roots is not None else config.selfdocs_corpus_roots

    client = ChromaDocSearchClient(config, SentenceTransformer(config.embed_model_search))

    if if_empty and client.count() > 0:
        return {"skipped": True, "reason": "collection not empty", "count": client.count()}

    chunks = walk_corpus(corpus_roots, root)
    client.reindex_all(chunks)

    public = sum(1 for c in chunks if c.role_visibility == "public")
    internal = sum(1 for c in chunks if c.role_visibility == "internal")
    by_doc_type = Counter(c.doc_type for c in chunks)
    return {
        "indexed_chunks": len(chunks),
        "public": public,
        "internal": internal,
        "by_doc_type": dict(by_doc_type),
        "roots": corpus_roots,
    }


def _parse_roots(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _print_dry_run(tally: dict[str, object]) -> None:
    print("DRY RUN — no model loaded, nothing written to Chroma.")
    print(f"  roots:          {tally['roots']}")
    print(f"  total chunks:   {tally['indexed_chunks']}")
    print(f"  public:         {tally['public']}")
    print(f"  internal:       {tally['internal']}")
    print("  by_doc_type:")
    by_doc_type: dict[str, int] = tally["by_doc_type"]  # type: ignore[assignment]
    for doc_type, n in sorted(by_doc_type.items()):
        print(f"    {doc_type}: {n}")
    excluded: list[str] = tally["excluded"]  # type: ignore[assignment]
    print(f"  excluded sensitive files ({len(excluded)}):")
    for path in excluded:
        print(f"    {path}")


def _print_summary(summary: dict[str, object]) -> None:
    if summary.get("skipped"):
        print(f"Skipped: {summary['reason']} (count={summary['count']}).")
        return
    print("Self-docs reindex complete.")
    print(f"  indexed chunks: {summary['indexed_chunks']}")
    print(f"  public:         {summary['public']}")
    print(f"  internal:       {summary['internal']}")
    print("  by_doc_type:")
    by_doc_type: dict[str, int] = summary["by_doc_type"]  # type: ignore[assignment]
    for doc_type, n in sorted(by_doc_type.items()):
        print(f"    {doc_type}: {n}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="(Re)index the project's self-documentation corpus into Chroma."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Walk + classify + print counts without loading the model or writing.",
    )
    parser.add_argument(
        "--roots",
        type=_parse_roots,
        default=None,
        metavar="a,b",
        help="Override corpus roots (comma-separated, repo-relative).",
    )
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Only (re)index when the collection is currently empty.",
    )
    args = parser.parse_args()

    if args.dry_run:
        config = SemanticConfig()
        roots = args.roots if args.roots is not None else config.selfdocs_corpus_roots
        _print_dry_run(tally_corpus(roots, repo_root()))
        return 0

    summary = index_selfdocs(if_empty=args.if_empty, roots=args.roots)
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
