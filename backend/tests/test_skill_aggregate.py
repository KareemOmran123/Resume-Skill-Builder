from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from skillpulse_ingest.models import IngestionQuery, JobPosting
from skillpulse_ingest.skill_aggregate import aggregate_skills
from skillpulse_ingest.storage_sqlite import SQLiteStore


def _posting(url: str, company: str = "Acme") -> JobPosting:
    return JobPosting(
        id=JobPosting.make_id("theirstack", url),
        source="theirstack",
        url=url,
        title="Backend Engineer",
        company=company,
        location="Dallas, TX",
        date_posted="2026-02-01T12:00:00Z",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        role_bucket="backend",
        level_bucket="entry",
        description_raw="Python and APIs",
        raw={"url": url},
    )


class TestSkillAggregate(unittest.TestCase):
    def test_aggregate_uses_distinct_postings_denominator_and_sort(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "skillpulse.db"
            store = SQLiteStore(str(db_path))

            p1 = _posting("https://example.com/1", company="Acme")
            p2 = _posting("https://example.com/2", company="Beta")
            p3 = _posting("https://example.com/3", company="Gamma")
            p4 = _posting("https://example.com/4", company="Delta")
            store.upsert_many([p1, p2, p3, p4])

            store.upsert_posting_skills(p1.id, {"Python": 2, "REST APIs": 1})
            store.upsert_posting_skills(p2.id, {"Python": 1, "Docker / Containers": 1})
            store.upsert_posting_skills(p3.id, {"AWS": 1})
            # p4 intentionally has no extracted skills, but should remain in denominator.

            q = IngestionQuery(location="Dallas", role_bucket="backend", level_bucket="entry", days=30)
            skills = aggregate_skills(str(db_path), q, top_n=10)

            self.assertEqual(skills[0]["name"], "Python")
            self.assertEqual(skills[0]["count"], 2)
            self.assertEqual(skills[0]["pct"], 50)

            tied = [s for s in skills if s["count"] == 1 and s["pct"] == 25]
            tied_names = [s["name"] for s in tied]
            self.assertEqual(tied_names, sorted(tied_names))

            store.close()
