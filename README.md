# RESUME-SKILL-BUILDER

This project analyzes job postings and surfaces the top hard skills needed for a selected role and location.

## Prerequisites

- Node.js (frontend)
- Python 3.10+ (backend)

## Frontend Setup

1. Install dependencies:
- `npm install`
2. Start dev server:
- `npm run dev`

## Backend Setup

1. Install backend package:
- `python -m pip install -e backend`
2. Set API key for Theirstack ingestion:
- PowerShell: `$env:THEIRSTACK_API_KEY="..."`
3. Backend artifacts now default to:
- `backend\data\skillpulse.db`
- `backend\logs\ingest.log`
- `backend\logs\skills_sample.json` (when requested, or via the combined runner)

## Recommended Backend Run

1. Run the full backend pipeline in one command:
- `python backend\scripts\run_backend.py --location "Dallas, TX" --role backend --level entry --days 30`
- This ingests postings, extracts skills, writes the SQLite DB/log artifacts under `backend\`, and prints the final insights JSON to stdout.

## Optional Manual Backend Run Order

1. Ingest postings:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30`
2. Extract and normalize skills:
- `python backend\scripts\extract_skills.py --location "Dallas, TX" --role backend --level entry --days 30 --sample-out backend\logs\skills_sample.json`
3. Generate insights JSON:
- `python backend\scripts\skill_insights.py --location "Dallas, TX" --role backend --level entry --days 30 --top 5`

## Tests

- Run backend tests:
- `python -m unittest discover -s backend\tests`

## Documentation Index

- End-to-end workflow: `docs/PROJECT_WORKFLOW.md`
- CI/CD and GitHub Actions: `docs/CI_CD.md`
- Backend internals/workflow: `backend/docs/BACKEND_WORKFLOW.md`
- Backend/frontend JSON contract: `backend/docs/JSON_CONTRACT.md`
- Schemas: `backend/docs/schemas/`
- Example payloads: `backend/docs/examples/`
