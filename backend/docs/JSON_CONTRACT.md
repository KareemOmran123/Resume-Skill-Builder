# JSON Contract (Backend -> Frontend)

This document defines the payload shapes the frontend can rely on.

## Version

- `schema_version`: `1.0.0`
- JSON Schema draft: `2020-12`

## Schema Files

- `backend/docs/schemas/ingest_query.schema.json`
- `backend/docs/schemas/job_posting.schema.json`
- `backend/docs/schemas/skill_insights_response.schema.json`

## Intended Usage

- `IngestionQuery`: request/filter contract for ingest/analysis runs.
- `JobPosting`: normalized internal posting shape from adapters.
- `SkillInsightsResponse`: frontend-facing response for the results page.

## Frontend Mapping Notes

Current `src/pages/Results.jsx` expects:

- `title`
- `subtitle`
- `skills[]` with each item containing:
- `name`
- `pct`

`SkillInsightsResponse` includes those fields and adds:

- `filters`
- `window`
- `totals`
- `generated_at`
- `schema_version`

This allows the frontend to keep current UI behavior while having stable metadata for future features.

## Example Payload

- `backend/docs/examples/skill_insights_response.example.json`

## Compatibility Rules

1. Additive fields are allowed in minor version updates.
2. Renaming/removing required fields requires a major version bump.
3. Frontend should fail closed if `schema_version` major changes.

