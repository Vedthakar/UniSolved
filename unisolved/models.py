from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StudentNeed:
    raw_question: str
    intent: str = "general_support"
    course_codes: list[str] = field(default_factory=list)
    program: str = ""
    issue_type: str = "general"
    language_preference: str = ""
    campus: str = "U of T St. George"
    needs_people: bool = False
    needs_official_resources: bool = True
    needs_food: bool = False


@dataclass
class Mentor:
    name: str
    phone: str
    email: str
    program: str
    year: int
    languages: list[str]
    courses: list[str]
    help_topics: list[str]
    bio: str
    availability: str


@dataclass
class Resource:
    name: str
    category: str
    campus: str
    area: str
    description: str
    tags: list[str]
    source_url: str
    is_official: bool


@dataclass
class Restaurant:
    name: str
    category: str
    campus: str
    area: str
    description: str
    tags: list[str]
    source_url: str
    is_official: bool


@dataclass
class MentorMatch:
    mentor: Mentor
    score: int
    why_match: str


@dataclass
class ResourceMatch:
    name: str
    category: str
    campus: str
    area: str
    description: str
    source_url: str
    is_official: bool
    why_match: str
    score: int


@dataclass
class GroundedCitation:
    title: str
    url: str
    query: str = ""


@dataclass
class AssistantReply:
    answer: str
    mentor_matches: list[MentorMatch] = field(default_factory=list)
    resource_matches: list[ResourceMatch] = field(default_factory=list)
    citations: list[GroundedCitation] = field(default_factory=list)
    mode_label: str = "Demo mode"
    parsed_need: StudentNeed | None = None
