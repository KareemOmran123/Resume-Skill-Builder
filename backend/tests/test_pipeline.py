import unittest
from datetime import datetime, timezone

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.pipeline import get_source, run_pipeline
from skillpulse_ingest.sources.jobspy import JobSpyAdapter


class FakeAdapter:
    name = "jobspy"

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def fetch(self, q: IngestionQuery) -> list[dict]:
        return self._rows


class BrokenAdapter:
    name = "jobspy"

    def fetch(self, q: IngestionQuery) -> list[dict]:
        raise RuntimeError("network failure")


class FakeStore:
    def __init__(self) -> None:
        self.received = []

    def upsert_many(self, postings):
        self.received.extend(postings)
        return (len(postings), 0)


class FakeLogger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


class TestPipeline(unittest.TestCase):
    def test_get_source_default_is_jobspy(self) -> None:
        adapter = get_source()
        self.assertIsInstance(adapter, JobSpyAdapter)

    def test_run_pipeline_filters_senior(self) -> None:
        rows = [
            {
                "id": "1",
                "title": "Senior Backend Engineer",
                "company": "Acme",
                "description": "Senior role",
                "date_posted": datetime.now(timezone.utc).isoformat(),
                "job_url": "https://example.com/senior",
                "site": "indeed",
            },
            {
                "id": "2",
                "title": "Junior Backend Engineer",
                "company": "Acme",
                "description": "Entry level role",
                "date_posted": datetime.now(timezone.utc).isoformat(),
                "job_url": "https://example.com/junior",
                "site": "indeed",
            },
        ]

        q = IngestionQuery(
            location="Dallas, TX",
            role_bucket="backend",
            level_bucket="entry",
            days=7,
            max_results=50,
        )
        store = FakeStore()
        logger = FakeLogger()

        run_pipeline(q, [FakeAdapter(rows)], store, logger)

        self.assertEqual(len(store.received), 1)
        self.assertEqual(store.received[0].title, "Junior Backend Engineer")

    def test_get_source_unknown_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_source("unknown")

    def test_get_source_jobspy(self) -> None:
        adapter = get_source("jobspy")
        self.assertIsInstance(adapter, JobSpyAdapter)

    def test_run_pipeline_normalizes_jobspy_source(self) -> None:
        rows = [
            {
                "id": "abc",
                "site": "linkedin",
                "title": "Junior Backend Engineer",
                "company": "Acme",
                "location": "Dallas, TX",
                "description": "Build Python APIs and microservices.",
                "date_posted": datetime.now(timezone.utc).isoformat(),
                "job_url": "https://example.com/jobs/abc",
            }
        ]

        q = IngestionQuery(
            location="Dallas, TX",
            role_bucket="backend",
            level_bucket="entry",
            days=7,
            max_results=50,
        )
        store = FakeStore()
        logger = FakeLogger()

        run_pipeline(q, [FakeAdapter(rows)], store, logger)
        self.assertEqual(len(store.received), 1)
        self.assertEqual(store.received[0].source, "jobspy")
        self.assertEqual(store.received[0].title, "Junior Backend Engineer")

    def test_run_pipeline_handles_fetch_errors(self) -> None:
        q = IngestionQuery(
            location="Dallas, TX",
            role_bucket="backend",
            level_bucket="entry",
            days=7,
            max_results=50,
        )
        store = FakeStore()
        logger = FakeLogger()
        run_pipeline(q, [BrokenAdapter()], store, logger)
        self.assertEqual(store.received, [])

    def test_run_pipeline_normalizes_non_string_fields(self) -> None:
        rows = [
            {
                "id": "3",
                "title": "Junior Backend Engineer",
                "company": {"name": "Acme"},
                "description": ["entry", "backend"],
                "date_posted": datetime.now(timezone.utc),
                "job_url": "https://example.com/field-shapes",
            }
        ]

        q = IngestionQuery(
            location="Dallas, TX",
            role_bucket="backend",
            level_bucket="entry",
            days=7,
            max_results=50,
        )
        store = FakeStore()
        logger = FakeLogger()
        run_pipeline(q, [FakeAdapter(rows)], store, logger)
        self.assertEqual(len(store.received), 1)
        self.assertEqual(store.received[0].company, "Acme")

    def test_run_pipeline_filters_jobspy_non_software_titles(self) -> None:
        rows = [
            {
                "id": "4",
                "title": "AI-Driven OSINT Analyst",
                "company": "Acme",
                "description": "Machine Learning Engineer duties with Python.",
                "date_posted": datetime.now(timezone.utc),
                "job_url": "https://example.com/noisy",
            },
            {
                "id": "5",
                "title": "Junior Software Developer",
                "company": "Beta",
                "description": "Build Python APIs.",
                "date_posted": datetime.now(timezone.utc),
                "job_url": "https://example.com/software",
            },
        ]

        q = IngestionQuery(
            location="United States",
            role_bucket="any",
            level_bucket="any",
            days=7,
            max_results=50,
        )
        store = FakeStore()
        logger = FakeLogger()
        run_pipeline(q, [FakeAdapter(rows)], store, logger)

        self.assertEqual(len(store.received), 1)
        self.assertEqual(store.received[0].title, "Junior Software Developer")
