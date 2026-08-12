from collections import defaultdict
from src.models.schemas import EvidenceStatus, JobRequirement, RequirementCategory, RequirementMatch
CATEGORY_WEIGHTS = {RequirementCategory.MUST_HAVE_SKILL: 40, RequirementCategory.EXPERIENCE: 25, RequirementCategory.NICE_TO_HAVE_SKILL: 15, RequirementCategory.EDUCATION: 10, RequirementCategory.DOMAIN: 10}
VERIFIED = {EvidenceStatus.DEMONSTRATED: 1.0, EvidenceStatus.PARTIAL: 0.5, EvidenceStatus.CLAIMED: 0.0, EvidenceStatus.MISSING: 0.0, EvidenceStatus.UNPROVEN: 0.0}
POTENTIAL = {**VERIFIED, EvidenceStatus.PARTIAL: 0.75, EvidenceStatus.CLAIMED: 0.5}
def calculate_scores(requirements: list[JobRequirement], matches: list[RequirementMatch]) -> tuple[int, int, str]:
    by_id = {m.requirement_id: m for m in matches}
    grouped: dict[RequirementCategory, list[JobRequirement]] = defaultdict(list)
    for requirement in requirements:
        grouped[requirement.category].append(requirement)
    def total(factors: dict[EvidenceStatus, float]) -> int:
        active = sum(CATEGORY_WEIGHTS[c] for c, items in grouped.items() if items)
        score = sum(CATEGORY_WEIGHTS[c] * sum(i.weight * factors.get(by_id[i.id].status, 0) for i in items if i.id in by_id) / sum(i.weight for i in items) for c, items in grouped.items())
        return round(min(100, max(0, score * 100 / active))) if active else 0
    verified, potential = total(VERIFIED), total(POTENTIAL)
    band = "strong_fit" if verified >= 75 else "moderate_fit" if verified >= 50 else "limited_evidence"
    return verified, max(verified, potential), band
