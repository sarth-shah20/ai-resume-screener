"""Mock data standing in for the not-yet-built extraction/analysis backend.

Shapes here mirror the JSON contracts documented in plan.md #7 (Prompt 1:
requirement extraction) so that swapping ``ScreeningClient`` methods over to
real LLM calls later is a body-only change -- no view code should need to
change when that happens.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SAMPLE_JOB_DESCRIPTIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "sample_data" / "job_descriptions"
)


def list_sample_job_descriptions() -> dict[str, str]:
    """Return {display_name: file_path} for every .txt file in sample_data/job_descriptions."""
    if not SAMPLE_JOB_DESCRIPTIONS_DIR.is_dir():
        return {}
    return {
        path.stem.replace("_", " ").title(): str(path)
        for path in sorted(SAMPLE_JOB_DESCRIPTIONS_DIR.glob("*.txt"))
    }


MOCK_EXTRACTED_REQUIREMENTS: dict[str, Any] = {
    "job_title": "Backend Engineer",
    "must_have_skills": [
        {"name": "Python", "weight": 12},
        {"name": "AWS (Lambda, S3)", "weight": 10},
        {"name": "REST API design", "weight": 9},
        {"name": "PostgreSQL", "weight": 9},
    ],
    "nice_to_have_skills": [
        {"name": "Kubernetes", "weight": 6},
        {"name": "Docker", "weight": 5},
        {"name": "Event-driven architecture", "weight": 4},
    ],
    "experience_requirements": [
        {"name": "Production backend systems", "minimum_years": 3, "weight": 25},
    ],
    "education_requirements": [
        {"name": "Bachelor's degree in Computer Science or related field", "weight": 10},
    ],
    "domain_requirements": [
        {"name": "Platform / infrastructure engineering", "weight": 10},
    ],
}


def mock_extract_requirements(job_description: str) -> dict[str, Any]:
    """Return a fixed mock extraction result for any non-empty job description.

    Real implementation (src/services/llm_service.py) will vary its output
    per job description; this mock intentionally does not parse the input --
    doing so would mean reimplementing the extraction logic that belongs to
    the backend stream.
    """
    return MOCK_EXTRACTED_REQUIREMENTS
