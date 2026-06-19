#!/usr/bin/env python
"""Backfill existing reports into the ChromaDB semantic vector store.

Usage:
    uv run python scripts/backfill_semantic.py [--batch-size N] [--force]

Options:
    --batch-size N  Number of reports to encode per batch (default: 100)
    --force         Re-index even reports that are already indexed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the src package is importable when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
from fala_gavea.infrastructure.database.session import SessionLocal
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill reports into semantic vector store.")
    parser.add_argument("--batch-size", type=int, default=100, metavar="N")
    parser.add_argument("--force", action="store_true", help="Re-index already-indexed reports")
    args = parser.parse_args()

    config = SemanticConfig()
    client = ChromaSearchClient(config)
    collection = client._collection

    db = SessionLocal()
    try:
        repo = SQLAlchemyReportRepository(db)
        from fala_gavea.domain.repositories.report_repository import ReportFilters
        reports = repo.find_all(ReportFilters())
    finally:
        db.close()

    total = len(reports)
    indexed = 0
    skipped = 0

    print(f"Found {total} reports to process (batch-size={args.batch_size}, force={args.force})")

    for i, report in enumerate(reports):
        if not args.force:
            existing = collection.get(ids=[report.id])
            if existing["ids"]:
                skipped += 1
                if (i + 1) % 500 == 0:
                    print(f"  [{i + 1}/{total}] {indexed} indexed, {skipped} skipped so far…")
                continue

        client.index(report)
        indexed += 1

        if (i + 1) % 500 == 0:
            print(f"  [{i + 1}/{total}] {indexed} indexed, {skipped} skipped so far…")

    print(f"\nDone. {indexed} indexed, {skipped} already existed (skipped).")


if __name__ == "__main__":
    main()
