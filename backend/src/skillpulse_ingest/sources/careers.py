from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from .base import SourceAdapter
from ..models import IngestionQuery
from ..role_match import classify_level, classify_role, matches_query
from ..runtime_paths import DATA_DIR

DEFAULT_SOURCES_PATH = DATA_DIR / "career_sources.json"
USER_AGENT = "SkillPulseBot/0.1 (+local educational project; respectful curated career-page fetcher)"


@dataclass(frozen=True)
class CareerSource:
    company: str
    source_type: str
    enabled: bool = True
    board_token: str | None = None
    company_slug: str | None = None
    org_slug: str | None = None
    url: str | None = None
    respect_robots: bool = True


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _contains_location(value: str, q: IngestionQuery) -> bool:
    if not q.location:
        return True
    text = value.lower()
    location = q.location.lower()
    if location in {"united states", "us", "usa", "u.s.", "u.s.a.", "us-wide", "nationwide"}:
        if not text:
            return False
        us_phrases = (
            "united states",
            "remote us",
            "remote, us",
            "remote - us",
            "remote - united states",
            "san francisco",
            "sunnyvale",
            "san mateo",
            "mountain view",
            "palo alto",
            "seattle",
            "austin",
            "dallas",
            "new york",
            "raleigh",
            "durham",
            "boston",
            "denver",
            "washington",
            "ann arbor",
            "california",
            "texas",
            "washington",
            "new york",
            "north carolina",
            "massachusetts",
            "colorado",
            "michigan",
        )
        us_state_codes = ("ca", "tx", "wa", "ny", "nc", "ma", "co", "mi")
        non_us_terms = (
            "canada",
            "toronto",
            "vancouver",
            "united kingdom",
            "london",
            "india",
            "hyderabad",
            "tokyo",
            "singapore",
            "germany",
            "denmark",
            "aarhus",
            "france",
            "netherlands",
            "australia",
            "japan",
            "korea",
            "mexico",
            "mx",
            "poland",
            "warsaw",
        )
        has_us_phrase = any(term in text for term in us_phrases)
        has_us_state_code = any(re.search(rf"(^|[^a-z]){re.escape(code)}([^a-z]|$)", text) for code in us_state_codes)
        return (has_us_phrase or has_us_state_code) and not any(term in text for term in non_us_terms)
    aliases = {
        "dallas, tx": ["dallas", "dfw", "dallas-fort worth"],
        "san francisco bay area": [
            "san francisco",
            "bay area",
            "san jose",
            "oakland",
            "mountain view",
            "sunnyvale",
            "san mateo",
            "fremont",
            "palo alto",
            "redwood city",
            "menlo park",
            "mtvhq",
            "sfo",
        ],
        "new york, ny": ["new york", "new york city", "nyc"],
        "seattle, wa": ["seattle"],
        "austin, tx": ["austin"],
    }.get(location, [location])
    return any(alias in text for alias in aliases)


