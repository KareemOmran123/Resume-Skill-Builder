# RESUME-SKILL-BUILDER

This project analyzes junior software engineering job postings from curated company career boards and surfaces the top hard skills needed in a selected location.

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
2. Configure in-house career sources:
- Copy `backend\data\career_sources.example.json` to `backend\data\career_sources.json`
- Add only public company career pages or public ATS job-board endpoints you are allowed to fetch.
- Enable entries by setting `"enabled": true`.
3. Optional: set API key for TheirStack ingestion only if you explicitly use `--source theirstack`:
- PowerShell: `$env:THEIRSTACK_API_KEY="..."`
4. Backend artifacts now default to:
- `backend\data\skillpulse.db`
- `backend\logs\ingest.log`
- `backend\logs\skills_sample.json` (when requested, or via the combined runner)

## In-House Career Source

The default ingestion source is `careers`, a curated in-house collector. It avoids broad job-board scraping and instead reads from configured public career sources. The current local source list contains more than 100 configured company career boards.

- `greenhouse`: public Greenhouse board API using `board_token`
- `lever`: public Lever postings API using `company_slug`
- `ashby`: public Ashby job board API using `org_slug`
- `generic_html`: a conservative fallback for public careers pages, with `robots.txt` checks enabled by default

Career-board fetches run concurrently. Tune the number of parallel source fetches with:

- PowerShell: `$env:CAREER_FETCH_WORKERS="16"`

Example source config:

```json
[
  {
    "company": "Acme",
    "type": "lever",
    "company_slug": "acme",
    "enabled": true
  }
]
```

The local `backend\data\career_sources.json` file is ignored by git so you can curate sources for your own use.

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
- `python backend\scripts\ingest.py --source careers --location "San Francisco Bay Area" --role any --level entry --days 30`
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
- Backend internals/workflow: `backend/docs/BACKEND_WORKFLOW.md`
- Backend/frontend JSON contract: `backend/docs/JSON_CONTRACT.md`
- Schemas: `backend/docs/schemas/`
- Example payloads: `backend/docs/examples/`
