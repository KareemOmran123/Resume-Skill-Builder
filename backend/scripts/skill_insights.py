from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.skill_aggregate import aggregate_skills
from skillpulse_ingest.storage_sqlite import SQLiteStore


def _title_for_query(q: IngestionQuery) -> str:
    level = {
        "entry": "Junior",
        "junior_mid": "Junior/Mid",
        "any": "",
    }[q.level_bucket]
    role = {
        "backend": "Backend",
        "frontend": "Frontend",
        "fullstack": "Full Stack",
        "any": "",
    }[q.role_bucket]
    parts = [level, role, "Software Engineer"]
    return " ".join(p for p in parts if p).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(Path("data") / "skillpulse.db"))
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=250,
    )

    store = SQLiteStore(args.db)
    postings_count = store.get_postings_count(q)
    companies_count = store.get_unique_companies_count(q)
    store.close()

    skills = aggregate_skills(args.db, q, top_n=args.top)

    # This payload is intentionally aligned to skill_insights_response.schema.json.
    payload = {
        "title": _title_for_query(q),
        "subtitle": f"Based on {postings_count} job postings in {q.location} from the last {q.days} days",
        "window": {"days": q.days},
        "filters": {
            "location": q.location,
            "role_bucket": q.role_bucket,
            "level_bucket": q.level_bucket,
            "days": q.days,
            "max_results": q.max_results,
        },
        "totals": {
            "postings_count": postings_count,
            "unique_companies_count": companies_count,
        },
        "skills": skills,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "schema_version": "1.0.0",
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
