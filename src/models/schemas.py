from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class RequirementCategory(StrEnum):
    MUST_HAVE_SKILL = "must_have_skill"
    EXPERIENCE = "experience"
    NICE_TO_HAVE_SKILL = "nice_to_have_skill"
    EDUCATION = "education"
    DOMAIN = "domain"

class EvidenceStatus(StrEnum):
    DEMONSTRATED = "demonstrated"
    CLAIMED = "claimed"
    PARTIAL = "partial"
    MISSING = "missing"
    UNPROVEN = "unproven"

class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class JobRequirement(BaseModel):
    id: str
    category: RequirementCategory
    description: str = Field(min_length=1)
    priority: str = "required"
    weight: float = Field(default=1, gt=0)
    minimum_years: float | None = Field(default=None, ge=0)

class ExtractedJob(BaseModel):
    title: str = "Untitled role"
    requirements: list[JobRequirement] = Field(min_length=1)

class RequirementMatch(BaseModel):
    requirement_id: str
    status: EvidenceStatus
    confidence: Confidence
    evidence: str | None = None
    evidence_section: str | None = None
    explanation: str = Field(min_length=1)
    @model_validator(mode="after")
    def require_grounding(self) -> "RequirementMatch":
        if self.status in {EvidenceStatus.DEMONSTRATED, EvidenceStatus.PARTIAL} and not self.evidence:
            raise ValueError("demonstrated and partial matches require evidence")
        return self

class CandidateAnalysis(BaseModel):
    candidate_name: str | None = None
    summary: str
    requirement_matches: list[RequirementMatch]
    gaps: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)

class CandidateResult(BaseModel):
    candidate_id: str
    source_name: str
    verified_score: int = Field(ge=0, le=100)
    potential_score: int = Field(ge=0, le=100)
    fit_band: str
    summary: str
    requirement_matches: list[RequirementMatch]
    gaps: list[str]
    interview_questions: list[str]
    github_projects: list["GitHubVerifyResponse"] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    request_id: str
    job: ExtractedJob
    candidates: list[CandidateResult]
    warnings: list[str] = Field(default_factory=list)
    processing_ms: int

class GitHubVerifyRequest(BaseModel):
    repository_url: str
    claimed_description: str = Field(min_length=1, max_length=4000)

class GitHubVerifyResponse(BaseModel):
    status: str
    repository: dict[str, object]
    supported_claims: list[str]
    unsupported_claims: list[str]
    evidence: list[dict[str, str]]
    limitations: list[str]

class JobDashboardItem(BaseModel):
    job_id: str
    title: str
    candidate_count: int
    latest_analysis_at: datetime
    average_verified_score: float
    average_potential_score: float

class JobDashboardResponse(BaseModel):
    jobs: list[JobDashboardItem]

class CandidateDashboardItem(BaseModel):
    candidate_id: str
    source_name: str
    verified_score: int
    potential_score: int
    fit_band: str
    summary: str
    github_project_count: int
    analyzed_at: datetime

class JobCandidatesResponse(BaseModel):
    job_id: str
    job: ExtractedJob
    raw_description: str
    candidates: list[CandidateDashboardItem]
