from __future__ import annotations

import os
import math
from typing import Any, Dict, List

from .base import SourceAdapter
from ..models import IngestionQuery


DEFAULT_SITES = ("indeed", "linkedin", "zip_recruiter", "google")


class JobSpyAdapter(SourceAdapter):
    name = "jobspy"

    def __init__(self, sites: list[str] | None = None) -> None:
        self.sites = sites or self._configured_sites()

    @staticmethod
    def _configured_sites() -> list[str]:
        raw = os.getenv("JOBSPY_SITES")
        if not raw:
            return list(DEFAULT_SITES)
        sites = [site.strip() for site in raw.split(",") if site.strip()]
        return sites or list(DEFAULT_SITES)

    @staticmethod
    def _configured_list(name: str) -> list[str] | None:
        raw = os.getenv(name)
        if not raw:
            return None
        values = [value.strip() for value in raw.split(",") if value.strip()]
        return values or None

    @staticmethod
    def _configured_bool(name: str) -> bool | None:
        raw = os.getenv(name)
        if raw is None:
            return None
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _configured_int(name: str) -> int | None:
        raw = os.getenv(name)
        if raw is None or not raw.strip():
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    @staticmethod
    def _search_term(q: IngestionQuery) -> str:
        override = os.getenv("JOBSPY_SEARCH_TERM")
        if override:
            return override
        role_terms = {
            "backend": '("backend engineer" OR "back end engineer" OR "software engineer")',
            "frontend": '("frontend engineer" OR "front end engineer" OR "software engineer")',
            "fullstack": '("full stack engineer" OR "fullstack engineer" OR "software engineer")',
            "any": '("software engineer" OR "software developer" OR "frontend engineer" OR "backend engineer" OR "full stack engineer")',
        }
        level_terms = {
            "entry": '("entry level" OR junior OR "new grad" OR graduate OR internship)',
            "junior_mid": '(junior OR "mid level" OR "mid-level")',
            "any": "",
        }
        exclusions = "-senior -staff -principal -manager -director -logistics -warehouse -fleet -controls"
        return " ".join(
            part
            for part in (
                role_terms.get(q.role_bucket, '"software engineer"'),
                level_terms.get(q.level_bucket, ""),
                exclusions,
            )
            if part
        )

    @staticmethod
    def _google_search_term(q: IngestionQuery) -> str:
        override = os.getenv("JOBSPY_GOOGLE_SEARCH_TERM")
        if override:
            return override
        search = JobSpyAdapter._search_term(q)
        location = f" in {q.location}" if q.location else ""
        return f"{search} jobs{location} since {q.days} days ago"

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, float):
            return value
        if isinstance(value, dict):
            return {str(k): JobSpyAdapter._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [JobSpyAdapter._json_safe(item) for item in value]
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except (TypeError, ValueError):
                pass
        if hasattr(value, "item"):
            try:
                return JobSpyAdapter._json_safe(value.item())
            except (TypeError, ValueError):
                pass
        return str(value)

    @staticmethod
    def _to_records(jobs: Any) -> list[dict[str, Any]]:
        if hasattr(jobs, "to_dict"):
            records = jobs.to_dict(orient="records")
        elif isinstance(jobs, list):
            records = jobs
        else:
            records = []

        return [JobSpyAdapter._json_safe(record) for record in records if isinstance(record, dict)]

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        try:
            from jobspy import scrape_jobs
        except ImportError as exc:
            raise RuntimeError(
                "JobSpy is not installed. Install backend dependencies with "
                "`python -m pip install -e backend` or `python -m pip install -r backend/requirements.txt`."
            ) from exc

        verbose = self._configured_int("JOBSPY_VERBOSE")
        kwargs: dict[str, Any] = {
            "site_name": self.sites,
            "search_term": self._search_term(q),
            "google_search_term": self._google_search_term(q),
            "location": q.location,
            "results_wanted": q.max_results,
            "hours_old": q.days * 24,
            "country_indeed": os.getenv("JOBSPY_COUNTRY_INDEED", "USA"),
            "verbose": verbose if verbose is not None else 1,
        }

        optional_values = {
            "distance": self._configured_int("JOBSPY_DISTANCE"),
            "job_type": os.getenv("JOBSPY_JOB_TYPE"),
            "proxies": self._configured_list("JOBSPY_PROXIES"),
            "is_remote": self._configured_bool("JOBSPY_REMOTE"),
            "easy_apply": self._configured_bool("JOBSPY_EASY_APPLY"),
            "user_agent": os.getenv("JOBSPY_USER_AGENT"),
            "description_format": os.getenv("JOBSPY_DESCRIPTION_FORMAT"),
            "linkedin_fetch_description": self._configured_bool("JOBSPY_LINKEDIN_FETCH_DESCRIPTION"),
            "enforce_annual_salary": self._configured_bool("JOBSPY_ENFORCE_ANNUAL_SALARY"),
            "offset": self._configured_int("JOBSPY_OFFSET"),
        }
        kwargs.update({key: value for key, value in optional_values.items() if value not in (None, "")})

        jobs = scrape_jobs(**kwargs)

        return self._to_records(jobs)[: q.max_results]
