# Backend Workflow

This document explains backend modules, runtime flow, and operation commands.

## Backend Modules

- `backend/src/skillpulse_ingest/models.py`
- `IngestionQuery`: query/filter input for all backend stages.
- `JobPosting`: normalized posting shape persisted into SQLite.

- `backend/src/skillpulse_ingest/pipeline.py`
- Source selection, normalization, role/level filtering, and persistence.

- `backend/src/skillpulse_ingest/storage_sqlite.py`
- SQLite schema and store helpers for `postings`, `posting_skills`, aggregate counts, and available posting locations.

- `backend/src/skillpulse_ingest/skills_catalog.py`
- Canonical skill groups and regex aliases.

- `backend/src/skillpulse_ingest/skill_extract.py`
- Text cleaning and hard-skill extraction.

- `backend/src/skillpulse_ingest/skill_aggregate.py`
- Skill prevalence aggregation and ranking.

- `backend/src/skillpulse_ingest/sources/`
- Adapter implementations for data providers.

- `backend/src/skillpulse_ingest/api.py`
- FastAPI routes for health checks, dynamic locations, and frontend skill insights.

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

Default source: `jobspy`.

The `jobspy` adapter calls `python-jobspy` and normalizes its dataframe output into the backend `JobPosting` shape. By default it searches Indeed, LinkedIn, ZipRecruiter, and Google. Override that list with `JOBSPY_SITES`, for example `indeed,linkedin`.

### 2) Skill Extraction Pipeline (Sprint 2)

1. `backend/scripts/extract_skills.py` loads filtered postings.
2. Clean posting text (`clean_text`).
3. Extract canonical hard-skill counts (`extract_skill_counts`).
4. Upsert into `posting_skills` with a single batched commit for the extraction run.
5. Optionally save sample output for manual QA.

### 3) Insights Aggregation Pipeline (Sprint 3)

1. `backend/scripts/skill_insights.py` builds the same `IngestionQuery` filter.
2. Reads posting totals (`postings_count`, `unique_companies_count`).
3. Aggregates skill prevalence with distinct posting counts.
4. Computes percentages and stable ordering.
5. Emits JSON matching `SkillInsightsResponse` schema.

### 4) Combined Runner

1. `backend/scripts/run_backend.py` runs ingestion, extraction, and insights generation in order.
2. Shared defaults keep all backend artifacts under `backend/data` and `backend/logs`.
3. Final insights JSON is printed to stdout, and extraction samples are written to `backend/logs/skills_sample.json` by default.

### 5) API Runtime

1. `GET /api/health` returns service status.
2. `GET /api/locations` returns `United States` plus distinct locations found in recent stored postings.
3. `GET /api/skills` returns the frontend-ready skill insights payload for the selected filters.

The frontend Scope dropdown calls `/api/locations`, so location options are generated from ingested posting data rather than a hardcoded list.

## Filtering Rules

- Shared filter object: `IngestionQuery`.
- Role and level filters applied when not `any`.
- Excludes `senior_excluded` records.
- Time window uses `retrieved_at >= now - days`.
- `United States` does not narrow by city/location.
- Specific locations use expanded aliases and case-insensitive `LIKE` matching.
- Available dropdown locations are split from raw posting locations and ordered by posting frequency.

## Reliability Behavior

- Job board reliability and rate limiting are handled by JobSpy. If a board blocks or rate limits a scrape, reduce `JOBSPY_SITES`, lower `--max-results`, or retry later.

## JSON Contract

- Contract doc: `backend/docs/JSON_CONTRACT.md`
- Schema: `backend/docs/schemas/skill_insights_response.schema.json`
- Example: `backend/docs/examples/skill_insights_response.example.json`
- API payloads:
- `GET /api/locations`
- `GET /api/skills`

## Operations

1. Install backend package:
- `python -m pip install -e backend`
2. Recommended one-command run:
- `python backend\scripts\run_backend.py --location "San Francisco Bay Area" --role any --level entry --days 30`
3. Optional step-by-step ingest:
- `python backend\scripts\ingest.py --source jobspy --location "San Francisco Bay Area" --role any --level entry --days 30`
4. Optional step-by-step extraction:
- `python backend\scripts\extract_skills.py --location "San Francisco Bay Area" --role any --level entry --days 30 --sample-out backend\logs\skills_sample.json`
5. Optional step-by-step insights:
- `python backend\scripts\skill_insights.py --location "San Francisco Bay Area" --role any --level entry --days 30 --top 5`
6. Inspect raw DB:
- `python backend\scripts\inspect_db.py --limit 10`
7. Start API for frontend:
- `python -m uvicorn skillpulse_ingest.api:app --host 127.0.0.1 --port 8000`

## Tests

- Run all backend tests:
- `python -m unittest discover -s backend\tests`
