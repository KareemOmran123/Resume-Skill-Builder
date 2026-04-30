# RESUME-SKILL-BUILDER

This project analyzes junior software engineering job postings collected through JobSpy and surfaces the top hard skills needed in a selected location.

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
2. Backend artifacts default to:
- `backend\data\skillpulse.db`
- `backend\logs\ingest.log`
- `backend\logs\skills_sample.json` (when requested, or via the combined runner)

## JobSpy Source

The default ingestion source is `jobspy`, using the `python-jobspy` package.

Default boards:

- `indeed`
- `linkedin`
- `zip_recruiter`
- `google`

Override the boards with a comma-separated environment variable:

- PowerShell: `$env:JOBSPY_SITES="indeed,linkedin,zip_recruiter,google"`

Optional JobSpy settings can also be supplied through environment variables:

- `JOBSPY_SEARCH_TERM`
- `JOBSPY_GOOGLE_SEARCH_TERM`
- `JOBSPY_DISTANCE`
- `JOBSPY_JOB_TYPE`
- `JOBSPY_REMOTE`
- `JOBSPY_EASY_APPLY`
- `JOBSPY_PROXIES`
- `JOBSPY_LINKEDIN_FETCH_DESCRIPTION`
- `JOBSPY_DESCRIPTION_FORMAT`
- `JOBSPY_VERBOSE`

## Dynamic Locations

The app no longer uses a static list of city options. After ingestion, the backend exposes locations found in stored postings through:

- `GET http://127.0.0.1:8000/api/locations`

The frontend Scope dropdown loads that endpoint and shows locations such as San Francisco, Dallas, Boston, Seattle, Austin, Denver, or any other locations found in the latest postings. `United States` is always kept as the default broad scope.

## Recommended Backend Run

1. Run the full backend pipeline in one command:
- `python backend\scripts\run_backend.py --location "San Francisco Bay Area" --role any --level entry --days 30`
- This ingests postings, extracts skills, writes the SQLite DB/log artifacts under `backend\`, and prints the final insights JSON to stdout.

## Optional Manual Backend Run Order

1. Ingest postings:
- `python backend\scripts\ingest.py --source jobspy --location "San Francisco Bay Area" --role any --level entry --days 30 --out backend\logs\jobs.json`
2. Extract and normalize skills:
- `python backend\scripts\extract_skills.py --location "San Francisco Bay Area" --role any --level entry --days 30 --sample-out backend\logs\skills_sample.json`
3. Generate insights JSON:
- `python backend\scripts\skill_insights.py --location "San Francisco Bay Area" --role any --level entry --days 30 --top 5`

## Tests

- Run backend tests:
- `python -m unittest discover -s backend\tests`
- Run frontend build:
- `npm run build`

## Documentation Index

- End-to-end workflow: `docs/PROJECT_WORKFLOW.md`
- CI/CD and GitHub Actions: `docs/CI_CD.md`
- Backend internals/workflow: `backend/docs/BACKEND_WORKFLOW.md`
- Backend/frontend JSON contract: `backend/docs/JSON_CONTRACT.md`
- Schemas: `backend/docs/schemas/`
- Example payloads: `backend/docs/examples/`
