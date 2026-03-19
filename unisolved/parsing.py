from __future__ import annotations

import re

from unisolved.models import StudentNeed


COURSE_CODE_PATTERN = re.compile(r"\b[A-Z]{3}\d{3}[A-Z]?\b")

PROGRAM_KEYWORDS = {
    "Computer Science": ["computer science", "cs", "coding", "programming"],
    "Life Sciences": ["life sci", "life sciences", "biology", "bio", "chemistry", "chem"],
    "Mathematics": ["math", "mathematics", "calculus", "proof"],
    "Engineering Science": ["engsci", "engineering", "engineer"],
    "Rotman Commerce": ["commerce", "rotman", "business", "accounting", "finance"],
    "Psychology": ["psych", "psychology"],
    "Economics": ["economics", "econ"],
    "Political Science": ["political science", "politics", "policy"],
    "Nursing": ["nursing", "clinical"],
}

LANGUAGE_KEYWORDS = {
    "Hindi": ["hindi"],
    "Punjabi": ["punjabi"],
    "Gujarati": ["gujarati"],
    "Mandarin": ["mandarin", "chinese"],
    "Arabic": ["arabic"],
    "Spanish": ["spanish"],
    "French": ["french"],
    "Bengali": ["bengali"],
    "Urdu": ["urdu"],
    "Malayalam": ["malayalam"],
}

FOOD_KEYWORDS = [
    "restaurant",
    "food",
    "eat",
    "lunch",
    "dinner",
    "coffee",
    "snack",
    "meal",
]

PEOPLE_KEYWORDS = [
    "senior",
    "upper year",
    "mentor",
    "someone",
    "peer",
    "talk to",
    "student who",
]

OFFICIAL_RESOURCE_KEYWORDS = [
    "registrar",
    "office",
    "campus resource",
    "official",
    "advisor",
    "advising",
    "resource",
    "support",
]

WELLNESS_KEYWORDS = [
    "overwhelmed",
    "stress",
    "stressed",
    "anxious",
    "anxiety",
    "mental health",
    "burned out",
    "burnt out",
]

ACADEMIC_KEYWORDS = [
    "assignment",
    "exam",
    "midterm",
    "professor",
    "ta",
    "grades",
    "study",
    "understanding",
    "concepts",
    "class",
    "course",
]

ADMIN_KEYWORDS = [
    "enrol",
    "enroll",
    "deadline",
    "transcript",
    "tuition",
    "petition",
    "drop",
    "add",
]

CAREER_KEYWORDS = [
    "resume",
    "career",
    "internship",
    "interview",
    "networking",
]


def parse_student_need(
    question: str,
    campus_override: str = "",
    course_override: str = "",
    language_override: str = "",
) -> StudentNeed:
    lowered = question.lower()
    course_codes = sorted(set(code.upper() for code in COURSE_CODE_PATTERN.findall(question.upper())))
    if course_override.strip():
        course_codes.extend(
            code.upper() for code in COURSE_CODE_PATTERN.findall(course_override.upper()) if code.upper() not in course_codes
        )

    campus = _infer_campus(lowered)
    if campus_override.strip():
        campus = campus_override.strip()

    language_preference = _infer_language(lowered)
    if language_override.strip():
        language_preference = language_override.strip()

    program = _infer_program(lowered, course_codes)
    issue_type = _infer_issue_type(lowered)
    needs_food = any(keyword in lowered for keyword in FOOD_KEYWORDS)
    needs_people = any(keyword in lowered for keyword in PEOPLE_KEYWORDS)
    needs_official_resources = needs_food is False or any(
        keyword in lowered for keyword in OFFICIAL_RESOURCE_KEYWORDS + WELLNESS_KEYWORDS + ADMIN_KEYWORDS + ACADEMIC_KEYWORDS
    )

    if issue_type in {"academic", "wellness"}:
        needs_people = True
    if course_codes:
        needs_people = True

    intent = "general_support"
    if needs_food:
        intent = "food_discovery"
    elif issue_type == "wellness":
        intent = "wellness_support"
    elif issue_type == "administrative":
        intent = "admin_support"
    elif issue_type == "career":
        intent = "career_support"
    elif issue_type == "academic":
        intent = "academic_support"

    return StudentNeed(
        raw_question=question,
        intent=intent,
        course_codes=course_codes,
        program=program,
        issue_type=issue_type,
        language_preference=language_preference,
        campus=campus,
        needs_people=needs_people,
        needs_official_resources=needs_official_resources,
        needs_food=needs_food,
    )


