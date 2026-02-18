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

## Backend Run Order

1. Ingest postings:
- `python backend\scripts\ingest.py --location "Dallas, TX" --role backend --level entry --days 30`
2. Extract and normalize skills:
- `python backend\scripts\extract_skills.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --sample-out backend\logs\skills_sample.json`
3. Generate insights JSON:
- `python backend\scripts\skill_insights.py --db backend\data\skillpulse.db --location "Dallas, TX" --role backend --level entry --days 30 --top 5`

## Tests

- Run backend tests:
- `python -m unittest discover -s backend\tests`

## Documentation Index

- End-to-end workflow: `docs/PROJECT_WORKFLOW.md`
- Backend internals/workflow: `backend/docs/BACKEND_WORKFLOW.md`
- Backend/frontend JSON contract: `backend/docs/JSON_CONTRACT.md`
- Schemas: `backend/docs/schemas/`
- Example payloads: `backend/docs/examples/`
