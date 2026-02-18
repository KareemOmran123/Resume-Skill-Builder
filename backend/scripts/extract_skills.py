from __future__ import annotations

import argparse
import json
from pathlib import Path

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.skill_extract import extract_skill_counts
from skillpulse_ingest.storage_sqlite import SQLiteStore


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(Path("data") / "skillpulse.db"))
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sample-out", default=None)
    args = ap.parse_args()

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=10_000,
    )

    store = SQLiteStore(args.db)
    rows = store.iter_postings(q, limit=args.limit)

    postings_processed = 0
    skills_inserted = 0
    skills_updated = 0
    nonempty_postings = 0
    sample: list[dict[str, object]] = []

    for row in rows:
        postings_processed += 1
        skill_counts = extract_skill_counts(row["title"], row["description_raw"])
        inserted, updated = store.upsert_posting_skills(row["id"], skill_counts)
        skills_inserted += inserted
        skills_updated += updated

        if skill_counts:
            nonempty_postings += 1

        # Keep sample small and deterministic for quick manual QA checks.
        if len(sample) < 20:
            sample.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "company": row["company"],
                    "extracted_skills": [
                        {"name": k, "count": v}
                        for k, v in sorted(skill_counts.items(), key=lambda kv: (-kv[1], kv[0]))
                    ],
                }
            )

    if args.sample_out:
        sample_path = Path(args.sample_out)
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"postings_processed={postings_processed}")
    print(f"postings_with_skills={nonempty_postings}")
    print(f"skills_inserted={skills_inserted}")
    print(f"skills_updated_or_skipped={skills_updated}")
    if args.sample_out:
        print(f"sample_written={args.sample_out}")

    store.close()


if __name__ == "__main__":
    main()