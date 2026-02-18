from __future__ import annotations

import html
import re
from collections import Counter

from .skills_catalog import SKILL_PATTERNS

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Compile once at import time so extraction is fast for batch processing.
_COMPILED_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    skill: tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)
    for skill, patterns in SKILL_PATTERNS.items()
}


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    no_tags = _HTML_TAG_RE.sub(" ", text)
    unescaped = html.unescape(no_tags)
    return _WS_RE.sub(" ", unescaped).strip()


def extract_skill_counts(title: str | None, description: str | None) -> dict[str, int]:
    # Title and description are combined so signals in either field are counted.
    cleaned_title = clean_text(title)
    cleaned_desc = clean_text(description)
    text = f"{cleaned_title}\n{cleaned_desc}".strip()
    if not text:
        return {}

    counts: Counter[str] = Counter()

    # Skills are canonicalized by catalog key; pattern aliases map into one bucket.
    for skill, patterns in _COMPILED_PATTERNS.items():
        skill_count = 0
        for pattern in patterns:
            skill_count += len(pattern.findall(text))
        if skill_count > 0:
            counts[skill] = skill_count

    return dict(counts)
