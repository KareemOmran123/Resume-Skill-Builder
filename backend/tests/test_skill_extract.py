import unittest

from skillpulse_ingest.skill_extract import clean_text, extract_skill_counts


class TestSkillExtract(unittest.TestCase):
    def test_clean_text_strips_html_and_unescapes(self) -> None:
        text = "<p>Python &amp; SQL</p><ul><li>REST APIs</li></ul>"
        cleaned = clean_text(text)
        self.assertEqual(cleaned, "Python & SQL REST APIs")

    def test_extract_from_html_description(self) -> None:
        title = "Junior Backend Engineer"
        desc = "<div>We use <b>Python</b>, PostgreSQL, and RESTful web services.</div>"
        counts = extract_skill_counts(title, desc)
        self.assertGreaterEqual(counts.get("Python", 0), 1)
        self.assertGreaterEqual(counts.get("SQL / Databases", 0), 1)
        self.assertGreaterEqual(counts.get("REST APIs", 0), 1)

    def test_normalization_aliases(self) -> None:
        title = "React.js and NodeJS Engineer"
        desc = "Build APIs with node.js and reactjs"
        counts = extract_skill_counts(title, desc)
        self.assertIn("React", counts)
        self.assertIn("Node.js", counts)

    def test_soft_skills_not_counted(self) -> None:
        title = "Engineer"
        desc = "Great communication and collaboration required"
        counts = extract_skill_counts(title, desc)
        self.assertEqual(counts, {})
