from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import IngestionQuery
from .runtime_paths import DEFAULT_DB_PATH
from .skill_aggregate import aggregate_skills
from .storage_sqlite import SQLiteStore

app = FastAPI(title="SkillPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/locations")
def locations(days: int = 30, limit: int = 100) -> dict[str, Any]:
    store = SQLiteStore(str(DEFAULT_DB_PATH))
    try:
        available = store.list_available_locations(days=days, limit=limit)
    finally:
        store.close()
    return {
        "locations": available,
        "window": {"days": days},
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def title_for_query(q: IngestionQuery) -> str:
    level = {
        "entry": "Junior",
        "junior_mid": "Junior/Mid",
        "any": "",
    }.get(q.level_bucket, "")
    role = {
        "backend": "Backend",
        "frontend": "Frontend",
        "fullstack": "Full Stack",
        "any": "",
    }.get(q.role_bucket, "")
    parts = [level, role, "Software Engineer"]
    return " ".join(p for p in parts if p).strip()


@app.get("/api/skills")
def skills(
    location: str = "United States",
    role: str = "any",
    level: str = "entry",
    days: int = 30,
    top: int = 5,
) -> dict[str, Any]:
    q = IngestionQuery(
        location=location,
        role_bucket=role,
        level_bucket=level,
        days=days,
        max_results=250,
    )

    db_path = str(DEFAULT_DB_PATH)
    store = SQLiteStore(db_path)
    try:
        postings_count = store.get_postings_count(q)
        companies_count = store.get_unique_companies_count(q)
    finally:
        store.close()

    return {
        "title": title_for_query(q),
        "subtitle": f"Based on {postings_count} job postings in {q.location} from the last {q.days} days",
        "window": {"days": q.days},
        "filters": {
            "location": q.location,
            "role_bucket": q.role_bucket,
            "level_bucket": q.level_bucket,
            "days": q.days,
            "max_results": q.max_results,
        },
        "totals": {
            "postings_count": postings_count,
            "unique_companies_count": companies_count,
        },
        "skills": aggregate_skills(db_path, q, top_n=top),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "schema_version": "1.0.0",
    }
