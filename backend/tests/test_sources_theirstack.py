import os
import unittest
from unittest.mock import patch

import requests

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.pipeline import _normalize_theirstack
from skillpulse_ingest.sources.theirstack import TheirstackAdapter


class DummyResponse:
    def __init__(self, payload, *, status_code: int = 200, text: str = "") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.ok = status_code < 400

    def raise_for_status(self) -> None:
        if not self.ok:
            response = requests.Response()
            response.status_code = self.status_code
            response._content = self.text.encode("utf-8")
            raise requests.HTTPError(f"{self.status_code} Client Error", response=response)

    def json(self) -> dict:
        return self._payload


class TestTheirstackAdapter(unittest.TestCase):
    def test_requires_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "THEIRSTACK_API_KEY environment variable is required"):
                TheirstackAdapter()

    def test_fetch_builds_minimal_payload_with_location(self) -> None:
        payload = {"metadata": {}, "data": [{"id": "1", "job_title": "Backend Engineer"}]}

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
                self.assertEqual(args[0], "https://api.theirstack.com/v1/jobs/search")
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
                self.assertEqual(kwargs["headers"]["Accept"], "application/json")
                self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

                body = kwargs["json"]
                self.assertEqual(
                    body,
                    {
                        "page": 0,
                        "limit": 5,
                        "job_country_code_or": ["US"],
                        "posted_at_max_age_days": 7,
                        "job_title_or": ["backend engineer", "back end engineer", "software engineer", "api engineer"],
                        "job_location_pattern_or": ["Dallas", "Dallas-Fort Worth", "DFW"],
                        "include_total_results": False,
                        "job_seniority_or": ["junior"],
                        "job_title_not": ["senior", "sr", "lead", "staff", "principal", "manager", "director"],
                        "job_description_contains_not": ["senior", "lead", "staff", "principal", "manager", "director"],
                    },
                )

    def test_build_payload_maps_query_filters(self) -> None:
        adapter = TheirstackAdapter(api_key="test-key")
        q = IngestionQuery(
            location="San Francisco Bay Area",
            role_bucket="frontend",
            level_bucket="entry",
            days=30,
            max_results=50,
        )

        body = adapter.build_payload(q, page=2, limit=25)

        self.assertEqual(body["page"], 2)
        self.assertEqual(body["limit"], 25)
        self.assertEqual(body["posted_at_max_age_days"], 30)
        self.assertIn("react developer", body["job_title_or"])
        self.assertEqual(body["job_seniority_or"], ["junior"])
        self.assertEqual(body["job_location_pattern_or"], ["San Francisco", "Bay Area", "San Jose", "Oakland"])
        self.assertNotIn("job_title_pattern_or", body)
        self.assertNotIn("entry", body["job_seniority_or"])
        self.assertNotIn("entry_level", body["job_seniority_or"])

    def test_fetch_parses_data_key_response(self) -> None:
        payload = {"metadata": {}, "data": [{"job_id": "1", "title": "Frontend Engineer"}]}

        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                mock_post.return_value = DummyResponse(payload)
                adapter = TheirstackAdapter()
                q = IngestionQuery(
                    location="Seattle, WA",
                    role_bucket="frontend",
                    level_bucket="entry",
                    days=30,
                    max_results=5,
                )

                jobs = adapter.fetch(q)

        self.assertEqual(jobs, payload["data"])

    def test_fetch_raises_clear_error_for_unknown_response_shape(self) -> None:
        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                mock_post.return_value = DummyResponse({"unexpected": []})
                adapter = TheirstackAdapter()
                q = IngestionQuery(
                    location="Seattle, WA",
                    role_bucket="frontend",
                    level_bucket="entry",
                    days=30,
                    max_results=5,
                )

                with self.assertRaisesRegex(ValueError, "Top-level keys: unexpected"):
                    adapter.fetch(q)

    def test_normalizes_theirstack_fallback_fields(self) -> None:
        raw = {
            "job_id": "job-123",
            "title": "Junior API Engineer",
            "company_name": "Example Co",
            "short_location": "Dallas, TX",
            "final_url": "https://example.com/jobs/123",
            "discovered_at": "2026-02-01T00:00:00Z",
            "job_description": "Entry level Python and REST API role.",
        }

        posting = _normalize_theirstack(raw)

        self.assertEqual(posting.source, "theirstack")
        self.assertEqual(posting.title, "Junior API Engineer")
        self.assertEqual(posting.company, "Example Co")
        self.assertEqual(posting.location, "Dallas, TX")
        self.assertEqual(posting.url, "https://example.com/jobs/123")
        self.assertEqual(posting.date_posted, "2026-02-01T00:00:00Z")
        self.assertEqual(posting.description_raw, "Entry level Python and REST API role.")
        self.assertEqual(posting.raw, raw)

    def test_fetch_prints_payload_for_http_errors(self) -> None:
        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                mock_post.return_value = DummyResponse(
                    {"detail": "bad request"},
                    status_code=422,
                    text='{"detail":"bad request"}',
                )
                adapter = TheirstackAdapter()
                q = IngestionQuery(
                    location="Dallas, TX",
                    role_bucket="backend",
                    level_bucket="entry",
                    days=30,
                    max_results=5,
                )

                with patch("builtins.print") as mock_print:
                    with self.assertRaises(requests.HTTPError):
                        adapter.fetch(q)

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        self.assertIn("TheirStack error status=422", printed)
        self.assertIn("TheirStack error response=", printed)
        self.assertIn("TheirStack request payload=", printed)
        self.assertNotIn("test-key", printed)

    def test_fetch_uses_plan_safe_page_limit(self) -> None:
        first_page = {"data": [{"id": str(i), "job_title": "Backend Engineer"} for i in range(25)]}
        second_page = {"data": [{"id": str(i), "job_title": "Backend Engineer"} for i in range(25, 30)]}

        with patch.dict(os.environ, {"THEIRSTACK_API_KEY": "test-key"}, clear=True):
            with patch("skillpulse_ingest.sources.theirstack.requests.post") as mock_post:
                mock_post.side_effect = [DummyResponse(first_page), DummyResponse(second_page)]
                adapter = TheirstackAdapter()
                q = IngestionQuery(
                    location="Dallas, TX",
                    role_bucket="backend",
                    level_bucket="entry",
                    days=30,
                    max_results=50,
                )

                jobs = adapter.fetch(q)

        self.assertEqual(len(jobs), 30)
        first_body = mock_post.call_args_list[0].kwargs["json"]
        second_body = mock_post.call_args_list[1].kwargs["json"]
        self.assertEqual(first_body["page"], 0)
        self.assertEqual(first_body["limit"], 25)
        self.assertEqual(second_body["page"], 1)
        self.assertEqual(second_body["limit"], 25)

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
