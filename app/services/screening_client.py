"""Facade between the UI and the analysis backend.

None of the backend modules this client will eventually delegate to exist
yet (``src/models``, ``src/services/llm_service.py``,
``src/services/scoring_service.py``, ``src/services/pii_service.py`` are
still empty per CLAUDE.md's architecture boundaries). Each method below is
the integration point: once the corresponding backend piece lands, the
method body swaps from a mock/`NotImplementedError` to a real call, and no
view code has to change because the call signature and return shape are
the contract.

Do not reimplement backend logic here -- if a view needs something this
client can't yet provide, that is a signal to flag the gap, not to fake a
scoring/LLM pipeline inside the UI layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services import fixtures, scoring

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB, per plan.md's "oversized" handling


class ScreeningClient:
    """Single entry point the UI uses for all analysis operations."""

    def extract_requirements(self, job_description: str) -> dict[str, Any]:
        """Return structured requirements extracted from a job description.

        Currently returns a fixed mock (see app/services/fixtures.py) since
        src/services/llm_service.py and src/models/schemas.py don't exist
        yet. Real implementation will call the LLM service (Prompt 1 in
        plan.md #7) and validate the response against the Pydantic schema --
        this method's signature and return shape are the contract views code
        against, so that swap should require no view changes.
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description must not be empty.")
        return fixtures.mock_extract_requirements(job_description)

    def parse_resume(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """Validate an uploaded resume and return its extracted text.

        Validation (extension, empty, oversized) is real and enforced here
        since it doesn't depend on actual PDF/DOCX parsing. The text itself
        is mocked (see app/services/fixtures.py) since
        src/parsers/resume_parser.py -- which will call PyMuPDF / python-docx
        -- doesn't exist yet. Swapping the mock for a real parse call should
        only change this method's body, not its signature or the errors it
        raises.
        """
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_RESUME_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{extension or 'unknown'}'. Upload a PDF or DOCX resume."
            )
        if not file_bytes:
            raise ValueError("This file is empty.")
        if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
            raise ValueError("This file exceeds the 5 MB size limit.")
        return fixtures.mock_parse_resume(filename)

    def analyze_candidate(
        self, resume: dict[str, Any], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Return evidence-grounded requirement matches plus a deterministic score.

        ``resume`` is expected to carry the fields set by ``parse_resume``
        (``resume_text``, and the mock-only ``profile_key`` used to look up
        canned evidence). The evidence matches themselves are mocked (see
        app/services/fixtures.py) since src/services/llm_service.py (Prompt
        2 in plan.md #7) doesn't exist yet. The score is calculated for
        real, in app/services/scoring.py, from those matches -- consistent
        with never letting the LLM half produce the final number, mocked or
        not. Once the real LLM service lands, only this method's body
        changes: it will stop reading ``profile_key`` and instead call the
        LLM with ``resume["resume_text"]`` and ``requirements``, but will
        still hand the result to the same scoring function.
        """
        profile_key = resume.get("profile_key")
        matches = fixtures.mock_analyze_candidate(profile_key) if profile_key else []
        if not matches:
            raise ValueError("Could not analyze this candidate's resume. Please retry.")
        score = scoring.score_candidate(matches, requirements)
        recommendation, confidence_label = scoring.recommendation_for(score["overall_score"])
        return {
            "matches": matches,
            "overall_score": score["overall_score"],
            "category_scores": score["category_scores"],
            "recommendation": recommendation,
            "confidence_label": confidence_label,
        }

    def redact_pii(self, text: str) -> str:
        """Return a PII-redacted copy of resume text for Blind Review Mode.

        Currently a regex-based mock covering email/phone only (see
        app/services/fixtures.py). Real implementation will call
        src/services/pii_service.py, which per plan.md #10 also needs to
        handle names, addresses, and photos.
        """
        return fixtures.mock_redact_pii(text)


def get_client() -> ScreeningClient:
    return ScreeningClient()
