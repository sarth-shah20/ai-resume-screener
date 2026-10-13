"""Deterministic explanations of the screening score. No LLM calls."""

import re
from difflib import SequenceMatcher

from pydantic import BaseModel

from src.models.schemas import EvidenceStatus, JobRequirement, RequirementMatch
from src.services.scoring_service import (
    BAND_THRESHOLDS,
    POTENTIAL,
    VERIFIED,
    requirement_points,
    score_statuses,
)

GROUNDING_THRESHOLD = 0.85
_FULL_CREDIT = {status: 1.0 for status in EvidenceStatus}


class Contribution(BaseModel):
    requirement_id: str
    description: str
    category: str
    status: EvidenceStatus
    max_points: float
    verified_points: float
    potential_points: float

    @property
    def uplift_points(self) -> float:
        """Points that are claimed or partly evidenced but not yet verified."""
        return max(0.0, self.potential_points - self.verified_points)

    @property
    def lost_points(self) -> float:
        return self.max_points - max(self.verified_points, self.potential_points)


class PathStep(BaseModel):
    requirement_id: str
    description: str
    current_status: EvidenceStatus
    gain: float
    score_after: int


def _statuses(matches: list[RequirementMatch]) -> dict[str, EvidenceStatus]:
    return {match.requirement_id: match.status for match in matches}


def score_breakdown(
    requirements: list[JobRequirement], matches: list[RequirementMatch]
) -> list[Contribution]:
    """Exact additive attribution: verified_points sum to the verified score."""
    statuses = _statuses(matches)
    maximum = requirement_points(requirements, statuses, _FULL_CREDIT)
    verified = requirement_points(requirements, statuses, VERIFIED)
    potential = requirement_points(requirements, statuses, POTENTIAL)
    return [
        Contribution(
            requirement_id=item.id,
            description=item.description,
            category=item.category.value,
            status=statuses.get(item.id, EvidenceStatus.UNPROVEN),
            max_points=maximum[item.id],
            verified_points=verified[item.id],
            potential_points=potential[item.id],
        )
        for item in requirements
    ]


def next_band_target(verified_score: int) -> tuple[str, int] | None:
    """The nearest fit band above the current score, or None at the top band."""
    above = [(band, minimum) for band, minimum in BAND_THRESHOLDS.items() if minimum > verified_score]
    return min(above, key=lambda item: item[1]) if above else None


def shortest_path(
    requirements: list[JobRequirement], matches: list[RequirementMatch], target: int
) -> list[PathStep]:
    """Fewest requirements that must become demonstrated to reach ``target``.

    The score is additive, so taking the largest available gains first is
    minimal in the number of changes. Returns [] when the target is already
    met or cannot be reached.
    """
    statuses = _statuses(matches)
    if score_statuses(requirements, statuses)[0] >= target:
        return []
    gaps = sorted(
        (item for item in score_breakdown(requirements, matches) if item.max_points > item.verified_points),
        key=lambda item: item.max_points - item.verified_points,
        reverse=True,
    )
    steps: list[PathStep] = []
    for item in gaps:
        statuses[item.requirement_id] = EvidenceStatus.DEMONSTRATED
        score = score_statuses(requirements, statuses)[0]
        steps.append(
            PathStep(
                requirement_id=item.requirement_id,
                description=item.description,
                current_status=item.status,
                gain=item.max_points - item.verified_points,
                score_after=score,
            )
        )
        if score >= target:
            return steps
    return []


def contrast(first: list[Contribution], second: list[Contribution]) -> list[tuple[Contribution, Contribution, float]]:
    """Requirements where two candidates differ, largest verified-point gap first."""
    other = {item.requirement_id: item for item in second}
    pairs = [
        (item, other[item.requirement_id], item.verified_points - other[item.requirement_id].verified_points)
        for item in first
        if item.requirement_id in other
    ]
    return sorted((pair for pair in pairs if abs(pair[2]) > 1e-9), key=lambda pair: abs(pair[2]), reverse=True)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def is_grounded(evidence: str, source_text: str) -> bool:
    """Whether a quoted evidence excerpt really appears in the source document.

    Tolerates reflowed whitespace, casing, punctuation, and elisions; rejects
    quotes whose wording is not found in the source.
    """
    quote, source = _normalize(evidence), _normalize(source_text)
    if not quote:
        return False
    if quote in source:
        return True
    matcher = SequenceMatcher(None, quote, source, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks() if block.size >= 4)
    return matched / len(quote) >= GROUNDING_THRESHOLD
