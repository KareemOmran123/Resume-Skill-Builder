import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from skillpulse_ingest.workflow import ExtractionSummary

ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name: str):
    script_path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestRunBackendScript(unittest.TestCase):
    def test_main_runs_all_stages_and_writes_output(self) -> None:
        run_backend = _load_script_module("run_backend")
        out_dir = ROOT / "tests" / "_generated"
        out_path = out_dir / "skill_insights.json"
        if out_path.exists():
            out_path.unlink()
        if out_dir.exists():
            for child in out_dir.iterdir():
                if child.is_file():
                    child.unlink()

        payload = {
            "title": "Junior Backend Software Engineer",
            "subtitle": "Based on 2 job postings in Dallas, TX from the last 30 days",
            "window": {"days": 30},
            "filters": {
                "location": "Dallas, TX",
                "role_bucket": "backend",
                "level_bucket": "entry",
                "days": 30,
                "max_results": 250,
            },
            "totals": {
                "postings_count": 2,
                "unique_companies_count": 2,
            },
            "skills": [{"name": "Python", "count": 2, "pct": 100}],
            "generated_at": "2026-04-26T00:00:00Z",
            "schema_version": "1.0.0",
        }

        with patch.object(run_backend, "ingest_postings") as mock_ingest:
            with patch.object(run_backend, "extract_posting_skills") as mock_extract:
                with patch.object(run_backend, "build_skill_insights") as mock_build:
                    mock_extract.return_value = ExtractionSummary(
                        postings_processed=2,
                        postings_with_skills=2,
                        skills_inserted=4,
                        skills_updated_or_skipped=0,
                        sample_out=str(ROOT / "logs" / "skills_sample.json"),
                    )
                    mock_build.return_value = payload

                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        run_backend.main(["--role", "backend", "--level", "entry", "--out", str(out_path)])

        mock_ingest.assert_called_once()
        mock_extract.assert_called_once()
        mock_build.assert_called_once()
        self.assertEqual(json.loads(stdout.getvalue()), payload)
        self.assertTrue(out_path.exists())
        self.assertEqual(json.loads(out_path.read_text(encoding="utf-8")), payload)

        out_path.unlink()
        if out_dir.exists() and not any(out_dir.iterdir()):
            out_dir.rmdir()
