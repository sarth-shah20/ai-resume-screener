"""Deterministic candidate scoring, computed in application code.

Per CLAUDE.md's architecture boundary, the LLM never produces the final
numeric score -- it classifies each requirement match and Python applies
the declared weights. This module implements plan.md #5's formula for real
(not a mock): it belongs in src/services/scoring_service.py once that
backend stream exists, and can move there unchanged -- it lives here for
now only because that file isn't built yet and isn't this stream's to
create.
"""

from __future__ import annotations

from typing import Any

MATCH_FACTOR: dict[str, float] = {
    "matched": 1.0,
    "partial": 0.5,
    "missing": 0.0,
    "unclear": 0.0,
}

REQUIREMENT_CATEGORIES = [
    "must_have_skills",
    "nice_to_have_skills",
    "experience_requirements",
    "education_requirements",
    "domain_requirements",
]


def score_candidate(
    matches: list[dict[str, Any]], requirements: dict[str, Any]
) -> dict[str, Any]:
    """Return {overall_score, category_scores} from requirement matches.

    Each category's requirement weights are expected to already sum to
    that category's overall percentage contribution (see
    app/services/fixtures.py's MOCK_EXTRACTED_REQUIREMENTS, where
    must-have weights sum to 40, matching plan.md #5's 40% weighting), so
    overall_score is simply the sum of weight * match_factor across every
    requirement, naturally bounded to [0, 100].
    """
    weight_lookup: dict[tuple[str, str], float] = {
        (category, item["name"]): item["weight"]
        for category in REQUIREMENT_CATEGORIES
        for item in requirements.get(category, [])
    }
    category_totals = {
        category: sum(item["weight"] for item in requirements.get(category, []))
        for category in REQUIREMENT_CATEGORIES
    }
    category_earned = {category: 0.0 for category in REQUIREMENT_CATEGORIES}

    overall_earned = 0.0
    for match in matches:
        key = (match["requirement_type"], match["requirement"])
        weight = weight_lookup.get(key, 0.0)
        factor = MATCH_FACTOR.get(match["status"], 0.0)
        contribution = weight * factor
        overall_earned += contribution
        category_earned[match["requirement_type"]] = (
            category_earned.get(match["requirement_type"], 0.0) + contribution
        )

    category_scores = {
        category: round((category_earned[category] / category_totals[category]) * 100)
        if category_totals[category]
        else 0
        for category in REQUIREMENT_CATEGORIES
    }

    overall_score = max(0, min(100, round(overall_earned)))
    return {"overall_score": overall_score, "category_scores": category_scores}


def recommendation_for(overall_score: int) -> tuple[str, str]:
    """Return (recommendation_text, confidence_label) for a score.

    Thresholds are simple, declared business rules -- not a model output --
    and are advisory only; the disclaimer banner and human review step
    remain authoritative per CLAUDE.md's responsible-AI requirements.
    """
    if overall_score >= 75:
        return "Strong fit -- recommend advancing to interview.", "High"
    if overall_score >= 40:
        return "Potential fit -- some gaps worth exploring in interview.", "Medium"
    return "Significant gaps against the stated requirements.", "Low"
