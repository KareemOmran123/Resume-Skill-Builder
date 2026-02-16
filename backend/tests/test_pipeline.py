import unittest
from datetime import datetime, timezone

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.pipeline import get_source, run_pipeline
from skillpulse_ingest.sources.remotive import RemotiveAdapter


class FakeAdapter:
    name = "theirstack"

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def fetch(self, q: IngestionQuery) -> list[dict]:
        return self._rows


class BrokenAdapter:
    name = "theirstack"

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
    def test_run_pipeline_filters_senior(self) -> None:
        rows = [
            {
                "id": "1",
                "job_title": "Senior Backend Engineer",
                "company": "Acme",
                "description": "Senior role",
                "date_posted": datetime.now(timezone.utc).isoformat(),
                "final_url": "https://example.com/senior",
            },
            {
                "id": "2",
                "job_title": "Junior Backend Engineer",
                "company": "Acme",
                "description": "Entry level role",
                "date_posted": datetime.now(timezone.utc).isoformat(),
                "final_url": "https://example.com/junior",
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

    def test_get_source_remotive(self) -> None:
        adapter = get_source("remotive")
        self.assertIsInstance(adapter, RemotiveAdapter)

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
                "job_title": "Junior Backend Engineer",
                "company": {"name": "Acme"},
                "description": ["entry", "backend"],
                "date_posted": datetime.now(timezone.utc),
                "final_url": "https://example.com/field-shapes",
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
