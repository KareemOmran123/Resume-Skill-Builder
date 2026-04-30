from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Type, Iterable

from .models import IngestionQuery, JobPosting
from .role_match import classify_level, classify_role, is_software_job_title, matches_query
from .sources.base import SourceAdapter
from .sources.jobspy import JobSpyAdapter

DEFAULT_SOURCE = "jobspy"

SOURCES: dict[str, Type[SourceAdapter]] = {
    "jobspy": JobSpyAdapter,
}


def get_source(name: Optional[str] = None) -> SourceAdapter:
    source_name = name or DEFAULT_SOURCE
    try:
        adapter_cls = SOURCES[source_name]
    except KeyError as exc:
        raise ValueError(f"Unknown source '{source_name}'. Options: {', '.join(SOURCES)}") from exc
    return adapter_cls()


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Some APIs return richer objects for text-like fields (e.g., company).
        name = value.get("name")
        if isinstance(name, str):
            return name
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _first_text(raw: dict, *keys: str) -> str:
    for key in keys:
        value = raw.get(key)
        text = _coerce_text(value)
        if text:
            return text
    return ""


def _normalize_jobspy(raw: dict) -> JobPosting:
    site = _first_text(raw, "site") or "jobspy"
    url = _first_text(raw, "job_url", "url")
    title = _coerce_text(raw.get("title"))
    company = _first_text(raw, "company", "company_name")
    location = _first_text(raw, "location")
    if not location:
        city = _first_text(raw, "city")
        state = _first_text(raw, "state")
        country = _first_text(raw, "country")
        location = ", ".join(part for part in (city, state, country) if part)
    date_posted = _first_text(raw, "date_posted") or None
    description = _coerce_text(raw.get("description"))

    role_bucket = classify_role(title, description)
    level_bucket = classify_level(title, description)

    fallback_url = f"jobspy://{site}/{_first_text(raw, 'id', 'job_id') or title}"

    return JobPosting(
        id=JobPosting.make_id("jobspy", url or fallback_url),
        source="jobspy",
        url=url or fallback_url,
        title=title,
        company=company,
        location=location or None,
        date_posted=date_posted,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        role_bucket=role_bucket,
        level_bucket=level_bucket,
        description_raw=description,
        raw=raw,
    )


def _normalize(source: SourceAdapter, raw: dict) -> JobPosting:
    if source.name == "jobspy":
        return _normalize_jobspy(raw)
    raise ValueError(f"No normalizer for source '{source.name}'")


def run_pipeline(
    q: IngestionQuery,
    adapters: Iterable[SourceAdapter],
    store,
    logger,
) -> None:
    total_inserted = 0
    total_skipped = 0

    for adapter in adapters:
        logger.info("Fetching from source=%s", adapter.name)
        try:
            raw_jobs = adapter.fetch(q)
        except Exception as exc:
            logger.error("Fetch failed for source=%s: %s", adapter.name, exc)
            continue
        logger.info("Fetched %d raw jobs from source=%s", len(raw_jobs), adapter.name)

        postings: list[JobPosting] = []
        for raw in raw_jobs:
            try:
                p = _normalize(adapter, raw)
            except Exception as exc:
                logger.warning("Skipping job from source=%s due to normalize error: %s", adapter.name, exc)
                continue

            if not matches_query(p.role_bucket, p.level_bucket, q.role_bucket, q.level_bucket):
                continue
            if adapter.name == "jobspy" and not is_software_job_title(p.title):
                continue
            postings.append(p)

        inserted, skipped = store.upsert_many(postings)
        total_inserted += inserted
        total_skipped += skipped
        logger.info(
            "Upserted source=%s inserted=%d skipped=%d (after filtering %d)",
            adapter.name,
            inserted,
            skipped,
            len(postings),
        )

    logger.info("Pipeline complete inserted=%d skipped=%d", total_inserted, total_skipped)
