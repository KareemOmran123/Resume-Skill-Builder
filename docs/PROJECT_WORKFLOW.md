# Project Workflow

This document explains how the project currently works end to end.

## Current State

- Frontend is a React/Vite app.
- Backend is a Python ingestion pipeline that fetches and stores normalized job postings.
- Frontend is currently using local mock data in `src/data/skills.js`.
- Backend output is persisted in SQLite and documented via JSON schemas in `backend/docs/schemas/`.
- There is no live API wiring from frontend to backend yet.

## Repository Overview

- `src/`: frontend UI.
- `backend/src/skillpulse_ingest/`: ingestion domain logic.
- `backend/scripts/`: operational scripts for ingest and DB inspection.
- `backend/tests/`: unit and integration tests.
- `backend/docs/`: backend contracts and workflows.
- `docs/`: project-level docs.

## Frontend Workflow (Current)

1. User lands on `src/pages/Landing.jsx`.
2. User selects focus filters in `src/pages/SelectFocus.jsx`.
3. Results page `src/pages/Results.jsx` renders a dataset from `src/data/skills.js`.
4. No backend request is made yet.

## Backend Workflow (Current)

1. Run ingest script: `backend/scripts/ingest.py`.
2. Script builds an `IngestionQuery` from CLI args.
3. Script selects a source adapter (`theirstack` default, `remotive` optional).
4. Adapter fetches raw jobs from provider API with retry/backoff.
5. Pipeline normalizes raw rows into `JobPosting`.
6. Pipeline classifies role/level and applies query matching filters.
7. SQLite store inserts new rows and skips duplicates by `id`.
8. Data is written to `postings` table in SQLite.

## Data Contracts

- JSON contract entrypoint: `backend/docs/JSON_CONTRACT.md`.
- Schemas:
- `backend/docs/schemas/ingest_query.schema.json`
- `backend/docs/schemas/job_posting.schema.json`
- `backend/docs/schemas/skill_insights_response.schema.json`
- Example:
- `backend/docs/examples/skill_insights_response.example.json`

## Testing Workflow

1. Install backend package for local imports:
- `python -m pip install -e backend`
2. Run backend tests:
- `python -m unittest discover -s backend\tests`
3. Optional live TheirStack integration test (requires key):
- `python -m unittest backend.tests.test_integration_theirstack_live`

## Operational Workflow

1. Set API key:
- `THEIRSTACK_API_KEY`
2. Run ingest:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30`
3. Inspect DB:
- `python backend\scripts\inspect_db.py --db backend\data\skillpulse.db --limit 10`

## What Is Not Implemented Yet

- Backend endpoint that emits `SkillInsightsResponse` directly for frontend.
- Frontend fetch logic against backend contract.
- Scheduled/automated ingest orchestration.

