from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .models import IngestionQuery
from .pipeline import get_source, run_pipeline
from .runtime_paths import ensure_parent_dir
from .skill_aggregate import aggregate_skills
from .skill_extract import extract_skill_counts
from .storage_sqlite import SQLiteStore


@dataclass(frozen=True)
class ExtractionSummary:
    postings_processed: int
    postings_with_skills: int
    skills_inserted: int
    skills_updated_or_skipped: int
    sample_out: str | None = None


def setup_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("skillpulse_ingest")
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    ensure_parent_dir(log_path)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


def ingest_postings(
    q: IngestionQuery,
    db_path: str,
    log_path: str,
    *,
    source_name: str | None = None,
) -> None:
    ensure_parent_dir(db_path)
    logger = setup_logger(log_path)
    store = SQLiteStore(db_path)
    try:
        adapters = [get_source(source_name)]
        run_pipeline(q, adapters, store, logger)
    finally:
        store.close()


def extract_posting_skills(
    db_path: str,
    q: IngestionQuery,
    *,
    limit: int | None = None,
    sample_out: str | None = None,
) -> ExtractionSummary:
    store = SQLiteStore(db_path)
    try:
        rows = store.iter_postings(q, limit=limit)

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
    finally:
        store.close()

    if sample_out:
        sample_path = ensure_parent_dir(sample_out)
        sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    return ExtractionSummary(
        postings_processed=postings_processed,
        postings_with_skills=nonempty_postings,
        skills_inserted=skills_inserted,
        skills_updated_or_skipped=skills_updated,
        sample_out=sample_out,
    )


def title_for_query(q: IngestionQuery) -> str:
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


def build_skill_insights(db_path: str, q: IngestionQuery, *, top_n: int) -> dict[str, Any]:
    store = SQLiteStore(db_path)
    try:
        postings_count = store.get_postings_count(q)
        companies_count = store.get_unique_companies_count(q)
    finally:
        store.close()

    skills = aggregate_skills(db_path, q, top_n=top_n)

    return {
        "title": title_for_query(q),
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
