from __future__ import annotations

import logging

from unisolved.config import Settings
from unisolved.database import ensure_database, fetch_mentors, fetch_resources, fetch_restaurants
from unisolved.gemini_client import GeminiService
from unisolved.matching import match_mentors, match_resources
from unisolved.models import AssistantReply, StudentNeed
from unisolved.parsing import merge_student_need, parse_student_need


logger = logging.getLogger(__name__)


class ChatOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        ensure_database(settings.db_path)
        self.gemini = GeminiService(settings)

    def respond(
        self,
        question: str,
        selected_campus: str = "",
        sidebar_course: str = "",
        sidebar_language: str = "",
    ) -> AssistantReply:
        base_need = parse_student_need(
            question=question,
            campus_override=selected_campus,
            course_override=sidebar_course,
            language_override=sidebar_language,
        )
        refined_need = self.gemini.extract_student_need(question, base_need.campus)
        need = merge_student_need(base_need, refined_need)

        mentors = fetch_mentors(self.settings.db_path)
        resources = fetch_resources(self.settings.db_path)
        restaurants = fetch_restaurants(self.settings.db_path)

        mentor_matches = match_mentors(need, mentors)
        resource_matches = match_resources(need, resources, restaurants)

        if self.gemini.available:
            try:
                answer, citations = self.gemini.draft_answer(question, need, mentor_matches, resource_matches)
                return AssistantReply(
                    answer=answer,
                    mentor_matches=mentor_matches,
                    resource_matches=resource_matches,
                    citations=citations,
                    mode_label="Live Gemini mode",
                    parsed_need=need,
                )
            except Exception:
                logger.exception("Falling back to demo mode after Gemini answer generation failed.")

        return AssistantReply(
            answer=_build_demo_answer(need, mentor_matches, resource_matches),
            mentor_matches=mentor_matches,
            resource_matches=resource_matches,
            citations=[],
            mode_label="Demo mode",
            parsed_need=need,
        )


def _build_demo_answer(
    need: StudentNeed,
    mentor_matches,
    resource_matches,
) -> str:
    if need.needs_food:
        opening = "I can help with nearby food options around U of T."
    elif need.issue_type == "wellness":
        opening = (
            "You sound overwhelmed, so I would start with one official support option today and one peer connection "
            "so you are not handling this alone."
        )
    elif need.issue_type == "academic":
        opening = (
            "This looks like an academic support question, so I pulled upper-year mentors plus official U of T help "
            "that fits your course or study issue."
        )
    elif need.issue_type == "administrative":
        opening = "This sounds administrative, so I prioritized official U of T resources and a student support path."
    else:
        opening = "I pulled the strongest support options from the local demo data for your situation."

    detail_lines: list[str] = []
    if mentor_matches:
        top_match = mentor_matches[0]
        detail_lines.append(
            f"Top mentor match: {top_match.mentor.name} ({top_match.mentor.program}, year {top_match.mentor.year}) "
            f"because they {top_match.why_match[:-1].lower()}."
        )
    if resource_matches:
        top_resource = resource_matches[0]
        detail_lines.append(
            f"Best resource right now: {top_resource.name}, which {top_resource.why_match[:-1].lower()}."
        )
    else:
        detail_lines.append("The seeded demo data did not find a more specific campus resource, so I kept the reply general.")

    if need.needs_food:
        close = "I also listed a few nearby places with quick context and public links below."
    else:
        close = "I listed curated matches below so you can act on this immediately."

    return " ".join([opening] + detail_lines + [close])
