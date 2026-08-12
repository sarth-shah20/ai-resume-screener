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

from typing import Any


class ScreeningClient:
    """Single entry point the UI uses for all analysis operations."""

    def extract_requirements(self, job_description: str) -> dict[str, Any]:
        """Return structured requirements extracted from a job description.

        Real implementation will call src/services/llm_service.py (Prompt 1
        in plan.md #7) and validate against src/models/schemas.py.
        """
        raise NotImplementedError("Wired up in the job-setup module.")

    def parse_resume(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """Return extracted text/sections for one uploaded resume.

        Real implementation will call src/parsers/resume_parser.py.
        """
        raise NotImplementedError("Wired up in the candidate-intake module.")

    def analyze_candidate(
        self, resume: dict[str, Any], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Return evidence-grounded requirement matches plus a deterministic score.

        Real implementation will call src/services/llm_service.py (Prompt 2)
        for evidence matching and src/services/scoring_service.py for the
        deterministic score -- the LLM never produces the final number.
        """
        raise NotImplementedError("Wired up in the screening-run module.")

    def redact_pii(self, text: str) -> str:
        """Return a PII-redacted copy of resume text for Blind Review Mode.

        Real implementation will call src/services/pii_service.py.
        """
        raise NotImplementedError("Wired up in the candidate-intake module.")


def get_client() -> ScreeningClient:
    return ScreeningClient()
