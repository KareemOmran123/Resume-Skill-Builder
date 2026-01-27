from __future__ import annotations

import sqlite3
from typing import Iterable
from .models import JobPosting

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
"""

class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
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
                        p.id, p.source, p.url, p.title, p.company, p.location, p.date_posted, p.retrieved_at,
                        p.role_bucket, p.level_bucket, p.description_raw, __import__("json").dumps(p.raw, ensure_ascii=False),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        self.conn.commit()
        return inserted, skipped

    def close(self) -> None:
        self.conn.close()
