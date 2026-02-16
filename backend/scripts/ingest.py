from __future__ import annotations

import argparse
import logging
from pathlib import Path

from skillpulse_ingest.models import IngestionQuery
from skillpulse_ingest.storage_sqlite import SQLiteStore
from skillpulse_ingest.pipeline import run_pipeline, get_source, SOURCES

def setup_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("skillpulse_ingest")
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(log_path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", default="Dallas, TX")
    ap.add_argument("--role", choices=["any", "frontend", "backend", "fullstack"], default="any")
    ap.add_argument("--level", choices=["any", "entry", "junior_mid"], default="any")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max-results", type=int, default=250)
    ap.add_argument("--source", choices=sorted(SOURCES.keys()), default=None)
    ap.add_argument("--db", default=str(Path("data") / "skillpulse.db"))
    ap.add_argument("--log", default=str(Path("logs") / "ingest.log"))
    args = ap.parse_args()

    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    logger = setup_logger(args.log)
    store = SQLiteStore(args.db)

    q = IngestionQuery(
        location=args.location,
        role_bucket=args.role,
        level_bucket=args.level,
        days=args.days,
        max_results=args.max_results,
    )

    adapters = [get_source(args.source)]
    run_pipeline(q, adapters, store, logger)

    store.close()

if __name__ == "__main__":
    main()
