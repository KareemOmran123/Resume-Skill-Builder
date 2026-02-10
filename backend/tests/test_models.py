import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from skillpulse_ingest.models import JobPosting


class TestModels(unittest.TestCase):
    def test_make_id_is_deterministic_and_short(self) -> None:
        a = JobPosting.make_id("source", "http://example.com/job/1")
        b = JobPosting.make_id("source", "http://example.com/job/1")
        c = JobPosting.make_id("source", "http://example.com/job/2")

        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(a), 32)

    def test_jobposting_to_json_serializes_fields(self) -> None:
        p = JobPosting(
            id="abc",
            source="theirstack",
            url="https://example.com",
            title="Backend Engineer",
            company="Acme",
            location="Dallas, TX",
            date_posted="2026-02-01T12:00:00Z",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
            role_bucket="backend",
            level_bucket="entry",
            description_raw="Build APIs",
            raw={"foo": "bar"},
        )

        raw = json.loads(p.to_json())
        self.assertEqual(raw["id"], "abc")
        self.assertEqual(raw["source"], "theirstack")
        self.assertEqual(raw["company"], "Acme")
