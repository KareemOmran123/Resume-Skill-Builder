import os
import unittest
from unittest.mock import patch

import requests

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.theirstack import TheirstackAdapter


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class TestTheirstackAdapter(unittest.TestCase):
    def test_requires_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                TheirstackAdapter()

    def test_fetch_builds_payload_with_location(self) -> None:
        payload = {"data": [{"id": "1", "job_title": "Backend Engineer"}]}

        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                mock_post.return_value = DummyResponse(payload)
                adapter = TheirstackAdapter()
                q = IngestionQuery(
                    location="Dallas, TX",
                    role_bucket="backend",
                    level_bucket="entry",
                    days=7,
                    max_results=5,
                )
                jobs = adapter.fetch(q)

                self.assertEqual(len(jobs), 1)
                args, kwargs = mock_post.call_args
                self.assertIn("headers", kwargs)
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
                body = kwargs["json"]
                self.assertEqual(body["posted_at_max_age_days"], 7)
                self.assertIn("job_location_pattern_or", body)
                self.assertIn("Dallas", body["job_location_pattern_or"][0])
                self.assertEqual(body["job_title_or"], ["backend"])
                self.assertIn("job_seniority_or", body)

    def test_fetch_retries_transient_errors(self) -> None:
        payload = {"data": []}
        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.time.sleep", return_value=None):
                with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                    mock_post.side_effect = [
                        requests.ConnectionError("temporary"),
                        DummyResponse(payload),
                    ]
                    adapter = TheirstackAdapter()
                    q = IngestionQuery(
                        location="Dallas, TX",
                        role_bucket="any",
                        level_bucket="any",
                        days=7,
                        max_results=5,
                    )
                    jobs = adapter.fetch(q)
                    self.assertEqual(jobs, [])
                    self.assertEqual(mock_post.call_count, 2)
