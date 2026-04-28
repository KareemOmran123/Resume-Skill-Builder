from __future__ import annotations

import argparse

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.pipeline import SOURCES
from skillpulse_ingest.runtime_paths import DEFAULT_DB_PATH, DEFAULT_LOG_PATH
from skillpulse_ingest.workflow import ingest_postings, setup_logger


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max-results", type=int, default=250)
    ap.add_argument("--source", choices=sorted(SOURCES.keys()), default=None)
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH))
    ap.add_argument("--log", default=str(DEFAULT_LOG_PATH))
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=args.max_results,
    )

    ingest_postings(q, args.db, args.log, source_name=args.source)

if __name__ == "__main__":
    main()
