from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from skillpulse_ingest.models import IngestionQuery, JobPosting
from skillpulse_ingest.storage_sqlite import SQLiteStore


def _make_posting(url: str, *, company: str = "Acme", location: str = "Dallas, TX", role: str = "backend", level: str = "entry", retrieved_at: str | None = None, description: str = "Build APIs") -> JobPosting:
    return JobPosting(
        id=JobPosting.make_id("theirstack", url),
        source="theirstack",
        url=url,
        title="Backend Engineer",
        company=company,
        location=location,
        date_posted="2026-02-01T12:00:00Z",
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat(),
        role_bucket=role,
        level_bucket=level,
        description_raw=description,
        raw={"url": url},
    )


class TestSQLiteStore(unittest.TestCase):
    def test_upsert_inserts_and_skips(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "skillpulse.db"
            store = SQLiteStore(str(db_path))

            p1 = _make_posting("https://example.com/1")
            p2 = _make_posting("https://example.com/2")

            inserted, skipped = store.upsert_many([p1, p2])
            self.assertEqual(inserted, 2)
            self.assertEqual(skipped, 0)

            inserted, skipped = store.upsert_many([p1, p2])
            self.assertEqual(inserted, 0)
            self.assertEqual(skipped, 2)

            store.close()

    def test_posting_skills_upsert(self) -> None:
        store = SQLiteStore(":memory:")
        p = _make_posting("https://example.com/skill")
        store.upsert_many([p])

        inserted, updated = store.upsert_posting_skills(p.id, {"Python": 2, "React": 1})
        self.assertEqual(inserted, 2)
        self.assertEqual(updated, 0)

        inserted, updated = store.upsert_posting_skills(p.id, {"Python": 3, "React": 1})
        self.assertEqual(inserted, 0)
        self.assertEqual(updated, 2)

        rows = store.conn.execute(
            "SELECT skill, count FROM posting_skills WHERE posting_id = ? ORDER BY skill",
            (p.id,),
        ).fetchall()
        self.assertEqual([(r["skill"], r["count"]) for r in rows], [("Python", 3), ("React", 1)])

        store.close()

    def test_iter_postings_and_counts(self) -> None:
        store = SQLiteStore(":memory:")
        now = datetime.now(timezone.utc)
        fresh = now.isoformat()
        stale = (now - timedelta(days=45)).isoformat()

        p1 = _make_posting("https://example.com/a", company="Acme", retrieved_at=fresh)
        p2 = _make_posting("https://example.com/b", company="Beta", retrieved_at=fresh)
        p3 = _make_posting("https://example.com/c", company="Acme", location="Austin, TX", retrieved_at=fresh)
        p4 = _make_posting("https://example.com/d", company="Old", retrieved_at=stale)
        store.upsert_many([p1, p2, p3, p4])

        q = IngestionQuery(location="Dallas", role_bucket="backend", level_bucket="entry", days=30)

        rows = store.iter_postings(q)
        self.assertEqual(len(rows), 2)
        self.assertEqual(store.get_postings_count(q), 2)
        self.assertEqual(store.get_unique_companies_count(q), 2)

        limited = store.iter_postings(q, limit=1)
        self.assertEqual(len(limited), 1)

        store.close()
