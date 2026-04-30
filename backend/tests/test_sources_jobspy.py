import os
import json
import unittest
from unittest.mock import MagicMock, patch

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.jobspy import DEFAULT_SITES, JobSpyAdapter


class FakeDataFrame:
    def __init__(self, records):
        self.records = records

    def to_dict(self, orient):
        self.orient = orient
        return self.records


class TestJobSpyAdapter(unittest.TestCase):
    def test_uses_default_sites(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            adapter = JobSpyAdapter()
        self.assertEqual(adapter.sites, list(DEFAULT_SITES))

    def test_reads_sites_from_environment(self) -> None:
        with patch.dict(os.environ, {"JOBSPY_SITES": "indeed, google"}, clear=True):
            adapter = JobSpyAdapter()
        self.assertEqual(adapter.sites, ["indeed", "google"])

    def test_fetch_calls_jobspy_and_returns_records(self) -> None:
        adapter = JobSpyAdapter(sites=["indeed"])
        q = IngestionQuery(location="Dallas, TX", role_bucket="backend", level_bucket="entry", days=7, max_results=2)

        dataframe = FakeDataFrame(
            [
                {"site": "indeed", "title": "Junior Backend Engineer", "company": "Acme"},
                {"site": "indeed", "title": "Backend Developer", "company": "Beta"},
            ]
        )

        with patch.dict("sys.modules", {"jobspy": MagicMock(scrape_jobs=MagicMock(return_value=dataframe))}):
            jobs = adapter.fetch(q)

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["title"], "Junior Backend Engineer")

    def test_fetch_passes_documented_options_from_environment(self) -> None:
        adapter = JobSpyAdapter(sites=["indeed", "glassdoor"])
        q = IngestionQuery(location="United States", role_bucket="any", level_bucket="any", days=3, max_results=5)
        scrape_jobs = MagicMock(return_value=FakeDataFrame([]))

        with patch.dict(
            os.environ,
            {
                "JOBSPY_PROXIES": "localhost, user:pass@example.com:1234",
                "JOBSPY_DISTANCE": "25",
                "JOBSPY_JOB_TYPE": "fulltime",
                "JOBSPY_REMOTE": "true",
                "JOBSPY_LINKEDIN_FETCH_DESCRIPTION": "1",
                "JOBSPY_VERBOSE": "0",
            },
            clear=True,
        ):
            with patch.dict("sys.modules", {"jobspy": MagicMock(scrape_jobs=scrape_jobs)}):
                adapter.fetch(q)

        kwargs = scrape_jobs.call_args.kwargs
        self.assertEqual(kwargs["site_name"], ["indeed", "glassdoor"])
        self.assertEqual(kwargs["country_indeed"], "USA")
        self.assertEqual(kwargs["hours_old"], 72)
        self.assertEqual(kwargs["proxies"], ["localhost", "user:pass@example.com:1234"])
        self.assertEqual(kwargs["distance"], 25)
        self.assertEqual(kwargs["job_type"], "fulltime")
        self.assertIs(kwargs["is_remote"], True)
        self.assertIs(kwargs["linkedin_fetch_description"], True)
        self.assertEqual(kwargs["verbose"], 0)

    def test_records_are_json_safe(self) -> None:
        rows = JobSpyAdapter._to_records(
            [
                {
                    "title": "Backend Engineer",
                    "company": float("nan"),
                    "nested": {"value": float("nan")},
                }
            ]
        )

        self.assertIsNone(rows[0]["company"])
        self.assertIsNone(rows[0]["nested"]["value"])
        json.dumps(rows[0])
