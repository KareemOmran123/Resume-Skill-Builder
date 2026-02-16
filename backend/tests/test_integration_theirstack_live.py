import os
import unittest

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.theirstack import TheirstackAdapter


@unittest.skipUnless(
    os.getenv("THEIRSTACK_API_KEY"),
    "Set THEIRSTACK_API_KEY to run live TheirStack integration checks.",
)
class TestTheirstackLiveIntegration(unittest.TestCase):
    def test_live_fetch_shape(self) -> None:
        adapter = TheirstackAdapter()
        q = IngestionQuery(
            location="United States",
            role_bucket="any",
            level_bucket="any",
            days=14,
            max_results=5,
        )

        rows = adapter.fetch(q)
        self.assertIsInstance(rows, list)
        if rows:
            self.assertIsInstance(rows[0], dict)
            expected_any = {"id", "job_title", "url", "final_url", "source_url"}
            self.assertTrue(any(k in rows[0] for k in expected_any))

