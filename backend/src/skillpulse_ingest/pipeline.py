from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Type, Iterable

from .models import IngestionQuery, JobPosting
from .role_match import classify_level, classify_role, matches_query
from .sources.remotive import RemotiveAdapter
from .sources.theirstack import TheirstackAdapter
from .sources.base import SourceAdapter

DEFAULT_SOURCE = "theirstack"

SOURCES: dict[str, Type[SourceAdapter]] = {
    "theirstack": TheirstackAdapter,
    "remotive": RemotiveAdapter,
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


def _normalize_remotive(raw: dict) -> JobPosting:
    url = _coerce_text(raw.get("url"))
    title = _coerce_text(raw.get("title"))
    company = _coerce_text(raw.get("company_name"))
    location = _coerce_text(raw.get("candidate_required_location")) or None
    date_posted = _coerce_text(raw.get("publication_date")) or None
    description = _coerce_text(raw.get("description"))

    role_bucket = classify_role(title, description)
    level_bucket = classify_level(title, description)

    return JobPosting(
        id=JobPosting.make_id("remotive", url or f"remotive://{raw.get('id', '')}"),
        source="remotive",
        url=url or f"remotive://{raw.get('id', '')}",
        title=title,
        company=company,
        location=location,
        date_posted=date_posted,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        role_bucket=role_bucket,
        level_bucket=level_bucket,
        description_raw=description,
        raw=raw,
    )


def _normalize_theirstack(raw: dict) -> JobPosting:
    url = _coerce_text(raw.get("final_url")) or _coerce_text(raw.get("url")) or _coerce_text(raw.get("source_url"))
    title = _coerce_text(raw.get("job_title"))
    company = _coerce_text(raw.get("company"))
    location = (
        _coerce_text(raw.get("location"))
        or _coerce_text(raw.get("short_location"))
        or _coerce_text(raw.get("long_location"))
        or None
    )
    date_posted = _coerce_text(raw.get("date_posted")) or None
    description = _coerce_text(raw.get("description"))

    role_bucket = classify_role(title, description)
    level_bucket = classify_level(title, description)

    fallback_url = f"theirstack://{raw.get('id', '')}"

    return JobPosting(
        id=JobPosting.make_id("theirstack", url or fallback_url),
        source="theirstack",
        url=url or fallback_url,
        title=title,
        company=company,
        location=location,
        date_posted=date_posted,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        role_bucket=role_bucket,
        level_bucket=level_bucket,
        description_raw=description,
        raw=raw,
    )


def _normalize(source: SourceAdapter, raw: dict) -> JobPosting:
    if source.name == "remotive":
        return _normalize_remotive(raw)
    if source.name == "theirstack":
        return _normalize_theirstack(raw)
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
