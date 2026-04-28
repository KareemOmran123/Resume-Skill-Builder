import importlib.util
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
        generated_dir = ROOT / "tests" / "_generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        log_path = generated_dir / "ingest.log"
        if log_path.exists():
            log_path.unlink()

        logger = ingest.setup_logger(str(log_path))
        self.assertGreaterEqual(len(logger.handlers), 2)
        self.assertTrue(log_path.exists())
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

        if log_path.exists():
            log_path.unlink()
        if generated_dir.exists() and not any(generated_dir.iterdir()):
            generated_dir.rmdir()
