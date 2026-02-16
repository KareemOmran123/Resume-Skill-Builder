from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

from .base import SourceAdapter
from ..models import IngestionQuery


class TheirstackAdapter(SourceAdapter):
    name = "theirstack"
    BASE = "https://api.theirstack.com/v1"
    MAX_RETRIES = 3
    BACKOFF_SECONDS = 1.0

    def __init__(self, api_key: Optional[str] = None) -> None:
        raw_key = api_key if api_key is not None else os.getenv("THEIRSTACK_API_KEY")
        self.api_key = raw_key.strip() if isinstance(raw_key, str) else raw_key
        if not self.api_key:
            raise ValueError("THEIRSTACK_API_KEY is required for TheirstackAdapter")

    @staticmethod
    def _is_retryable(exc: requests.RequestException) -> bool:
        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return True
        if isinstance(exc, requests.HTTPError):
            resp = exc.response
            status = resp.status_code if resp is not None else None
            return status in {429, 500, 502, 503, 504}
        return False

    def _post_with_retry(self, payload: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
        last_exc: requests.RequestException | None = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    f"{self.BASE}/jobs/search",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt >= self.MAX_RETRIES or not self._is_retryable(exc):
                    raise
                time.sleep(self.BACKOFF_SECONDS * (2 ** attempt))
        assert last_exc is not None
        raise last_exc

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

            r = self._post_with_retry(payload, headers)
            data = r.json()
            jobs = data.get("data", []) or data.get("jobs", []) or []

            if not jobs:
                break

            out.extend(jobs)

            if len(jobs) < limit:
                break
            page += 1

        return out[: q.max_results]
