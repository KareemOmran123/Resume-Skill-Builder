from __future__ import annotations

import argparse
import json

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.runtime_paths import DEFAULT_DB_PATH
from skillpulse_ingest.workflow import build_skill_insights


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH))
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=5)
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=250,
    )

    payload = build_skill_insights(args.db, q, top_n=args.top)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
