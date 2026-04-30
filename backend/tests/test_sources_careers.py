import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.careers import CareersAdapter


class TestCareersAdapter(unittest.TestCase):
    def test_missing_sources_file_explains_setup(self) -> None:
        adapter = CareersAdapter(sources_path="missing-career-sources.json")
        with self.assertRaisesRegex(FileNotFoundError, "career_sources.example.json"):
            adapter.fetch(IngestionQuery(location="Dallas, TX", role_bucket="backend", level_bucket="entry"))

    def test_greenhouse_source_maps_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources_path = Path(tmpdir) / "career_sources.json"
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "company": "Acme",
                            "type": "greenhouse",
                            "board_token": "acme",
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            adapter = CareersAdapter(sources_path=str(sources_path))
            adapter.REQUEST_DELAY_SECONDS = 0

            payload = {
                "jobs": [
                    {
                        "id": 123,
                        "title": "Junior Backend Engineer",
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
                        "updated_at": "2026-04-01T00:00:00Z",
                        "content": "<p>Python microservices</p>",
                        "offices": [{"name": "Dallas, TX"}],
                    }
                ]
            }

            with patch.object(adapter, "_get_json", return_value=payload):
                jobs = adapter.fetch(
                    IngestionQuery(location="Dallas, TX", role_bucket="backend", level_bucket="entry", max_results=10)
                )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source_kind"], "greenhouse")
        self.assertEqual(jobs[0]["company"], "Acme")
        self.assertEqual(jobs[0]["title"], "Junior Backend Engineer")
        self.assertEqual(jobs[0]["location"], "Dallas, TX")

    def test_fetch_applies_max_results_after_query_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources_path = Path(tmpdir) / "career_sources.json"
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "company": "Acme",
                            "type": "greenhouse",
                            "board_token": "acme",
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            adapter = CareersAdapter(sources_path=str(sources_path))
            adapter.REQUEST_DELAY_SECONDS = 0

            senior_jobs = [
                {
                    "id": i,
                    "title": "Senior Backend Engineer",
                    "absolute_url": f"https://boards.greenhouse.io/acme/jobs/{i}",
                    "updated_at": "2026-04-01T00:00:00Z",
                    "content": "<p>Python APIs</p>",
                    "offices": [{"name": "San Francisco, California"}],
                }
                for i in range(30)
            ]
            entry_jobs = [
                {
                    "id": 100 + i,
                    "title": "Software Engineer - New Grad",
                    "absolute_url": f"https://boards.greenhouse.io/acme/jobs/{100 + i}",
                    "updated_at": "2026-04-01T00:00:00Z",
                    "content": "<p>Build Python APIs and microservices.</p>",
                    "offices": [{"name": "San Francisco, California"}],
                }
                for i in range(3)
            ]
            non_software_entry_job = {
                "id": 200,
                "title": "Technical Recruiter - New Grad",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/200",
                "updated_at": "2026-04-01T00:00:00Z",
                "content": "<p>Partner with engineering teams.</p>",
                "offices": [{"name": "San Francisco, California"}],
            }
            payload = {"jobs": [*senior_jobs, non_software_entry_job, *entry_jobs]}

            with patch.object(adapter, "_get_json", return_value=payload):
                jobs = adapter.fetch(
                    IngestionQuery(
                        location="San Francisco Bay Area",
                        role_bucket="any",
                        level_bucket="entry",
                        max_results=2,
                    )
                )

        self.assertEqual(len(jobs), 2)
        self.assertTrue(all("New Grad" in job["title"] for job in jobs))
        self.assertTrue(all("Recruiter" not in job["title"] for job in jobs))

    def test_united_states_filter_does_not_match_foreign_substrings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources_path = Path(tmpdir) / "career_sources.json"
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "company": "Acme",
                            "type": "greenhouse",
                            "board_token": "acme",
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            adapter = CareersAdapter(sources_path=str(sources_path))
            adapter.REQUEST_DELAY_SECONDS = 0

            payload = {
                "jobs": [
                    {
                        "id": 1,
                        "title": "Junior Software Engineer",
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
                        "content": "<p>Python APIs</p>",
                        "offices": [{"name": "Warsaw, Poland"}],
                    },
                    {
                        "id": 2,
                        "title": "Junior Software Engineer",
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/2",
                        "content": "<p>Python APIs</p>",
                        "offices": [{"name": "Mexico City, MX"}],
                    },
                    {
                        "id": 3,
                        "title": "Junior Software Engineer",
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/3",
                        "content": "<p>Python APIs</p>",
                        "offices": [{"name": "Seattle, WA"}],
                    },
                ]
            }

            with patch.object(adapter, "_get_json", return_value=payload):
                jobs = adapter.fetch(
                    IngestionQuery(location="United States", role_bucket="any", level_bucket="entry", max_results=10)
                )

        self.assertEqual([job["location"] for job in jobs], ["Seattle, WA"])

    def test_lever_source_maps_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources_path = Path(tmpdir) / "career_sources.json"
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "company": "Beta",
                            "type": "lever",
                            "company_slug": "beta",
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            adapter = CareersAdapter(sources_path=str(sources_path))
            adapter.REQUEST_DELAY_SECONDS = 0

            payload = [
                {
                    "id": "abc",
                    "text": "Junior API Engineer",
                    "hostedUrl": "https://jobs.lever.co/beta/abc",
                    "createdAt": 1775000000000,
                    "categories": {"location": "Dallas, TX"},
                    "lists": [{"content": "<p>Build REST APIs with SQL.</p>"}],
                }
            ]

            with patch.object(adapter, "_get_json", return_value=payload):
                jobs = adapter.fetch(
                    IngestionQuery(location="Dallas, TX", role_bucket="backend", level_bucket="entry", max_results=10)
                )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source_kind"], "lever")
        self.assertEqual(jobs[0]["company"], "Beta")
        self.assertIn("REST APIs", jobs[0]["description"])

    def test_generic_html_respects_robots_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources_path = Path(tmpdir) / "career_sources.json"
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "company": "Gamma",
                            "type": "generic_html",
                            "url": "https://example.com/careers",
                            "respect_robots": True,
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            adapter = CareersAdapter(sources_path=str(sources_path))
            adapter.REQUEST_DELAY_SECONDS = 0

            with patch.object(adapter, "_robots_allowed", return_value=False):
                with patch.object(adapter, "_get_text") as mock_get_text:
                    jobs = adapter.fetch(
                        IngestionQuery(location="Dallas, TX", role_bucket="backend", level_bucket="entry", max_results=10)
                    )

        self.assertEqual(jobs, [])
        mock_get_text.assert_not_called()
