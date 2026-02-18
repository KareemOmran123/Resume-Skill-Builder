# Backend Workflow

This document explains backend modules, runtime flow, and operation commands.

## Backend Modules

- `backend/src/skillpulse_ingest/models.py`
- `IngestionQuery`: query/filter input for all backend stages.
- `JobPosting`: normalized posting shape persisted into SQLite.

- `backend/src/skillpulse_ingest/pipeline.py`
- Source selection, normalization, role/level filtering, and persistence.

- `backend/src/skillpulse_ingest/storage_sqlite.py`
- SQLite schema and store helpers for `postings` and `posting_skills`.

- `backend/src/skillpulse_ingest/skills_catalog.py`
- Canonical skill groups and regex aliases.

- `backend/src/skillpulse_ingest/skill_extract.py`
- Text cleaning and hard-skill extraction.

- `backend/src/skillpulse_ingest/skill_aggregate.py`
- Skill prevalence aggregation and ranking.

- `backend/src/skillpulse_ingest/sources/`
- Adapter implementations for data providers.

## Database Model

### Table: `postings`

- Normalized postings from ingestion.
- Primary key: `id` (`sha256(source:url)` truncated).

### Table: `posting_skills`

- Per-posting extracted skill counts.
- Composite PK: `(posting_id, skill)`.
- Indexed on `skill` and `posting_id`.

## Runtime Pipelines

### 1) Ingestion Pipeline

1. `backend/scripts/ingest.py` parses CLI args.
2. Build `IngestionQuery`.
3. Fetch via selected source adapter.
4. Normalize + classify + filter.
5. Upsert into `postings`.

### 2) Skill Extraction Pipeline (Sprint 2)

1. `backend/scripts/extract_skills.py` loads filtered postings.
2. Clean posting text (`clean_text`).
3. Extract canonical hard-skill counts (`extract_skill_counts`).
4. Upsert into `posting_skills`.
5. Optionally save sample output for manual QA.

### 3) Insights Aggregation Pipeline (Sprint 3)

1. `backend/scripts/skill_insights.py` builds the same `IngestionQuery` filter.
2. Reads posting totals (`postings_count`, `unique_companies_count`).
3. Aggregates skill prevalence with distinct posting counts.
4. Computes percentages and stable ordering.
5. Emits JSON matching `SkillInsightsResponse` schema.

## Filtering Rules

- Shared filter object: `IngestionQuery`.
- Role and level filters applied when not `any`.
- Excludes `senior_excluded` records.
- Time window uses `retrieved_at >= now - days`.
- Location filter uses case-insensitive `LIKE` match.

## Reliability Behavior

- Source adapters retry on transient failures:
- connection errors
- timeouts
- HTTP `429/500/502/503/504`
- Backoff: exponential, base `1.0s`, max retries `3`.

## JSON Contract

- Contract doc: `backend/docs/JSON_CONTRACT.md`
- Schema: `backend/docs/schemas/skill_insights_response.schema.json`
- Example: `backend/docs/examples/skill_insights_response.example.json`

## Operations

1. Install backend package:
- `python -m pip install -e backend`
2. Run ingest:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30`
3. Run extraction:
- `python backend\scripts\extract_skills.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --sample-out backend\logs\skills_sample.json`
4. Generate insights:
- `python backend\scripts\skill_insights.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --top 5`
5. Inspect raw DB:
- `python backend\scripts\inspect_db.py --db backend\data\skillpulse.db --limit 10`

## Tests

- Run all backend tests:
- `python -m unittest discover -s backend\tests`
- Live provider integration test (optional):
- `python -m unittest backend.tests.test_integration_theirstack_live`
