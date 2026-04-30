# JSON Contract (Backend -> Frontend)

This document defines payload shapes the frontend can rely on.

## Versioning

- `schema_version`: `1.0.0`
- JSON Schema draft: `2020-12`

## Schema Files

- `backend/docs/schemas/ingest_query.schema.json`
- `backend/docs/schemas/job_posting.schema.json`
- `backend/docs/schemas/skill_insights_response.schema.json`

## Which Stage Uses Which Schema

- Ingestion/filter input: `IngestionQuery`
- Normalized persistence object: `JobPosting`
- Frontend-ready insights output: `SkillInsightsResponse`

## API Endpoints

### `GET /api/skills`

Returns the frontend-ready skill insight payload for the selected filters.

Query params:

- `location`: location string, defaults to `United States`
- `role`: role bucket, defaults to `any`
- `level`: level bucket, defaults to `entry`
- `days`: rolling ingestion window, defaults to `30`
- `top`: number of ranked skills to return, defaults to `5`

### `GET /api/locations`

Returns location options discovered from postings stored in SQLite.

Query params:

- `days`: rolling ingestion window, defaults to `30`
- `limit`: max number of locations to return, defaults to `100`

Response shape:

```json
{
  "locations": ["United States", "San Francisco, CA", "Seattle, WA"],
  "window": { "days": 30 },
  "generated_at": "2026-04-30T00:00:00Z"
}
```

Notes:

- `United States` is always the first option.
- Other values come from actual ingested posting locations.
- The frontend Scope dropdown should use this response instead of a static location list.

## `SkillInsightsResponse` Field Notes

Required fields (per schema):

- `title`
- `subtitle`
- `window.days`
- `filters`
- `totals.postings_count`
- `totals.unique_companies_count`
- `skills[]` with `name`, `count`, `pct`

Optional but emitted by current script:

- `generated_at`
- `schema_version`

## Producer Script

- `backend/scripts/skill_insights.py` produces this payload.
- It reads pre-extracted data from `posting_skills` and posting totals from `postings`.
- `GET /api/skills` produces the same frontend contract at runtime.
- `GET /api/locations` reads posting locations from `postings`.

## Frontend Mapping

Current `src/pages/Results.jsx` requires:

- `title`
- `subtitle`
- `skills[].name`
- `skills[].pct`

The response also includes totals and filters for future UX extensions without contract changes.

Current `src/pages/SelectFocus.jsx` requires:

- `/api/locations.locations[]`

If `/api/locations` is unavailable or empty, the frontend falls back to `United States`.

## Example Payload

- `backend/docs/examples/skill_insights_response.example.json`

## Compatibility Rules

1. Additive fields are allowed in minor versions.
2. Removing/renaming required fields requires a major version bump.
3. Frontend should reject unsupported major `schema_version` values.
