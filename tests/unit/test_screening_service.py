import asyncio
import sqlite3

import pytest

from src.database import ScreeningRepository
from src.models.schemas import CandidateAnalysis, ExtractedJob
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


@pytest.mark.asyncio
async def test_evaluations_are_bounded_and_results_are_persisted(tmp_path):
    llm = TrackingLLM()
    database = tmp_path / "screenings.db"
    service = ScreeningService(llm, ScreeningRepository(f"sqlite:///{database}"), max_concurrent_evaluations=2)

    response = await service.analyze("Need Python", [(f"resume-{index}.txt", "Python") for index in range(5)], False)

    assert llm.peak == 2
    assert [candidate.source_name for candidate in response.candidates] == [f"resume-{index}.txt" for index in range(5)]
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM screening_requests").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM candidate_results").fetchone()[0] == 5
