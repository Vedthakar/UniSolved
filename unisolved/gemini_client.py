from __future__ import annotations

import json
import logging
from typing import Any

from unisolved.config import Settings
from unisolved.models import GroundedCitation, MentorMatch, ResourceMatch, StudentNeed
from unisolved.parsing import student_need_from_dict

try:
    from google import genai
except ImportError:  # pragma: no cover - exercised indirectly in fallback mode
    genai = None


logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = None
        if genai is not None and settings.live_mode_enabled:
            try:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except Exception:
                logger.exception("Failed to initialize Gemini client.")

    @property
    def available(self) -> bool:
        return self.client is not None

    def extract_student_need(self, question: str, campus: str) -> StudentNeed | None:
        if not self.available:
            return None

        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "course_codes": {"type": "array", "items": {"type": "string"}},
                "program": {"type": "string"},
                "issue_type": {"type": "string"},
                "language_preference": {"type": "string"},
                "campus": {"type": "string"},
                "needs_people": {"type": "boolean"},
                "needs_official_resources": {"type": "boolean"},
                "needs_food": {"type": "boolean"},
            },
            "required": [
                "intent",
                "course_codes",
                "program",
                "issue_type",
                "language_preference",
                "campus",
                "needs_people",
                "needs_official_resources",
                "needs_food",
            ],
            "additionalProperties": False,
        }

        prompt = (
            "Extract the student need from the message.\n"
            "Return JSON only.\n"
            f"Campus default: {campus}\n"
            "Use course codes when explicitly mentioned. Keep booleans conservative.\n"
            f"Message: {question}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": schema,
                    "temperature": 0.1,
                },
            )
            parsed = json.loads(response.text)
            return student_need_from_dict(parsed, raw_question=question)
        except Exception:
            logger.exception("Gemini student-need extraction failed.")
            return None

    def draft_answer(
        self,
        question: str,
        need: StudentNeed,
        mentor_matches: list[MentorMatch],
        resource_matches: list[ResourceMatch],
    ) -> tuple[str, list[GroundedCitation]]:
        if not self.available:
            raise RuntimeError("Gemini service is not configured.")

        mentor_summary = "\n".join(_summarize_mentor_match(match) for match in mentor_matches[:3])
        if not mentor_summary:
            mentor_summary = "- No mentor match selected."

        resource_summary = "\n".join(_summarize_resource_match(match) for match in resource_matches[:4])
        if not resource_summary:
            resource_summary = "- No local campus resource selected."

        prompt = f"""
You are UniSolved, a U of T student support assistant.
Answer the student's question in 2 short paragraphs max.
Use grounded public web information when it improves the answer.
Do not invent policies, contacts, or office details.
Mention that mentor and resource recommendations are curated below when relevant.
Treat mentor matches as private local records. Do not infer or restate phone numbers, emails, or other direct contact data.

Student question: {question}
Structured need:
- intent: {need.intent}
- issue_type: {need.issue_type}
- program: {need.program or "unknown"}
- course_codes: {", ".join(need.course_codes) or "none"}
- language_preference: {need.language_preference or "none"}
- campus: {need.campus}

Curated mentor matches:
{mentor_summary}

Curated campus/public resources:
{resource_summary}
""".strip()

        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0.2,
            },
        )
        return response.text.strip(), _extract_citations(response)


def _summarize_mentor_match(match: MentorMatch) -> str:
    return (
        f"- {match.mentor.name}: {match.why_match} "
        f"Program {match.mentor.program}, year {match.mentor.year}, availability {match.mentor.availability}."
    )


def _summarize_resource_match(match: ResourceMatch) -> str:
    return f"- {match.name}: {match.description} Source: {match.source_url}"


def _extract_citations(response: Any) -> list[GroundedCitation]:
    candidates = getattr(response, "candidates", None) or _dict_get(response, "candidates", [])
    if not candidates:
        return []

    candidate = candidates[0]
    metadata = getattr(candidate, "grounding_metadata", None) or _dict_get(candidate, "groundingMetadata")
    if metadata is None:
        metadata = _dict_get(candidate, "grounding_metadata")
    if metadata is None:
        return []

    queries = getattr(metadata, "web_search_queries", None) or _dict_get(metadata, "webSearchQueries", [])
    chunks = getattr(metadata, "grounding_chunks", None) or _dict_get(metadata, "groundingChunks", [])

    citations: list[GroundedCitation] = []
    for index, chunk in enumerate(chunks):
        web = getattr(chunk, "web", None) or _dict_get(chunk, "web", {})
        url = getattr(web, "uri", None) or _dict_get(web, "uri", "")
        title = getattr(web, "title", None) or _dict_get(web, "title", "")
        if url and title:
            citations.append(
                GroundedCitation(
                    title=title,
                    url=url,
                    query=queries[min(index, len(queries) - 1)] if queries else "",
                )
            )
    return _dedupe_citations(citations)


def _dict_get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return default


def _dedupe_citations(citations: list[GroundedCitation]) -> list[GroundedCitation]:
    seen: set[str] = set()
    unique_citations: list[GroundedCitation] = []
    for citation in citations:
        if citation.url in seen:
            continue
        seen.add(citation.url)
        unique_citations.append(citation)
    return unique_citations[:6]
