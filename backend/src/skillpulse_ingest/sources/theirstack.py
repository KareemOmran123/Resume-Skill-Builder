from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import requests

from .base import SourceAdapter
from ..models import IngestionQuery


class TheirstackAdapter(SourceAdapter):
    name = "theirstack"
    BASE = "https://api.theirstack.com/v1"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("THEIRSTACK_API_KEY")
        if not self.api_key:
            raise ValueError("THEIRSTACK_API_KEY is required for TheirstackAdapter")

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        page = 0

        headers = {"Authorization": f"Bearer {self.api_key}"}

        location_pattern = None
        if q.location:
            # TheirStack expects regex patterns for location filters.
            location_pattern = re.escape(q.location)

        seniority_or = None
        if q.level_bucket == "entry":
            seniority_or = ["intern", "entry", "junior"]
        elif q.level_bucket == "junior_mid":
            seniority_or = ["junior", "mid_level"]

        while len(out) < q.max_results:
            remaining = q.max_results - len(out)
            limit = min(50, remaining)

            payload: Dict[str, Any] = {
                "page": page,
                "limit": limit,
                "posted_at_max_age_days": q.days,
            }

            if q.role_bucket != "any":
                payload["job_title_or"] = [q.role_bucket]
            if seniority_or:
                payload["job_seniority_or"] = seniority_or
            if location_pattern:
                payload["job_location_pattern_or"] = [location_pattern]

            r = requests.post(
                f"{self.BASE}/jobs/search",
                json=payload,
                headers=headers,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            jobs = data.get("data", []) or data.get("jobs", []) or []

            if not jobs:
                break

            out.extend(jobs)

            if len(jobs) < limit:
                break
            page += 1

        return out[: q.max_results]
