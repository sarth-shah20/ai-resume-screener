import json
import re
from typing import Protocol, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from src.config import Settings
from src.models.schemas import CandidateAnalysis, ExtractedJob
from src.prompts import SYSTEM_PROMPT, candidate_prompt, github_prompt, job_prompt

T = TypeVar("T", bound=BaseModel)

class LLMError(RuntimeError):
    pass

class LLMProvider(Protocol):
    async def extract_job(self, text: str) -> ExtractedJob: ...
    async def analyze_candidate(self, job: ExtractedJob, text: str) -> CandidateAnalysis: ...
    async def verify_github(self, claim: str, evidence: dict[str, object]) -> dict[str, object]: ...

class NvidiaLLMProvider:
    def __init__(self, settings: Settings):
        if not settings.nvidia_api_key:
            raise LLMError("NVIDIA_API_KEY is not configured.")
        self.model = settings.nvidia_model
        self.client = AsyncOpenAI(api_key=settings.nvidia_api_key, base_url=settings.nvidia_base_url, timeout=settings.llm_timeout_seconds, max_retries=1)

    async def _request(self, prompt: str, schema: type[T]) -> T:
        last_error: Exception | None = None
        for attempt in range(2):
            repair = "\nYour previous response was invalid. Return only schema-valid JSON." if attempt else ""
            try:
                response = await self.client.chat.completions.create(model=self.model, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt + repair}], temperature=0.1, top_p=1, max_tokens=4096)
                return schema.model_validate(json.loads(_json_text(response.choices[0].message.content or "")))
            except (json.JSONDecodeError, ValidationError, IndexError, AttributeError) as exc:
                last_error = exc
            except Exception as exc:
                raise LLMError("The NVIDIA model request failed.") from exc
        raise LLMError("The model returned invalid structured output.") from last_error

    async def extract_job(self, text: str) -> ExtractedJob:
        return await self._request(job_prompt(text), ExtractedJob)
    async def analyze_candidate(self, job: ExtractedJob, text: str) -> CandidateAnalysis:
        return await self._request(candidate_prompt(job, text), CandidateAnalysis)
    async def verify_github(self, claim: str, evidence: dict[str, object]) -> dict[str, object]:
        class RepoAssessment(BaseModel):
            status: str
            supported_claims: list[str]
            unsupported_claims: list[str]
            evidence: list[dict[str, str]]
        return (await self._request(github_prompt(claim, evidence), RepoAssessment)).model_dump()

def _json_text(value: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", value, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else value.strip()
