from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from .base import SourceAdapter
from ..models import IngestionQuery


class TheirstackAdapter(SourceAdapter):
    name = "theirstack"
    SEARCH_URL = "https://api.theirstack.com/v1/jobs/search"
    PAGE_LIMIT = 25
    MAX_RETRIES = 3
    BACKOFF_SECONDS = 1.0

    def __init__(self, api_key: Optional[str] = None) -> None:
        raw_key = api_key if api_key is not None else os.getenv("THEIRSTACK_API_KEY")
        self.api_key = raw_key.strip() if isinstance(raw_key, str) else raw_key
        if not self.api_key:
            raise ValueError("THEIRSTACK_API_KEY environment variable is required for TheirStack ingestion.")

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
                    self.SEARCH_URL,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                if not resp.ok:
                    print(f"TheirStack error status={resp.status_code}")
                    print(f"TheirStack error response={resp.text}")
                    print(f"TheirStack request payload={payload}")
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt >= self.MAX_RETRIES or not self._is_retryable(exc):
                    raise
                time.sleep(self.BACKOFF_SECONDS * (2 ** attempt))
        assert last_exc is not None
        raise last_exc

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _role_title_terms(role_bucket: str) -> list[str]:
        return {
            "backend": ["backend engineer", "back end engineer", "software engineer", "api engineer"],
            "frontend": ["frontend engineer", "front end engineer", "software engineer", "react developer", "ui engineer"],
            "fullstack": ["full stack engineer", "fullstack engineer", "software engineer", "web developer"],
            "any": ["software engineer", "software developer", "web developer"],
        }.get(role_bucket, ["software engineer", "software developer", "web developer"])

    @staticmethod
    def _location_terms(location: str) -> list[str]:
        normalized = location.strip()
        return {
            "Dallas, TX": ["Dallas", "Dallas-Fort Worth", "DFW"],
            "San Francisco Bay Area": ["San Francisco", "Bay Area", "San Jose", "Oakland"],
            "New York, NY": ["New York", "New York City", "NYC"],
            "Seattle, WA": ["Seattle"],
            "Austin, TX": ["Austin"],
        }.get(normalized, [normalized] if normalized else [])

    def build_payload(self, q: IngestionQuery, *, page: int, limit: int) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "page": page,
            "limit": limit,
            "job_country_code_or": ["US"],
            "posted_at_max_age_days": q.days,
            "job_title_or": self._role_title_terms(q.role_bucket),
            "job_location_pattern_or": self._location_terms(q.location),
            "include_total_results": False,
        }

        if q.level_bucket == "entry":
            payload["job_seniority_or"] = ["junior"]
            payload["job_title_not"] = ["senior", "sr", "lead", "staff", "principal", "manager", "director"]
            payload["job_description_contains_not"] = ["senior", "lead", "staff", "principal", "manager", "director"]
        elif q.level_bucket == "junior_mid":
            payload["job_seniority_or"] = ["junior", "mid_level"]

        return payload

    @staticmethod
    def _extract_jobs(data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected TheirStack response type: {type(data).__name__}")
        if "data" not in data:
            keys = ", ".join(sorted(str(k) for k in data.keys()))
            raise ValueError(f"Unexpected TheirStack response shape. Top-level keys: {keys}")

        jobs = data["data"]
        if not isinstance(jobs, list):
            raise ValueError(f"Unexpected TheirStack data payload type: {type(jobs).__name__}")

        return [job for job in jobs if isinstance(job, dict)]

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        page = 0
        headers = self._headers()

        while len(out) < q.max_results:
            remaining = q.max_results - len(out)
            limit = min(self.PAGE_LIMIT, remaining)
            payload = self.build_payload(q, page=page, limit=limit)

            print(f"TheirStack request page={page} limit={limit}")
            response = self._post_with_retry(payload, headers)
            jobs = self._extract_jobs(response.json())
            print(f"TheirStack returned jobs={len(jobs)}")

            if not jobs:
                break

            out.extend(jobs)
            print(f"TheirStack normalized raw jobs total={len(out)}")

            if len(jobs) < limit:
                break
            page += 1

        return out[: q.max_results]
