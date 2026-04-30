from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Iterable
import re

from .models import IngestionQuery, JobPosting

SCHEMA = """
CREATE TABLE IF NOT EXISTS postings (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT,
  date_posted TEXT,
  retrieved_at TEXT NOT NULL,
  role_bucket TEXT NOT NULL,
  level_bucket TEXT NOT NULL,
  description_raw TEXT NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_postings_role ON postings(role_bucket);
CREATE INDEX IF NOT EXISTS idx_postings_level ON postings(level_bucket);
CREATE INDEX IF NOT EXISTS idx_postings_date ON postings(date_posted);

CREATE TABLE IF NOT EXISTS posting_skills (
  posting_id TEXT NOT NULL,
  skill TEXT NOT NULL,
  count INTEGER NOT NULL,
  PRIMARY KEY (posting_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_posting_skills_skill ON posting_skills(skill);
CREATE INDEX IF NOT EXISTS idx_posting_skills_posting ON posting_skills(posting_id);
"""


def location_search_terms(location: str) -> list[str]:
    normalized = location.strip().lower()
    if normalized in {"united states", "us", "usa", "u.s.", "u.s.a.", "us-wide", "nationwide"}:
        return []
    aliases = {
        "dallas, tx": ["dallas", "dfw", "dallas-fort worth"],
        "dallas-fort worth": ["dallas", "dfw", "dallas-fort worth"],
        "san francisco bay area": [
            "san francisco",
            "bay area",
            "san jose",
            "oakland",
            "mountain view",
            "sunnyvale",
            "san mateo",
            "fremont",
            "palo alto",
            "redwood city",
            "menlo park",
            "mtvhq",
            "sfo",
        ],
        "new york, ny": ["new york", "new york city", "nyc"],
        "new york city": ["new york", "new york city", "nyc"],
        "seattle, wa": ["seattle"],
        "austin, tx": ["austin"],
    }.get(normalized)
    return aliases or ([normalized] if normalized else [])


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_many(self, postings: Iterable[JobPosting]) -> tuple[int, int]:
        inserted = 0
        skipped = 0
        cur = self.conn.cursor()
        for p in postings:
            try:
                cur.execute(
                    """
                    INSERT INTO postings (
                      id, source, url, title, company, location, date_posted, retrieved_at,
                      role_bucket, level_bucket, description_raw, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p.id,
                        p.source,
                        p.url,
                        p.title,
                        p.company,
                        p.location,
                        p.date_posted,
                        p.retrieved_at,
                        p.role_bucket,
                        p.level_bucket,
                        p.description_raw,
                        json.dumps(p.raw, ensure_ascii=False),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        self.conn.commit()
        return inserted, skipped

    def _posting_where_clause(self, q: IngestionQuery) -> tuple[str, list[object]]:
        # One shared filter clause keeps extraction and aggregation aligned.
        clauses: list[str] = ["level_bucket != ?"]
        params: list[object] = ["senior_excluded"]

        if q.role_bucket != "any":
            clauses.append("role_bucket = ?")
            params.append(q.role_bucket)

        if q.level_bucket != "any":
            clauses.append("level_bucket = ?")
            params.append(q.level_bucket)

        if q.location:
            terms = location_search_terms(q.location)
            if terms:
                clauses.append("location IS NOT NULL")
                clauses.append("(" + " OR ".join("LOWER(location) LIKE ?" for _ in terms) + ")")
                params.extend(f"%{term}%" for term in terms)

        cutoff = datetime.now(timezone.utc) - timedelta(days=q.days)
        clauses.append("retrieved_at >= ?")
        params.append(cutoff.isoformat())

        return " AND ".join(clauses), params

    def iter_postings(self, q: IngestionQuery, limit: int | None = None):
        where_sql, params = self._posting_where_clause(q)
        sql = (
            "SELECT id, title, company, location, retrieved_at, description_raw, role_bucket, level_bucket "
            "FROM postings "
            f"WHERE {where_sql} "
            "ORDER BY retrieved_at DESC"
        )
        if limit is not None:
            sql += " LIMIT ?"
            params = [*params, limit]
        cur = self.conn.cursor()
        return cur.execute(sql, params).fetchall()

    def export_postings(self, q: IngestionQuery, limit: int | None = None) -> list[dict[str, object]]:
        where_sql, params = self._posting_where_clause(q)
        sql = (
            "SELECT id, source, url, title, company, location, date_posted, retrieved_at, "
            "role_bucket, level_bucket, description_raw, raw_json "
            "FROM postings "
            f"WHERE {where_sql} "
            "ORDER BY retrieved_at DESC"
        )
        if limit is not None:
            sql += " LIMIT ?"
            params = [*params, limit]

        rows = self.conn.cursor().execute(sql, params).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            raw_json = item.pop("raw_json", "{}")
            try:
                item["raw"] = json.loads(str(raw_json))
            except json.JSONDecodeError:
                item["raw"] = {}
            out.append(item)
        return out

    def upsert_posting_skills(
        self,
        posting_id: str,
        skill_counts: dict[str, int],
        *,
        commit: bool = True,
    ) -> tuple[int, int]:
        inserted = 0
        updated_or_skipped = 0
        cur = self.conn.cursor()

        # We track existing rows to report insert vs update counts in script summaries.
        existing = {
            row["skill"]: row["count"]
            for row in cur.execute(
                "SELECT skill, count FROM posting_skills WHERE posting_id = ?",
                (posting_id,),
            ).fetchall()
        }

        for skill, count in skill_counts.items():
            cur.execute(
                """
                INSERT INTO posting_skills (posting_id, skill, count)
                VALUES (?, ?, ?)
                ON CONFLICT(posting_id, skill)
                DO UPDATE SET count = excluded.count
                """,
                (posting_id, skill, count),
            )
            if skill in existing:
                updated_or_skipped += 1
            else:
                inserted += 1

        if commit:
            self.conn.commit()
        return inserted, updated_or_skipped

    def commit(self) -> None:
        self.conn.commit()

    def get_postings_count(self, q: IngestionQuery) -> int:
        where_sql, params = self._posting_where_clause(q)
        cur = self.conn.cursor()
        row = cur.execute(
            f"SELECT COUNT(*) AS n FROM postings WHERE {where_sql}",
            params,
        ).fetchone()
        return int(row["n"]) if row else 0

    def get_unique_companies_count(self, q: IngestionQuery) -> int:
        where_sql, params = self._posting_where_clause(q)
        cur = self.conn.cursor()
        row = cur.execute(
            f"SELECT COUNT(DISTINCT company) AS n FROM postings WHERE {where_sql}",
            params,
        ).fetchone()
        return int(row["n"]) if row else 0

    @staticmethod
    def _split_location_options(location: str | None) -> list[str]:
        if not location:
            return []
        normalized = " ".join(location.split())
        parts = re.split(r"\s*(?:;|\||/|\bor\b)\s*", normalized, flags=re.IGNORECASE)
        return [part.strip(" ,-") for part in parts if part.strip(" ,-")]

    def list_available_locations(self, *, days: int = 30, limit: int = 100) -> list[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT location, COUNT(*) AS n
            FROM postings
            WHERE location IS NOT NULL
              AND TRIM(location) != ''
              AND retrieved_at >= ?
            GROUP BY location
            ORDER BY n DESC, location ASC
            """,
            (cutoff.isoformat(),),
        ).fetchall()

        counts: dict[str, int] = {}
        for row in rows:
            for option in self._split_location_options(row["location"]):
                if option.lower() in {"united states", "us", "usa", "u.s.", "u.s.a."}:
                    continue
                counts[option] = counts.get(option, 0) + int(row["n"])

        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
        return ["United States", *[location for location, _ in ordered[: max(0, limit - 1)]]]

    def close(self) -> None:
        self.conn.close()
