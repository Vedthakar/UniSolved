from __future__ import annotations

from unisolved.models import Mentor, MentorMatch, Resource, ResourceMatch, Restaurant, StudentNeed


def match_mentors(need: StudentNeed, mentors: list[Mentor], limit: int = 3) -> list[MentorMatch]:
    scored_matches: list[MentorMatch] = []
    for mentor in mentors:
        score = 0
        reasons: list[str] = []
        course_overlap = sorted(set(code.upper() for code in mentor.courses) & set(need.course_codes))
        if course_overlap:
            score += 70 + (10 * len(course_overlap))
            reasons.append(f"shares experience with {', '.join(course_overlap)}")

        if need.program and mentor.program.lower() == need.program.lower():
            score += 28
            reasons.append(f"is in {mentor.program}")

        if need.language_preference and any(
            language.lower() == need.language_preference.lower() for language in mentor.languages
        ):
            score += 24
            reasons.append(f"speaks {need.language_preference}")

        topic_overlap = _overlap(mentor.help_topics, _issue_topics(need.issue_type))
        if topic_overlap:
            score += 18 + (3 * len(topic_overlap))
            reasons.append(f"helps with {', '.join(topic_overlap[:2])}")

        if need.issue_type == "wellness" and any("wellness" in topic.lower() for topic in mentor.help_topics):
            score += 12

        score += max(mentor.year - 1, 0) * 2

        if need.needs_people is False and score < 35:
            continue

        if score > 0:
            scored_matches.append(
                MentorMatch(
                    mentor=mentor,
                    score=score,
                    why_match=_format_reasons(reasons, mentor),
                )
            )

    return sorted(scored_matches, key=lambda match: (-match.score, match.mentor.name))[:limit]


def match_resources(
    need: StudentNeed,
    resources: list[Resource],
    restaurants: list[Restaurant],
    limit: int = 4,
) -> list[ResourceMatch]:
    candidates: list[ResourceMatch] = []
    if need.needs_food:
        for restaurant in restaurants:
            score, why_match = _score_restaurant(need, restaurant)
            if score > 0:
                candidates.append(
                    ResourceMatch(
                        name=restaurant.name,
                        category=restaurant.category,
                        campus=restaurant.campus,
                        area=restaurant.area,
                        description=restaurant.description,
                        source_url=restaurant.source_url,
                        is_official=restaurant.is_official,
                        why_match=why_match,
                        score=score,
                    )
                )
    else:
        for resource in resources:
            score, why_match = _score_resource(need, resource)
            if score > 0:
                candidates.append(
                    ResourceMatch(
                        name=resource.name,
                        category=resource.category,
                        campus=resource.campus,
                        area=resource.area,
                        description=resource.description,
                        source_url=resource.source_url,
                        is_official=resource.is_official,
                        why_match=why_match,
                        score=score,
                    )
                )

        if need.issue_type in {"academic", "wellness", "administrative"}:
            candidates = sorted(
                candidates,
                key=lambda match: (-int(match.is_official), -match.score, match.name),
            )
            return candidates[:limit]

    return sorted(candidates, key=lambda match: (-match.score, match.name))[:limit]


def _score_resource(need: StudentNeed, resource: Resource) -> tuple[int, str]:
    score = 10
    reasons: list[str] = []
    if resource.campus == need.campus:
        score += 14
        reasons.append(f"located for {need.campus}")

    issue_topics = _issue_topics(need.issue_type)
    tag_overlap = _overlap(resource.tags, issue_topics + need.course_codes)
    if tag_overlap:
        score += 18 + (3 * len(tag_overlap))
        reasons.append(f"covers {', '.join(tag_overlap[:2])}")

    if need.needs_official_resources and resource.is_official:
        score += 25
        reasons.append("is an official U of T resource")

    if need.issue_type == "wellness" and resource.category == "wellness":
        score += 25
    if need.issue_type == "administrative" and resource.category == "administrative":
        score += 25
    if need.issue_type == "academic" and resource.category in {"academic_support", "writing_support"}:
        score += 22
    if need.issue_type == "career" and resource.category == "career":
        score += 25

    return score, _format_reasons(reasons, resource)


def _score_restaurant(need: StudentNeed, restaurant: Restaurant) -> tuple[int, str]:
    score = 12
    reasons: list[str] = ["is close to campus"]
    if restaurant.campus == need.campus:
        score += 18
    if "late" in need.raw_question.lower() and "late night" in " ".join(restaurant.tags).lower():
        score += 15
        reasons.append("fits a late meal after class")
    if any(keyword in need.raw_question.lower() for keyword in ["quick", "between class", "between classes"]):
        if any(tag in restaurant.tags for tag in ["quick meal", "takeout", "between classes"]):
            score += 15
            reasons.append("works for a fast stop between classes")
    return score, _format_reasons(reasons, restaurant)


def _issue_topics(issue_type: str) -> list[str]:
    lookup = {
        "academic": ["assignments", "study habits", "exam prep", "concept clarity", "problem sets", "writing"],
        "wellness": ["wellness check-ins", "stress management", "support"],
        "administrative": ["campus help", "advising", "support"],
        "career": ["career", "resume", "networking"],
        "food": ["food", "quick meal", "late night"],
        "general": ["support", "campus help"],
    }
    return lookup.get(issue_type, ["support"])


def _overlap(left: list[str], right: list[str]) -> list[str]:
    right_lower = {item.lower() for item in right}
    return [item for item in left if item.lower() in right_lower]


def _format_reasons(reasons: list[str], record: Mentor | Resource | Restaurant) -> str:
    if reasons:
        if len(reasons) == 1:
            return reasons[0].capitalize() + "."
        return ", ".join(reasons[:-1]).capitalize() + f", and {reasons[-1]}."
    if isinstance(record, Mentor):
        return f"{record.name} is a solid general support match."
    return f"{record.name} is a relevant option for this question."
