from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
LOG_DIR = BACKEND_ROOT / "logs"

DEFAULT_DB_PATH = DATA_DIR / "skillpulse.db"
DEFAULT_LOG_PATH = LOG_DIR / "ingest.log"
DEFAULT_SAMPLE_PATH = LOG_DIR / "skills_sample.json"


def ensure_parent_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
