"""Mock data standing in for the not-yet-built extraction/analysis backend.

Shapes here mirror the JSON contracts documented in plan.md #7 (Prompt 1:
requirement extraction) so that swapping ``ScreeningClient`` methods over to
real LLM calls later is a body-only change -- no view code should need to
change when that happens.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

_SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"
SAMPLE_JOB_DESCRIPTIONS_DIR = _SAMPLE_DATA_DIR / "job_descriptions"
SAMPLE_RESUMES_DIR = _SAMPLE_DATA_DIR / "resumes"


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


# Rotated by upload order so a demo run naturally shows one of each profile
# plan.md #1 asks for: strong / borderline / keyword-heavy-but-weak-evidence.
_MOCK_RESUME_PROFILES = [
    "strong_candidate.txt",
    "borderline_candidate.txt",
    "keyword_heavy_weak_evidence.txt",
]


def mock_parse_resume(filename: str) -> dict[str, Any]:
    """Return mock parsed resume data, deterministically chosen from the filename.

    Does not read the real uploaded file's bytes -- real PDF/DOCX text
    extraction belongs to src/parsers/resume_parser.py (PyMuPDF /
    python-docx), which isn't built yet and is a backend-stream dependency,
    not a UI one. Instead this rotates through the synthetic sample resumes
    in sample_data/resumes/ (deterministic per filename, so re-processing
    the same file is stable) so the intake -> screening -> report flow has
    something real to render end to end.
    """
    index = int(hashlib.md5(filename.encode("utf-8")).hexdigest(), 16) % len(
        _MOCK_RESUME_PROFILES
    )
    path = SAMPLE_RESUMES_DIR / _MOCK_RESUME_PROFILES[index]
    text = path.read_text(encoding="utf-8")
    display_name = text.splitlines()[0].strip()
    return {"display_name": display_name, "resume_text": text}


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")


def mock_redact_pii(text: str) -> str:
    """Return a copy of text with emails/phone numbers replaced by placeholders.

    Real implementation (src/services/pii_service.py) will also handle
    names, addresses, and photos per plan.md #10; this mock only covers the
    two patterns that are safe to detect with a regex, purely so Blind
    Review Mode has something real to show in the UI before that service
    exists.
    """
    text = _EMAIL_RE.sub("[redacted email]", text)
    text = _PHONE_RE.sub("[redacted phone]", text)
    return text
