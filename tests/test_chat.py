from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unisolved.chat import ChatOrchestrator
from unisolved.config import Settings
from unisolved.database import ensure_database, fetch_mentors, fetch_resources, fetch_restaurants
from unisolved.gemini_client import GeminiService
from unisolved.matching import match_mentors, match_resources
from unisolved.parsing import parse_student_need


class ChatFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "demo.sqlite3"
        self.settings = Settings(gemini_api_key="", db_path=self.db_path)
        self.orchestrator = ChatOrchestrator(self.settings)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_csc108_prompt_returns_mentor_and_resources(self) -> None:
        reply = self.orchestrator.respond(
            "I'm struggling in CSC108 and want someone who speaks Hindi.",
            selected_campus="U of T St. George",
        )

        self.assertEqual(reply.mode_label, "Demo mode")
        self.assertGreaterEqual(len(reply.mentor_matches), 1)
        self.assertEqual(reply.mentor_matches[0].mentor.name, "Aarav Mehta")
        self.assertTrue(reply.mentor_matches[0].mentor.phone.startswith("416-555-"))
        self.assertGreaterEqual(len(reply.resource_matches), 1)

    def test_food_prompt_returns_restaurants(self) -> None:
        reply = self.orchestrator.respond("Where can I eat near campus after class?")

        self.assertEqual(reply.mode_label, "Demo mode")
        self.assertGreaterEqual(len(reply.resource_matches), 1)
        self.assertTrue(all(match.category == "restaurant" for match in reply.resource_matches))

    def test_overwhelmed_prompt_returns_support_resources(self) -> None:
        reply = self.orchestrator.respond("I'm overwhelmed and don't know who to talk to.")

        self.assertEqual(reply.mode_label, "Demo mode")
        self.assertGreaterEqual(len(reply.resource_matches), 1)
        self.assertTrue(any(match.category == "wellness" for match in reply.resource_matches))

    def test_missing_key_gracefully_stays_in_demo_mode(self) -> None:
        reply = self.orchestrator.respond("How do I get help with assignments?")

        self.assertEqual(reply.mode_label, "Demo mode")
        self.assertEqual(reply.citations, [])

    def test_live_prompt_excludes_mentor_contact_details(self) -> None:
        ensure_database(self.db_path)
        mentors = fetch_mentors(self.db_path)
        resources = fetch_resources(self.db_path)
        restaurants = fetch_restaurants(self.db_path)
        need = parse_student_need("I'm struggling in CSC108 and want someone who speaks Hindi.")
        mentor_matches = match_mentors(need, mentors)
        resource_matches = match_resources(need, resources, restaurants)

        service = GeminiService(Settings(gemini_api_key="demo-key", db_path=self.db_path))
        service.client = _CapturingClient()

        service.draft_answer(
            question=need.raw_question,
            need=need,
            mentor_matches=mentor_matches,
            resource_matches=resource_matches,
        )

        captured_prompt = service.client.last_prompt
        self.assertIsNotNone(captured_prompt)
        self.assertNotIn(mentor_matches[0].mentor.phone, captured_prompt)
        self.assertNotIn(mentor_matches[0].mentor.email, captured_prompt)


class _CapturingClient:
    def __init__(self) -> None:
        self.last_prompt = None
        self.models = _CapturingModels(self)


class _CapturingModels:
    def __init__(self, parent: _CapturingClient) -> None:
        self.parent = parent

    def generate_content(self, *, model: str, contents: str, config: dict) -> "_Response":
        self.parent.last_prompt = contents
        return _Response()


class _Response:
    text = "stubbed answer"
    candidates: list = []


if __name__ == "__main__":
    unittest.main()
