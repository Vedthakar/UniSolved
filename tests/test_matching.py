from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unisolved.config import Settings
from unisolved.database import ensure_database, fetch_mentors, fetch_resources, fetch_restaurants
from unisolved.matching import match_mentors, match_resources
from unisolved.parsing import parse_student_need


class MatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "demo.sqlite3"
        ensure_database(self.db_path)
        self.mentors = fetch_mentors(self.db_path)
        self.resources = fetch_resources(self.db_path)
        self.restaurants = fetch_restaurants(self.db_path)
        self.settings = Settings(gemini_api_key="", db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_course_language_issue_match_outranks_generic_program_match(self) -> None:
        need = parse_student_need(
            "I am struggling in CSC108 and want someone who speaks Hindi to help with assignments."
        )
        matches = match_mentors(need, self.mentors, limit=3)

        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].mentor.name, "Aarav Mehta")
        self.assertIn("speaks hindi", matches[0].why_match.lower())

    def test_students_without_course_codes_still_get_sensible_matches(self) -> None:
        need = parse_student_need("I am overwhelmed and need someone on campus to talk to about stress.")
        matches = match_mentors(need, self.mentors, limit=3)

        self.assertGreaterEqual(len(matches), 1)
        self.assertTrue(any(match.mentor.phone.startswith("416-555-") for match in matches))

    def test_phone_and_email_are_present_on_demo_matches(self) -> None:
        need = parse_student_need("I need help with MAT137 and exams.")
        matches = match_mentors(need, self.mentors, limit=3)

        self.assertGreaterEqual(len(matches), 1)
        self.assertTrue(matches[0].mentor.phone)
        self.assertTrue(matches[0].mentor.email)

    def test_academic_distress_prioritizes_official_resources(self) -> None:
        need = parse_student_need("I am falling behind in class and need official campus help.")
        matches = match_resources(need, self.resources, self.restaurants, limit=3)

        self.assertGreaterEqual(len(matches), 1)
        self.assertTrue(matches[0].is_official)
        self.assertIn(matches[0].category, {"academic_support", "writing_support", "student_support"})

    def test_restaurant_queries_return_food_options(self) -> None:
        need = parse_student_need("Where can I eat near campus after class?")
        matches = match_resources(need, self.resources, self.restaurants, limit=3)

        self.assertGreaterEqual(len(matches), 1)
        self.assertTrue(all(match.category == "restaurant" for match in matches))


if __name__ == "__main__":
    unittest.main()
