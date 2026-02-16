# Backend Workflow

This document explains backend architecture, runtime flow, and operations.

## Modules

- `backend/src/skillpulse_ingest/models.py`
- `IngestionQuery`: ingest/filter input object.
- `JobPosting`: normalized posting object used before persistence.

- `backend/src/skillpulse_ingest/sources/base.py`
- Source adapter interface.

- `backend/src/skillpulse_ingest/sources/theirstack.py`
- Theirstack fetcher.
- Requires `THEIRSTACK_API_KEY`.
- Uses retry/backoff for transient failures.

- `backend/src/skillpulse_ingest/sources/remotive.py`
- Remotive fetcher.
- Uses retry/backoff for transient failures.

- `backend/src/skillpulse_ingest/role_match.py`
- Heuristic role/level classification and query matching.

- `backend/src/skillpulse_ingest/pipeline.py`
- Source selection, normalization, filtering, and persistence orchestration.

- `backend/src/skillpulse_ingest/storage_sqlite.py`
- SQLite schema and upsert behavior.

- `backend/scripts/ingest.py`
- CLI entrypoint for running ingestion.

- `backend/scripts/inspect_db.py`
- CLI utility for checking DB contents quickly.

## Runtime Flow

1. `ingest.py` parses CLI args into `IngestionQuery`.
2. `get_source()` in `pipeline.py` resolves source adapter.
3. Adapter fetches API rows with retry/backoff.
4. `pipeline.py` normalizes source rows into `JobPosting`.
5. `classify_role()` and `classify_level()` compute buckets.
6. `matches_query()` keeps only rows matching requested role/level.
7. `SQLiteStore.upsert_many()` inserts rows and skips duplicates.
8. Script logs inserted/skipped totals.

## Reliability Behavior

- Both adapters retry on:
- connection errors
- timeouts
- HTTP `429`, `500`, `502`, `503`, `504`
- Retry policy:
- max retries: `3`
- exponential backoff base: `1.0s`

## Packaging and Imports

- Backend uses `src/` layout and `pyproject.toml`:
- `backend/pyproject.toml`
- Install once per environment:
- `python -m pip install -e backend`
- This removes the need for `sys.path` hacks in scripts/tests.

## Running Backend

1. Install editable package:
- `python -m pip install -e backend`
2. Set API key:
- PowerShell: `$env:THEIRSTACK_API_KEY="..."`
3. Ingest sample:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30 --max-results 250`
4. Inspect DB:
- `python backend\scripts\inspect_db.py --db backend\data\skillpulse.db --limit 10`

## Database Model

Table: `postings`

- Primary key: `id` (`sha256(source:url)` truncated).
- Core fields:
- `source`, `url`, `title`, `company`, `location`, `date_posted`
- Classification fields:
- `role_bucket`, `level_bucket`
- Audit fields:
- `retrieved_at`, `description_raw`, `raw_json`

## Test Coverage

- Unit tests for models, role matching, storage, adapters, pipeline, scripts.
- Live integration test for TheirStack:
- `backend/tests/test_integration_theirstack_live.py`
- The test is skipped unless `THEIRSTACK_API_KEY` is set.

## Contract for Frontend

- See `backend/docs/JSON_CONTRACT.md` for response schemas and compatibility rules.
- Main frontend response schema:
- `backend/docs/schemas/skill_insights_response.schema.json`

