import asyncio
import sqlite3

import pytest

from src.database import ScreeningRepository
from src.models.schemas import CandidateAnalysis, ExtractedJob, GitHubVerifyResponse
from src.services.screening_service import ScreeningService


class TrackingLLM:
    def __init__(self):
        self.active = 0
        self.peak = 0

    async def extract_job(self, text):
        return ExtractedJob.model_validate(
            {"title": "Engineer", "requirements": [{"id": "r1", "category": "must_have_skill", "description": "Python"}]}
        )

    async def analyze_candidate(self, job, text):
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1
        return CandidateAnalysis.model_validate(
            {
                "summary": "Relevant experience",
                "requirement_matches": [
                    {
                        "requirement_id": "r1",
                        "status": "demonstrated",
                        "confidence": "high",
                        "evidence": "Built Python APIs",
                        "explanation": "Direct evidence",
                    }
                ],
            }
        )

class TrackingGitHub:
    def __init__(self):
        self.calls = []

    async def verify(self, url, claim):
        self.calls.append(url)
        await asyncio.sleep(0.01)
        return GitHubVerifyResponse(
            status="verified",
            repository={"url": url},
            supported_claims=["Python API"],
            unsupported_claims=[],
            evidence=[{"source": "README.md", "finding": "Python API"}],
            limitations=["Authorship is not proven."],
        )


@pytest.mark.asyncio
async def test_evaluations_are_bounded_and_results_are_persisted(tmp_path):
    llm = TrackingLLM()
    github = TrackingGitHub()
    database = tmp_path / "screenings.db"
    repository = ScreeningRepository(f"sqlite:///{database}")
    service = ScreeningService(llm, repository, max_concurrent_evaluations=2, github=github)

    response = await service.analyze(
        "Need Python",
        [
            (f"resume-{index}.txt", "Python", ["https://github.com/example/project"] if index == 0 else [])
            for index in range(5)
        ],
        False,
    )

    assert llm.peak == 2
    assert github.calls == ["https://github.com/example/project"]
    assert response.candidates[0].github_projects[0].status == "verified"
    assert [candidate.source_name for candidate in response.candidates] == [f"resume-{index}.txt" for index in range(5)]
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM screening_requests").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM candidate_results").fetchone()[0] == 5
        assert connection.execute("SELECT raw_description FROM screening_requests").fetchone()[0] == "Need Python"

    jobs = await repository.list_jobs()
    assert jobs[0].candidate_count == 5
    candidates = await repository.list_candidates(response.request_id)
    assert candidates is not None
    assert len(candidates.candidates) == 5
    detail = await repository.get_candidate(response.request_id, "candidate-1")
    assert detail is not None
    assert detail.github_projects[0].status == "verified"
