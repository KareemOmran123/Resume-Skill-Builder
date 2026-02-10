import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.remotive import RemotiveAdapter


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class TestRemotiveAdapter(unittest.TestCase):
    def test_fetch_filters_by_date_and_search(self) -> None:
        recent = datetime.now(timezone.utc).isoformat()
        payload = {
            "jobs": [
                {
                    "id": 1,
                    "title": "Backend Engineer",
                    "company_name": "Acme",
                    "publication_date": recent,
                    "description": "APIs",
                },
                {
                    "id": 2,
                    "title": "Old Role",
                    "company_name": "OldCo",
                    "publication_date": "2000-01-01T00:00:00Z",
                    "description": "Legacy",
                },
            ]
        }

        with patch("skillpulse_ingest.sources.remotive.requests.get") as mock_get:
            mock_get.return_value = DummyResponse(payload)
            adapter = RemotiveAdapter()
            q = IngestionQuery(
                location="Dallas, TX",
                role_bucket="backend",
                level_bucket="any",
                days=2,
                max_results=10,
            )
            jobs = adapter.fetch(q)

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["title"], "Backend Engineer")
            _, kwargs = mock_get.call_args
            self.assertIn("params", kwargs)
            self.assertEqual(kwargs["params"].get("search"), "backend")

    def test_fetch_without_role_bucket(self) -> None:
        payload = {"jobs": []}
        with patch("skillpulse_ingest.sources.remotive.requests.get") as mock_get:
            mock_get.return_value = DummyResponse(payload)
            adapter = RemotiveAdapter()
            q = IngestionQuery(
                location="Dallas, TX",
                role_bucket="any",
                level_bucket="any",
                days=2,
                max_results=10,
            )
            adapter.fetch(q)
            _, kwargs = mock_get.call_args
            self.assertEqual(kwargs.get("params"), {})
