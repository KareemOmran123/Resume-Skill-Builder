import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_ingest_module():
    ingest_path = ROOT / "scripts" / "ingest.py"
    spec = importlib.util.spec_from_file_location("ingest", ingest_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestIngestScript(unittest.TestCase):
    def test_setup_logger_creates_handlers(self) -> None:
        ingest = _load_ingest_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "ingest.log"
            logger = ingest.setup_logger(str(log_path))
            self.assertGreaterEqual(len(logger.handlers), 2)
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
