from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from skillpulse_ingest.models import JobPosting
from skillpulse_ingest.storage_sqlite import SQLiteStore


def _make_posting(url: str) -> JobPosting:
    return JobPosting(
        id=JobPosting.make_id("theirstack", url),
        source="theirstack",
        url=url,
        title="Backend Engineer",
        company="Acme",
        location="Dallas, TX",
        date_posted="2026-02-01T12:00:00Z",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        role_bucket="backend",
        level_bucket="entry",
        description_raw="Build APIs",
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
