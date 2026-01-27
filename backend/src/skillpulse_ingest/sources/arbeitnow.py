from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
from dateutil import parser as dtparser
import requests

from .base import SourceAdapter
from ..models import IngestionQuery

class ArbeitnowAdapter(SourceAdapter):
    name = "arbeitnow"
    BASE = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        # API returns jobs in consistent format; may paginate.
        # We'll pull first N pages until max_results or no more pages.
        out: List[Dict[str, Any]] = []
        page = 1

        cutoff = datetime.now(timezone.utc).timestamp() - (q.days * 86400)

        while len(out) < q.max_results:
            params = {"page": page}
            r = requests.get(self.BASE, params=params, timeout=30)
            r.raise_for_status()
            payload = r.json()
            jobs = payload.get("data", []) or payload.get("jobs", []) or []

            if not jobs:
                break

            for j in jobs:
                # Many APIs use created_at or published_at. Handle best-effort.
                dt = j.get("created_at") or j.get("published_at") or j.get("date")
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

            # pagination
            links = payload.get("links", {})
            next_link = links.get("next") if isinstance(links, dict) else None
            if next_link:
                page += 1
                continue

            # fallback: if no pagination info, just stop after first page
            if page == 1:
                break
            page += 1

        return out
