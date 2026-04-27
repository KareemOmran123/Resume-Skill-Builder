import importlib.util
import unittest
from pathlib import Path

from skillpulse_ingest.runtime_paths import DEFAULT_DB_PATH, DEFAULT_LOG_PATH, DEFAULT_SAMPLE_PATH

ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name: str):
    script_path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestScriptDefaults(unittest.TestCase):
    def test_ingest_defaults_use_backend_paths(self) -> None:
        ingest = _load_script_module("ingest")
        args = ingest.build_parser().parse_args([])
        self.assertEqual(Path(args.db), DEFAULT_DB_PATH)
        self.assertEqual(Path(args.log), DEFAULT_LOG_PATH)

    def test_extract_defaults_use_backend_db(self) -> None:
        extract = _load_script_module("extract_skills")
        args = extract.build_parser().parse_args([])
        self.assertEqual(Path(args.db), DEFAULT_DB_PATH)
        self.assertIsNone(args.sample_out)

    def test_skill_insights_defaults_use_backend_db(self) -> None:
        skill_insights = _load_script_module("skill_insights")
        args = skill_insights.build_parser().parse_args([])
        self.assertEqual(Path(args.db), DEFAULT_DB_PATH)

    def test_inspect_db_defaults_use_backend_db(self) -> None:
        inspect_db = _load_script_module("inspect_db")
        args = inspect_db.build_parser().parse_args([])
        self.assertEqual(Path(args.db), DEFAULT_DB_PATH)

    def test_run_backend_defaults_use_backend_paths(self) -> None:
        run_backend = _load_script_module("run_backend")
        args = run_backend.build_parser().parse_args([])
        self.assertEqual(Path(args.db), DEFAULT_DB_PATH)
        self.assertEqual(Path(args.log), DEFAULT_LOG_PATH)
        self.assertEqual(Path(args.sample_out), DEFAULT_SAMPLE_PATH)
