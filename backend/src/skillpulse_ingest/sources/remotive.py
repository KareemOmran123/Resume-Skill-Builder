from __future__ import annotations

import time
from typing import Any, Dict, List
from datetime import datetime, timezone
from dateutil import parser as dtparser
import requests

from .base import SourceAdapter
from ..models import IngestionQuery

class RemotiveAdapter(SourceAdapter):
    name = "remotive"
    BASE = "https://remotive.com/api/remote-jobs"
    MAX_RETRIES = 3
    BACKOFF_SECONDS = 1.0

    @staticmethod
    def _is_retryable(exc: requests.RequestException) -> bool:
        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return True
        if isinstance(exc, requests.HTTPError):
            resp = exc.response
            status = resp.status_code if resp is not None else None
            return status in {429, 500, 502, 503, 504}
        return False

    def _get_with_retry(self, params: dict) -> requests.Response:
        last_exc: requests.RequestException | None = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(self.BASE, params=params, timeout=30)
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
        # Remotive supports some filtering like "search" and "category"
        # We'll use role_bucket as a weak search term.
        params = {}
        if q.role_bucket != "any":
            params["search"] = q.role_bucket

        r = self._get_with_retry(params)
        data = r.json()
        jobs = data.get("jobs", [])

        # best-effort time window filter
        cutoff = datetime.now(timezone.utc).timestamp() - (q.days * 86400)
        out: List[Dict[str, Any]] = []
        for j in jobs:
            # Remotive uses publication_date
            dt = j.get("publication_date")
            keep = True
            if dt:
                try:
                    ts = dtparser.parse(dt).timestamp()
                    keep = ts >= cutoff
                except Exception:
                    keep = True
            if keep:
                out.append(j)
            if len(out) >= q.max_results:
                break

        return out
