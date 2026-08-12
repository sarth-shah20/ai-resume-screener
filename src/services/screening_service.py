import asyncio
import time
from uuid import uuid4
from src.database import ScreeningRepository
from src.models.schemas import AnalyzeResponse, CandidateResult
from src.services.llm_service import LLMProvider
from src.services.pii_service import redact_pii
from src.services.scoring_service import calculate_scores

class ScreeningService:
    def __init__(self, llm: LLMProvider, repository: ScreeningRepository, max_concurrent_evaluations: int):
        self.llm = llm
        self.repository = repository
        self.max_concurrent_evaluations = max_concurrent_evaluations

    async def analyze(self, job_text: str, resumes: list[tuple[str, str]], blind_mode: bool) -> AnalyzeResponse:
        started = time.perf_counter()
        job = await self.llm.extract_job(job_text)
        semaphore = asyncio.Semaphore(self.max_concurrent_evaluations)

        async def evaluate(index: int, source_name: str, resume: str) -> CandidateResult:
            async with semaphore:
                analysis = await self.llm.analyze_candidate(job, redact_pii(resume) if blind_mode else resume)
            verified, potential, band = calculate_scores(job.requirements, analysis.requirement_matches)
            return CandidateResult(candidate_id=f"candidate-{index}", source_name=source_name if not blind_mode else f"Candidate {index}", verified_score=verified, potential_score=potential, fit_band=band, summary=analysis.summary, requirement_matches=analysis.requirement_matches, gaps=analysis.gaps, interview_questions=analysis.interview_questions)

        candidates = await asyncio.gather(
            *(evaluate(index, source_name, resume) for index, (source_name, resume) in enumerate(resumes, start=1))
        )
        response = AnalyzeResponse(request_id=str(uuid4()), job=job, candidates=candidates, processing_ms=round((time.perf_counter() - started) * 1000))
        await self.repository.save(response)
        return response
