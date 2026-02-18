# Project Workflow

This document explains how the project currently works end to end.

## Architecture Snapshot

- Frontend: React + Vite (`src/`)
- Backend: Python ingestion + extraction + aggregation (`backend/src/skillpulse_ingest/`)
- Storage: SQLite (`postings`, `posting_skills`)
- Contract: JSON schema for frontend response (`backend/docs/schemas/skill_insights_response.schema.json`)

## Repository Layout

- `src/`: frontend pages/components and mock data.
- `backend/src/skillpulse_ingest/`: backend domain modules.
- `backend/scripts/`: operational CLIs.
- `backend/tests/`: backend tests.
- `backend/docs/`: backend documentation and schemas.
- `docs/`: project-level workflow docs.

## End-to-End Data Flow

1. Ingest raw postings from external provider APIs.
2. Normalize postings into canonical backend records.
3. Persist normalized records into `postings`.
4. Extract hard skills from each posting into `posting_skills`.
5. Aggregate skills by filtered posting set.
6. Emit a frontend-ready `SkillInsightsResponse` JSON payload.

## Sprint 1 (Ingestion)

1. Run `backend/scripts/ingest.py`.
2. Build `IngestionQuery` from CLI arguments.
3. Fetch raw rows via source adapter (`theirstack` default, `remotive` optional).
4. Normalize records and classify role/level.
5. Insert unique rows into `postings`.

## Sprint 2 (Skill Extraction + Normalization)

1. Run `backend/scripts/extract_skills.py`.
2. Load filtered postings via `SQLiteStore.iter_postings(...)`.
3. Clean title/description (`clean_text`) and extract hard skills (`extract_skill_counts`).
4. Normalize aliases to canonical skill names through the catalog.
5. Upsert per-posting skill counts into `posting_skills`.
6. Optionally output a sample extraction JSON for manual review.

## Sprint 3 (Aggregation + Insights Output)

1. Run `backend/scripts/skill_insights.py`.
2. Compute filtered totals:
- `postings_count`
- `unique_companies_count`
3. Aggregate skill prevalence using distinct postings containing each skill.
4. Calculate percentages with denominator = filtered posting count.
5. Sort stably (`pct desc`, `count desc`, `name asc`).
6. Emit schema-compatible `SkillInsightsResponse` JSON.

## Frontend Status

- Current UI still reads mock data from `src/data/skills.js`.
- Backend now produces the final payload shape that frontend can consume.

## Standard Runbook

1. Install backend package:
- `python -m pip install -e backend`
2. Ingest postings:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30`
3. Extract skills:
- `python backend\scripts\extract_skills.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --sample-out backend\logs\skills_sample.json`
4. Generate insights JSON:
- `python backend\scripts\skill_insights.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --top 5`
5. Run tests:
- `python -m unittest discover -s backend\tests`

## Known Gaps

- Frontend is not yet wired to backend API/CLI output.
- No scheduler/orchestrator yet for automated refresh.
