from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Iterable

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
                        __import__("json").dumps(p.raw, ensure_ascii=False),
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
            clauses.append("location IS NOT NULL")
            clauses.append("LOWER(location) LIKE ?")
            params.append(f"%{q.location.lower()}%")

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

    def upsert_posting_skills(self, posting_id: str, skill_counts: dict[str, int]) -> tuple[int, int]:
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

        self.conn.commit()
        return inserted, updated_or_skipped

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

    def close(self) -> None:
        self.conn.close()
