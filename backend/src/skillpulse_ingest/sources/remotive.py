from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
from dateutil import parser as dtparser
import requests

from .base import SourceAdapter
from ..models import IngestionQuery

class RemotiveAdapter(SourceAdapter):
    name = "remotive"
    BASE = "https://remotive.com/api/remote-jobs"

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        # Remotive supports some filtering like "search" and "category"
        # We'll use role_bucket as a weak search term.
        params = {}
        if q.role_bucket != "any":
            params["search"] = q.role_bucket

        r = requests.get(self.BASE, params=params, timeout=30)
        r.raise_for_status()
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
