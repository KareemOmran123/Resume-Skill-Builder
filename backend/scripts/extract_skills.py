from __future__ import annotations

import argparse

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.runtime_paths import DEFAULT_DB_PATH
from skillpulse_ingest.workflow import extract_posting_skills


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH))
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sample-out", default=None)
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=10_000,
    )

    summary = extract_posting_skills(args.db, q, limit=args.limit, sample_out=args.sample_out)

    print(f"postings_processed={summary.postings_processed}")
    print(f"postings_with_skills={summary.postings_with_skills}")
    print(f"skills_inserted={summary.skills_inserted}")
    print(f"skills_updated_or_skipped={summary.skills_updated_or_skipped}")
    if args.sample_out:
        print(f"sample_written={args.sample_out}")


if __name__ == "__main__":
    main()
