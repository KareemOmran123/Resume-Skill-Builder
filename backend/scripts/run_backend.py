from __future__ import annotations

import argparse
import json
import sys

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.pipeline import SOURCES
from skillpulse_ingest.runtime_paths import (
    DEFAULT_DB_PATH,
    DEFAULT_LOG_PATH,
    DEFAULT_SAMPLE_PATH,
    ensure_parent_dir,
)
from skillpulse_ingest.workflow import build_skill_insights, extract_posting_skills, ingest_postings


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run ingest, extraction, and insights in one command.")
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max-results", type=int, default=250)
    ap.add_argument("--source", choices=sorted(SOURCES.keys()), default=None)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH))
    ap.add_argument("--log", default=str(DEFAULT_LOG_PATH))
    ap.add_argument("--sample-out", default=str(DEFAULT_SAMPLE_PATH))
    ap.add_argument("--out", default=None)
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
    summary = extract_posting_skills(args.db, q, sample_out=args.sample_out)
    payload = build_skill_insights(args.db, q, top_n=args.top)

    print(f"postings_processed={summary.postings_processed}", file=sys.stderr)
    print(f"postings_with_skills={summary.postings_with_skills}", file=sys.stderr)
    print(f"skills_inserted={summary.skills_inserted}", file=sys.stderr)
    print(f"skills_updated_or_skipped={summary.skills_updated_or_skipped}", file=sys.stderr)
    if summary.sample_out:
        print(f"sample_written={summary.sample_out}", file=sys.stderr)

    if args.out:
        out_path = ensure_parent_dir(args.out)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"insights_written={out_path}", file=sys.stderr)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