def merge_student_need(base_need: StudentNeed, override_need: StudentNeed | None) -> StudentNeed:
    if override_need is None:
        return base_need

    merged_course_codes = sorted(set(base_need.course_codes + override_need.course_codes))
    return StudentNeed(
        raw_question=base_need.raw_question,
        intent=override_need.intent or base_need.intent,
        course_codes=merged_course_codes,
        program=override_need.program or base_need.program,
        issue_type=override_need.issue_type or base_need.issue_type,
        language_preference=override_need.language_preference or base_need.language_preference,
        campus=override_need.campus or base_need.campus,
        needs_people=override_need.needs_people or base_need.needs_people,
        needs_official_resources=override_need.needs_official_resources or base_need.needs_official_resources,
        needs_food=override_need.needs_food or base_need.needs_food,
    )


def student_need_from_dict(data: dict[str, object], raw_question: str) -> StudentNeed:
    return StudentNeed(
        raw_question=raw_question,
        intent=_safe_string(data.get("intent"), "general_support"),
        course_codes=[str(code).upper() for code in _safe_list(data.get("course_codes"))],
        program=_safe_string(data.get("program")),
        issue_type=_safe_string(data.get("issue_type"), "general"),
        language_preference=_safe_string(data.get("language_preference")),
        campus=_safe_string(data.get("campus"), "U of T St. George"),
        needs_people=_safe_bool(data.get("needs_people")),
        needs_official_resources=_safe_bool(data.get("needs_official_resources"), True),
        needs_food=_safe_bool(data.get("needs_food")),
    )


def _infer_campus(lowered: str) -> str:
    if "mississauga" in lowered or "utm" in lowered:
        return "U of T Mississauga"
    if "scarborough" in lowered or "utsc" in lowered:
        return "U of T Scarborough"
    return "U of T St. George"


def _infer_language(lowered: str) -> str:
    for language, keywords in LANGUAGE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return language
    return ""


def _infer_program(lowered: str, course_codes: list[str]) -> str:
    for program, keywords in PROGRAM_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return program

    if any(code.startswith("CSC") for code in course_codes):
        return "Computer Science"
    if any(code.startswith("MAT") for code in course_codes):
        return "Mathematics"
    if any(code.startswith("BIO") or code.startswith("CHM") for code in course_codes):
        return "Life Sciences"
    if any(code.startswith("ECO") or code.startswith("RSM") for code in course_codes):
        return "Rotman Commerce"
    if any(code.startswith("APS") or code.startswith("MIE") or code.startswith("CIV") for code in course_codes):
        return "Engineering Science"
    if any(code.startswith("PSY") for code in course_codes):
        return "Psychology"
    return ""


def _infer_issue_type(lowered: str) -> str:
    if any(keyword in lowered for keyword in FOOD_KEYWORDS):
        return "food"
    if any(keyword in lowered for keyword in WELLNESS_KEYWORDS):
        return "wellness"
    if any(keyword in lowered for keyword in CAREER_KEYWORDS):
        return "career"
    if any(keyword in lowered for keyword in ADMIN_KEYWORDS):
        return "administrative"
    if any(keyword in lowered for keyword in ACADEMIC_KEYWORDS) or COURSE_CODE_PATTERN.search(lowered.upper()):
        return "academic"
    return "general"


def _safe_string(value: object, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return default


def _safe_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _safe_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default
