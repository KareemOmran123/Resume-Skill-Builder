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

## Frontend Mapping

Current `src/pages/Results.jsx` requires:

- `title`
- `subtitle`
- `skills[].name`
- `skills[].pct`

The response also includes totals and filters for future UX extensions without contract changes.

## Example Payload

- `backend/docs/examples/skill_insights_response.example.json`

## Compatibility Rules

1. Additive fields are allowed in minor versions.
2. Removing/renaming required fields requires a major version bump.
3. Frontend should reject unsupported major `schema_version` values.