class CareersAdapter(SourceAdapter):
    name = "careers"
    REQUEST_DELAY_SECONDS = 0.0
    DEFAULT_MAX_WORKERS = 8

    def __init__(self, sources_path: str | None = None) -> None:
        configured_path = sources_path or os.getenv("CAREER_SOURCES_PATH") or str(DEFAULT_SOURCES_PATH)
        self.sources_path = Path(configured_path)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9"})
        self.max_workers = self._configured_max_workers()

    def _configured_max_workers(self) -> int:
        raw = os.getenv("CAREER_FETCH_WORKERS", str(self.DEFAULT_MAX_WORKERS))
        try:
            workers = int(raw)
        except ValueError:
            return self.DEFAULT_MAX_WORKERS
        return max(1, min(workers, 32))

    def _load_sources(self) -> list[CareerSource]:
        if not self.sources_path.exists():
            raise FileNotFoundError(
                f"Career sources file not found: {self.sources_path}. "
                "Copy backend/data/career_sources.example.json to backend/data/career_sources.json and enable sources."
            )

        raw_sources = json.loads(self.sources_path.read_text(encoding="utf-8"))
        if not isinstance(raw_sources, list):
            raise ValueError("Career sources file must contain a JSON array.")

        sources: list[CareerSource] = []
        for raw in raw_sources:
            if not isinstance(raw, dict):
                continue
            sources.append(
                CareerSource(
                    company=_coerce_text(raw.get("company")),
                    source_type=_coerce_text(raw.get("type")).lower(),
                    enabled=bool(raw.get("enabled", True)),
                    board_token=_coerce_text(raw.get("board_token")) or None,
                    company_slug=_coerce_text(raw.get("company_slug")) or None,
                    org_slug=_coerce_text(raw.get("org_slug")) or None,
                    url=_coerce_text(raw.get("url")) or None,
                    respect_robots=bool(raw.get("respect_robots", True)),
                )
            )
        return [source for source in sources if source.enabled]

    def _get_json(self, url: str, params: dict[str, object] | None = None) -> Any:
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _get_text(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except Exception:
            return False
        return parser.can_fetch(USER_AGENT, url)

    def _greenhouse(self, source: CareerSource, q: IngestionQuery) -> list[dict[str, Any]]:
        if not source.board_token:
            raise ValueError(f"Greenhouse source '{source.company}' requires board_token.")
        url = f"https://boards-api.greenhouse.io/v1/boards/{source.board_token}/jobs"
        data = self._get_json(url, params={"content": "true"})
        jobs = data.get("jobs", []) if isinstance(data, dict) else []

        out: list[dict[str, Any]] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            offices = job.get("offices") if isinstance(job.get("offices"), list) else []
            location = ", ".join(_coerce_text(office.get("name")) for office in offices if isinstance(office, dict))
            if not location:
                location = _coerce_text(job.get("location", {}).get("name") if isinstance(job.get("location"), dict) else "")
            if not _contains_location(location, q):
                continue
            out.append(
                {
                    "source_kind": "greenhouse",
                    "source_company": source.company,
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": source.company,
                    "location": location,
                    "url": job.get("absolute_url"),
                    "date_posted": job.get("updated_at"),
                    "description": job.get("content"),
                    "raw_source_json": job,
                }
            )
        return out

    def _lever(self, source: CareerSource, q: IngestionQuery) -> list[dict[str, Any]]:
        if not source.company_slug:
            raise ValueError(f"Lever source '{source.company}' requires company_slug.")
        url = f"https://api.lever.co/v0/postings/{source.company_slug}"
        data = self._get_json(url, params={"mode": "json"})
        jobs = data if isinstance(data, list) else []

        out: list[dict[str, Any]] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            categories = job.get("categories") if isinstance(job.get("categories"), dict) else {}
            location = _coerce_text(categories.get("location"))
            if not _contains_location(location, q):
                continue
            description = "\n".join(
                _strip_html(_coerce_text(section.get("content")))
                for section in job.get("lists", [])
                if isinstance(section, dict)
            )
            out.append(
                {
                    "source_kind": "lever",
                    "source_company": source.company,
                    "id": job.get("id"),
                    "title": job.get("text"),
                    "company": source.company,
                    "location": location,
                    "url": job.get("hostedUrl") or job.get("applyUrl"),
                    "date_posted": datetime.fromtimestamp(job.get("createdAt", 0) / 1000, timezone.utc).isoformat()
                    if isinstance(job.get("createdAt"), (int, float))
                    else None,
                    "description": description or job.get("descriptionPlain") or job.get("description"),
                    "raw_source_json": job,
                }
            )
        return out

    def _ashby(self, source: CareerSource, q: IngestionQuery) -> list[dict[str, Any]]:
        if not source.org_slug:
            raise ValueError(f"Ashby source '{source.company}' requires org_slug.")
        url = f"https://api.ashbyhq.com/posting-api/job-board/{source.org_slug}"
        data = self._get_json(url)
        jobs = data.get("jobs", []) if isinstance(data, dict) else []

        out: list[dict[str, Any]] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            location = _coerce_text(job.get("location"))
            if not _contains_location(location, q):
                continue
            out.append(
                {
                    "source_kind": "ashby",
                    "source_company": source.company,
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": source.company,
                    "location": location,
                    "url": job.get("jobUrl") or job.get("applyUrl"),
                    "date_posted": job.get("publishedAt"),
                    "description": job.get("descriptionHtml") or job.get("descriptionPlain"),
                    "raw_source_json": job,
                }
            )
        return out

    def _generic_html(self, source: CareerSource, q: IngestionQuery) -> list[dict[str, Any]]:
        if not source.url:
            raise ValueError(f"HTML source '{source.company}' requires url.")
        if source.respect_robots and not self._robots_allowed(source.url):
            print(f"Skipping {source.company}: robots.txt does not allow fetching {source.url}")
            return []

        html = self._get_text(source.url)
        links = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.I | re.S)
        out: list[dict[str, Any]] = []
        for href, label_html in links:
            title = _strip_html(label_html)
            if not title:
                continue
            title_l = title.lower()
            if not any(term in title_l for term in ("engineer", "developer", "software", "backend", "frontend")):
                continue
            url = urljoin(source.url, href)
            out.append(
                {
                    "source_kind": "generic_html",
                    "source_company": source.company,
                    "id": url,
                    "title": title,
                    "company": source.company,
                    "location": q.location,
                    "url": url,
                    "date_posted": None,
                    "description": title,
                    "raw_source_json": {"url": url, "title": title, "source_url": source.url},
                }
            )
        return out

    def _fetch_source(self, source: CareerSource, q: IngestionQuery) -> list[dict[str, Any]]:
        if source.source_type == "greenhouse":
            return self._greenhouse(source, q)
        if source.source_type == "lever":
            return self._lever(source, q)
        if source.source_type == "ashby":
            return self._ashby(source, q)
        if source.source_type == "generic_html":
            return self._generic_html(source, q)
        raise ValueError(f"Unsupported career source type '{source.source_type}' for {source.company}.")

    @staticmethod
    def _matches_query(raw: dict[str, Any], q: IngestionQuery) -> bool:
        title = _coerce_text(raw.get("title"))
        description = _strip_html(_coerce_text(raw.get("description")))
        if not CareersAdapter._is_software_title(title):
            return False
        role_bucket = classify_role(title, description)
        level_bucket = classify_level(title, description)
        return matches_query(role_bucket, level_bucket, q.role_bucket, q.level_bucket)

    @staticmethod
    def _is_software_title(title: str) -> bool:
        title_l = title.lower()
        include_terms = ("engineer", "developer", "software", "backend", "frontend", "full stack", "data scientist")
        exclude_terms = (
            "recruiter",
            "coordinator",
            "manager",
            "director",
            "assistant",
            "counsel",
            "account executive",
            "vp ",
            "sr ",
            "sr.",
            "senior",
            "staff",
            "principal",
            "lead",
            "data center",
            "facilities",
            "hardware technician",
        )
        return any(term in title_l for term in include_terms) and not any(term in title_l for term in exclude_terms)

    def fetch(self, q: IngestionQuery) -> List[Dict[str, Any]]:
        out: list[dict[str, Any]] = []
        sources = self._load_sources()
        if not sources:
            return out

        def fetch_one(index: int, source: CareerSource) -> tuple[int, CareerSource, list[dict[str, Any]]]:
            print(f"Career source fetch company={source.company} type={source.source_type}")
            try:
                jobs = self._fetch_source(source, q)
            except Exception as exc:
                print(f"Career source skipped company={source.company}: {exc}")
                return index, source, []
            matching_jobs = [job for job in jobs if self._matches_query(job, q)]
            print(f"Career source returned company={source.company} jobs={len(jobs)} matching={len(matching_jobs)}")
            if self.REQUEST_DELAY_SECONDS > 0:
                time.sleep(self.REQUEST_DELAY_SECONDS)
            return index, source, matching_jobs

        max_workers = min(self.max_workers, len(sources))
        results: list[tuple[int, CareerSource, list[dict[str, Any]]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_one, index, source) for index, source in enumerate(sources)]
            for future in as_completed(futures):
                results.append(future.result())

        for _, _, matching_jobs in sorted(results, key=lambda item: item[0]):
            if len(out) >= q.max_results:
                break
            remaining = q.max_results - len(out)
            out.extend(matching_jobs[:remaining])

        print(f"Career sources total matching={len(out)}")
        return out[: q.max_results]
