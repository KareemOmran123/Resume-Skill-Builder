import unittest

from skillpulse_ingest.role_match import classify_level, classify_role, is_software_job_title, matches_query


class TestRoleMatch(unittest.TestCase):
    def test_classify_role_backend(self) -> None:
        title = "Backend Engineer"
        desc = "Work on APIs and services in Java."
        self.assertEqual(classify_role(title, desc), "backend")

    def test_classify_role_does_not_match_api_inside_words(self) -> None:
        title = "Candidate Experience Coordinator"
        desc = "Partner with talent acquisition teams and schedule interviews."
        self.assertEqual(classify_role(title, desc), "any")

    def test_classify_role_fullstack(self) -> None:
        title = "Full Stack Engineer"
        desc = "End-to-end ownership across frontend and backend."
        self.assertEqual(classify_role(title, desc), "fullstack")

    def test_classify_level_entry_tokens(self) -> None:
        title = "Junior Software Engineer"
        desc = "0-2 years experience"
        self.assertEqual(classify_level(title, desc), "entry")

    def test_classify_level_intern_tokens(self) -> None:
        title = "Software Engineer, Intern"
        desc = "Campus recruiting role"
        self.assertEqual(classify_level(title, desc), "entry")

    def test_classify_level_does_not_match_single_letters(self) -> None:
        title = "Candidate Experience Coordinator"
        desc = "Coordinate interviews and offer letters."
        self.assertEqual(classify_level(title, desc), "any")

    def test_classify_level_excludes_senior(self) -> None:
        title = "Senior Software Engineer"
        desc = "5+ years"
        self.assertEqual(classify_level(title, desc), "senior_excluded")

    def test_matches_query_filters(self) -> None:
        self.assertTrue(matches_query("backend", "entry", "backend", "entry"))
        self.assertFalse(matches_query("frontend", "entry", "backend", "entry"))
        self.assertFalse(matches_query("backend", "senior_excluded", "backend", "any"))

    def test_software_job_title_filter_keeps_software_roles(self) -> None:
        self.assertTrue(is_software_job_title("Front-End Engineer II"))
        self.assertTrue(is_software_job_title("Junior Software Developer"))
        self.assertTrue(is_software_job_title("Machine Learning Engineer"))

    def test_software_job_title_filter_rejects_description_noise(self) -> None:
        self.assertFalse(is_software_job_title("AI-Driven OSINT Analyst"))
        self.assertFalse(is_software_job_title("Logistics & Warehouse Coordinator"))
        self.assertFalse(is_software_job_title("Controls Engineer"))
