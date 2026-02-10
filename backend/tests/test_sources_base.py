import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.sources.base import SourceAdapter


class DummyAdapter(SourceAdapter):
    name = "dummy"

    def fetch(self, q: IngestionQuery):
        return []


class TestSourceAdapter(unittest.TestCase):
    def test_abstract_base_cannot_instantiate(self) -> None:
        with self.assertRaises(TypeError):
            SourceAdapter()  # type: ignore[abstract]

    def test_dummy_adapter_implements_fetch(self) -> None:
        adapter = DummyAdapter()
        q = IngestionQuery(location="X", role_bucket="any", level_bucket="any")
        self.assertEqual(adapter.fetch(q), [])
