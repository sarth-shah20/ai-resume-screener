from pathlib import Path

import pytest

from src.models.schemas import ExtractedJob, RequirementMatch
from src.services.explain_service import contrast, is_grounded, next_band_target, score_breakdown, shortest_path
from src.services.scoring_service import calculate_scores

JOB = ExtractedJob.model_validate(
    {
        "title": "Backend Engineer",
        "requirements": [
            {"id": "r1", "category": "must_have_skill", "description": "Python", "weight": 2},
            {"id": "r2", "category": "must_have_skill", "description": "AWS"},
            {"id": "r3", "category": "experience", "description": "3+ years backend"},
            {"id": "r4", "category": "nice_to_have_skill", "description": "Kubernetes"},
            {"id": "r5", "category": "education", "description": "CS degree"},
        ],
    }
)
RESUME = (Path(__file__).resolve().parents[2] / "sample_data/resumes/keyword_heavy_weak_evidence.txt").read_text(encoding="utf-8")


def _matches(*statuses: str) -> list[RequirementMatch]:
    return [
        RequirementMatch(requirement_id=f"r{index}", status=status, confidence="medium", evidence="quote", explanation="why")
        for index, status in enumerate(statuses, start=1)
    ]


def test_breakdown_points_sum_to_the_scores():
    matches = _matches("demonstrated", "claimed", "partial", "unproven", "missing")
    verified, potential, _ = calculate_scores(JOB.requirements, matches)
    breakdown = score_breakdown(JOB.requirements, matches)
    assert round(sum(item.verified_points for item in breakdown)) == verified
    assert round(sum(item.potential_points for item in breakdown)) == potential
    assert sum(item.max_points for item in breakdown) == pytest.approx(100)
    assert all(item.lost_points >= 0 and item.uplift_points >= 0 for item in breakdown)


def test_shortest_path_reaches_target_with_fewest_changes():
    matches = _matches("demonstrated", "claimed", "unproven", "unproven", "unproven")
    assert calculate_scores(JOB.requirements, matches)[0] == 30
    steps = shortest_path(JOB.requirements, matches, 50)
    # Experience is the single largest gap (+28), so one change is enough.
    assert [step.requirement_id for step in steps] == ["r3"]
    assert steps[-1].score_after >= 50
    # The two largest gaps only reach 74, so a third change is required.
    to_strong = shortest_path(JOB.requirements, matches, 75)
    assert [step.requirement_id for step in to_strong] == ["r3", "r4", "r2"]
    assert [step.score_after for step in to_strong] == [57, 74, 89]


def test_shortest_path_is_empty_when_target_already_met():
    matches = _matches(*["demonstrated"] * 5)
    assert shortest_path(JOB.requirements, matches, 75) == []
    assert next_band_target(100) is None
    assert next_band_target(30) == ("moderate_fit", 50)
    assert next_band_target(60) == ("strong_fit", 75)


def test_contrast_orders_requirements_by_point_gap():
    strong = score_breakdown(JOB.requirements, _matches("demonstrated", "demonstrated", "demonstrated", "unproven", "unproven"))
    weak = score_breakdown(JOB.requirements, _matches("demonstrated", "claimed", "unproven", "unproven", "unproven"))
    differences = contrast(strong, weak)
    assert [first.requirement_id for first, _, _ in differences] == ["r3", "r2"]
    assert all(delta > 0 for _, _, delta in differences)


def test_grounding_accepts_reflowed_and_recased_quotes():
    assert is_grounded("attended internal workshops covering python,  AWS, and Kubernetes basics", RESUME)
    assert is_grounded("Results-driven engineer passionate about Python, AWS, Kubernetes, Docker, PostgreSQL", RESUME)
    assert is_grounded("Supported employee laptops ... and network connectivity issues", RESUME)


def test_grounding_rejects_fabricated_quotes():
    assert not is_grounded("Designed and deployed Kubernetes clusters serving 2M requests per day on AWS", RESUME)
    assert not is_grounded("Built Python REST APIs backed by PostgreSQL for five years", RESUME)
    assert not is_grounded("", RESUME)
