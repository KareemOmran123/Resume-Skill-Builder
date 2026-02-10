from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional, Dict
import hashlib
import json


@dataclass(frozen=True)
class IngestionQuery:
    location: str                 # e.g., "Dallas, TX" (may be best-effort depending on source)
    role_bucket: str              # "frontend" | "backend" | "fullstack" | "any"
    level_bucket: str             # "entry" | "junior_mid" | "any"
    days: int = 30                # time window
    max_results: int = 250        # cap per source to avoid runaway


@dataclass
class JobPosting:
    id: str
    source: str
    url: str
    title: str
    company: str
    location: Optional[str]
    date_posted: Optional[str]    # ISO8601 string, or None if not available
    retrieved_at: str             # ISO8601
    role_bucket: str
    level_bucket: str
    description_raw: str
    raw: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def make_id(source: str, url: str) -> str:
        h = hashlib.sha256(f"{source}:{url}".encode("utf-8")).hexdigest()
        return h[:32]
