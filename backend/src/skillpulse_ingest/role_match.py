from __future__ import annotations

import re
from typing import Tuple

ENTRY_TOKENS = [
    "new grad", "graduate", "university grad", "early career",
    "entry level", "entry-level", "junior", "jr", "associate",
    " l1", " level 1", " engineer i", " engineer 1", " i ", " 1 "
]

EXCLUDE_SENIOR = ["senior", " sr", "lead", "staff", "principal", "architect", "manager", "director"]

YOE_PATTERNS_ENTRY = [
    re.compile(r"\b0\s*-\s*2\s+years?\b", re.I),
    re.compile(r"\b1\s*-\s*3\s+years?\b", re.I),
    re.compile(r"\b2\s*-\s*3\s+years?\b", re.I),
]

BACKEND_KW = [
    "backend", "back end", "server-side", "platform", "api", "services", "microservices",
    "cloud", "aws", "devops", "devsecops", "sre", "reliability",
    "java", "spring", "spring boot", "hibernate", "jpa", "sql", "postgres", "oracle",
]

FRONTEND_KW = [
    "frontend", "front end", "ui", "web", "client-side",
    "react", "typescript", "javascript", "html", "css", "angular", "next.js",
]

FULLSTACK_KW = [
    "full stack", "full-stack",
    "work across the stack", "both sides", "end-to-end", "end to end",
]

def _contains_any(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)

def classify_role(title: str, desc: str) -> str:
    text = f"{title}\n{desc}".lower()

    if _contains_any(text, FULLSTACK_KW):
        return "fullstack"

    be = sum(1 for k in BACKEND_KW if k in text)
    fe = sum(1 for k in FRONTEND_KW if k in text)

    # simple heuristic
    if be >= fe and be > 0:
        return "backend"
    if fe > 0:
        return "frontend"
    return "any"

def classify_level(title: str, desc: str) -> str:
    text = f"{title}\n{desc}".lower()

    if _contains_any(text, EXCLUDE_SENIOR):
        return "senior_excluded"

    if any(p.search(text) for p in YOE_PATTERNS_ENTRY):
        return "entry"

    if _contains_any(text, ENTRY_TOKENS):
        return "entry"

    return "any"

def matches_query(role_bucket: str, level_bucket: str, q_role: str, q_level: str) -> bool:
    if q_role != "any" and role_bucket != q_role:
        return False
    if q_level != "any" and level_bucket != q_level:
        return False
    if level_bucket == "senior_excluded":
        return False
    return True
