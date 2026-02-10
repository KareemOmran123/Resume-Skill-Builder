import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from skillpulse_ingest.role_match import classify_level, classify_role, matches_query


class TestRoleMatch(unittest.TestCase):
    def test_classify_role_backend(self) -> None:
        title = "Backend Engineer"
        desc = "Work on APIs and services in Java."
        self.assertEqual(classify_role(title, desc), "backend")

    def test_classify_role_fullstack(self) -> None:
        title = "Full Stack Engineer"
        desc = "End-to-end ownership across frontend and backend."
        self.assertEqual(classify_role(title, desc), "fullstack")

    def test_classify_level_entry_tokens(self) -> None:
        title = "Junior Software Engineer"
        desc = "0-2 years experience"
        self.assertEqual(classify_level(title, desc), "entry")

    def test_classify_level_excludes_senior(self) -> None:
        title = "Senior Software Engineer"
        desc = "5+ years"
        self.assertEqual(classify_level(title, desc), "senior_excluded")

    def test_matches_query_filters(self) -> None:
        self.assertTrue(matches_query("backend", "entry", "backend", "entry"))
        self.assertFalse(matches_query("frontend", "entry", "backend", "entry"))
        self.assertFalse(matches_query("backend", "senior_excluded", "backend", "any"))
