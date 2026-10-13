from collections import defaultdict
from src.models.schemas import EvidenceStatus, JobRequirement, RequirementCategory, RequirementMatch
CATEGORY_WEIGHTS = {RequirementCategory.MUST_HAVE_SKILL: 40, RequirementCategory.EXPERIENCE: 25, RequirementCategory.NICE_TO_HAVE_SKILL: 15, RequirementCategory.EDUCATION: 10, RequirementCategory.DOMAIN: 10}
VERIFIED = {EvidenceStatus.DEMONSTRATED: 1.0, EvidenceStatus.PARTIAL: 0.5, EvidenceStatus.CLAIMED: 0.0, EvidenceStatus.MISSING: 0.0, EvidenceStatus.UNPROVEN: 0.0}
POTENTIAL = {**VERIFIED, EvidenceStatus.PARTIAL: 0.75, EvidenceStatus.CLAIMED: 0.5}
BAND_THRESHOLDS = {"strong_fit": 75, "moderate_fit": 50}
def fit_band(verified: float) -> str:
    return next((band for band, minimum in BAND_THRESHOLDS.items() if verified >= minimum), "limited_evidence")
def requirement_points(requirements: list[JobRequirement], statuses: dict[str, EvidenceStatus], factors: dict[EvidenceStatus, float]) -> dict[str, float]:
    """Each requirement's exact, additive share of the 0-100 score; the values sum to the unrounded score."""
    grouped: dict[RequirementCategory, list[JobRequirement]] = defaultdict(list)
    for requirement in requirements:
        grouped[requirement.category].append(requirement)
    active = sum(CATEGORY_WEIGHTS[c] for c in grouped)
    return {i.id: CATEGORY_WEIGHTS[c] * 100 / active * i.weight / sum(j.weight for j in items) * factors.get(statuses.get(i.id), 0) for c, items in grouped.items() for i in items}
def score_statuses(requirements: list[JobRequirement], statuses: dict[str, EvidenceStatus]) -> tuple[int, int, str]:
    def total(factors: dict[EvidenceStatus, float]) -> int:
        return round(min(100, max(0, sum(requirement_points(requirements, statuses, factors).values()))))
    verified, potential = total(VERIFIED), total(POTENTIAL)
    return verified, max(verified, potential), fit_band(verified)
def calculate_scores(requirements: list[JobRequirement], matches: list[RequirementMatch]) -> tuple[int, int, str]:
    return score_statuses(requirements, {m.requirement_id: m.status for m in matches})
