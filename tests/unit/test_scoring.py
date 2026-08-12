from src.models.schemas import ExtractedJob, RequirementMatch
from src.services.scoring_service import calculate_scores

def test_claimed_skill_has_only_potential_score():
    job = ExtractedJob.model_validate({"title": "API Engineer", "requirements": [{"id": "r1", "category": "must_have_skill", "description": "FastAPI"}]})
    matches = [RequirementMatch(requirement_id="r1", status="claimed", confidence="medium", explanation="Listed only")]
    assert calculate_scores(job.requirements, matches) == (0, 50, "limited_evidence")

def test_demonstrated_skill_scores_full_points():
    job = ExtractedJob.model_validate({"title": "API Engineer", "requirements": [{"id": "r1", "category": "must_have_skill", "description": "FastAPI"}]})
    matches = [RequirementMatch(requirement_id="r1", status="demonstrated", confidence="high", evidence="Built FastAPI APIs", explanation="Direct evidence")]
    assert calculate_scores(job.requirements, matches) == (100, 100, "strong_fit")
