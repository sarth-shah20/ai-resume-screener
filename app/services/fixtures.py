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
    profile_key = _MOCK_RESUME_PROFILES[index]
    path = SAMPLE_RESUMES_DIR / profile_key
    text = path.read_text(encoding="utf-8")
    display_name = text.splitlines()[0].strip()
    return {"display_name": display_name, "resume_text": text, "profile_key": profile_key}


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")


# Hand-authored per sample resume rather than computed by string-matching:
# evidence-matching is the LLM's job (Prompt 2 in plan.md #7), so a heuristic
# keyword scanner here would misrepresent what the mock stands in for. Status
# vocabulary follows plan.md/CLAUDE.md exactly -- "unclear" (no evidence
# either way) is used instead of "missing" wherever a skill is simply never
# mentioned, since absence of evidence must never be treated as proof of
# absence. Evidence strings are lifted verbatim from the corresponding
# sample_data/resumes/*.txt file.
MOCK_CANDIDATE_MATCHES: dict[str, list[dict[str, Any]]] = {
    "strong_candidate.txt": [
        {
            "requirement": "Python",
            "requirement_type": "must_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Built and maintained REST APIs in Python (Flask) serving 2M+ daily requests.",
            "explanation": "Directly demonstrates production Python usage at scale.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "AWS (Lambda, S3)",
            "requirement_type": "must_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Designed AWS Lambda functions for asynchronous order processing, backed by S3 for artifact storage.",
            "explanation": "Both named services are used in a described production workflow.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "REST API design",
            "requirement_type": "must_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Built and maintained REST APIs in Python (Flask) serving 2M+ daily requests.",
            "explanation": "Explicit, ongoing ownership of REST API design and operation.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "PostgreSQL",
            "requirement_type": "must_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Migrated the primary datastore to PostgreSQL, including schema design and a zero-downtime cutover.",
            "explanation": "Ownership of schema design and migration goes beyond basic usage.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "Kubernetes",
            "requirement_type": "nice_to_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Deployed them to a Kubernetes cluster; wrote the team's first Helm charts.",
            "explanation": "Hands-on deployment and tooling ownership, not just exposure.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "Docker",
            "requirement_type": "nice_to_have_skills",
            "status": "matched",
            "confidence": "high",
            "evidence": "Containerized all services with Docker.",
            "explanation": "Direct evidence of containerizing production services.",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
        {
            "requirement": "Event-driven architecture",
            "requirement_type": "nice_to_have_skills",
            "status": "matched",
            "confidence": "medium",
            "evidence": "Introduced an event-driven architecture using SQS to decouple ingestion from processing, cutting end-to-end latency by 40%.",
            "explanation": "Concrete architectural decision with a measured outcome.",
            "evidence_location": "Experience: Software Engineer, Alderway Data",
        },
        {
            "requirement": "Production backend systems",
            "requirement_type": "experience_requirements",
            "status": "matched",
            "confidence": "high",
            "evidence": "Backend engineer with 5 years of experience building and operating production services on AWS.",
            "explanation": "Stated years exceed the 3-year minimum and are backed by specific project detail.",
            "evidence_location": "Summary",
        },
        {
            "requirement": "Bachelor's degree in Computer Science or related field",
            "requirement_type": "education_requirements",
            "status": "matched",
            "confidence": "high",
            "evidence": "B.S. in Computer Science, University of Washington (2019).",
            "explanation": "Exact match to the stated requirement.",
            "evidence_location": "Education",
        },
        {
            "requirement": "Platform / infrastructure engineering",
            "requirement_type": "domain_requirements",
            "status": "matched",
            "confidence": "medium",
            "evidence": "Backend Engineer, Northbridge Systems -- platform team.",
            "explanation": "Current role is explicitly on a platform team with infrastructure ownership (datastore migration, Kubernetes deployment).",
            "evidence_location": "Experience: Backend Engineer, Northbridge Systems",
        },
    ],
    "borderline_candidate.txt": [
        {
            "requirement": "Python",
            "requirement_type": "must_have_skills",
            "status": "matched",
            "confidence": "medium",
            "evidence": "Wrote internal tooling in Python to automate inventory reports.",
            "explanation": "Real Python usage, though scoped to internal tooling rather than production services.",
            "evidence_location": "Experience: Software Developer, Fielding Retail Co.",
        },
        {
            "requirement": "AWS (Lambda, S3)",
            "requirement_type": "must_have_skills",
            "status": "partial",
            "confidence": "medium",
            "evidence": "Used AWS Lambda in one project to trigger nightly report generation.",
            "explanation": "Lambda experience is real but limited to one project; no S3 usage mentioned and production scale/duration is unavailable.",
            "evidence_location": "Experience: Software Developer, Fielding Retail Co.",
        },
        {
            "requirement": "REST API design",
            "requirement_type": "must_have_skills",
            "status": "partial",
            "confidence": "low",
            "evidence": "Built a small internal scripts and a basic Flask app for ticket tracking.",
            "explanation": "Suggests some API-adjacent work but doesn't explicitly describe REST API design.",
            "evidence_location": "Experience: Junior Developer, Campus IT Help Desk",
        },
        {
            "requirement": "PostgreSQL",
            "requirement_type": "must_have_skills",
            "status": "partial",
            "confidence": "medium",
            "evidence": "Worked with a PostgreSQL database maintained by another team; wrote read-only reporting queries against it.",
            "explanation": "Confirmed PostgreSQL usage, but as a consumer of an existing database rather than someone who designs or owns schemas.",
            "evidence_location": "Experience: Software Developer, Fielding Retail Co.",
        },
        {
            "requirement": "Kubernetes",
            "requirement_type": "nice_to_have_skills",
            "status": "unclear",
            "confidence": "high",
            "evidence": None,
            "explanation": "No mention of Kubernetes anywhere in the resume.",
            "evidence_location": None,
        },
        {
            "requirement": "Docker",
            "requirement_type": "nice_to_have_skills",
            "status": "unclear",
            "confidence": "high",
            "evidence": None,
            "explanation": "No mention of Docker anywhere in the resume.",
            "evidence_location": None,
        },
        {
            "requirement": "Event-driven architecture",
            "requirement_type": "nice_to_have_skills",
            "status": "unclear",
            "confidence": "high",
            "evidence": None,
            "explanation": "No mention of event-driven systems or message queues.",
            "evidence_location": None,
        },
        {
            "requirement": "Production backend systems",
            "requirement_type": "experience_requirements",
            "status": "partial",
            "confidence": "low",
            "evidence": "Software Developer, Fielding Retail Co. (2022 - Present); Junior Developer, Campus IT Help Desk (2021 - 2022, part-time).",
            "explanation": "Under 2 years of relevant experience against a 3-year minimum, and most of it is internal tooling rather than production backend systems.",
            "evidence_location": "Experience",
        },
        {
            "requirement": "Bachelor's degree in Computer Science or related field",
            "requirement_type": "education_requirements",
            "status": "partial",
            "confidence": "medium",
            "evidence": "Associate's Degree in Information Technology, Austin Community College (2021). Currently completing a B.S. in Computer Science part-time.",
            "explanation": "Bachelor's is in progress, not yet completed.",
            "evidence_location": "Education",
        },
        {
            "requirement": "Platform / infrastructure engineering",
            "requirement_type": "domain_requirements",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "No resume evidence directly addressing platform or infrastructure engineering work.",
            "evidence_location": None,
        },
    ],
    "keyword_heavy_weak_evidence.txt": [
        {
            "requirement": "Python",
            "requirement_type": "must_have_skills",
            "status": "partial",
            "confidence": "low",
            "evidence": "Attended internal workshops covering Python, AWS, and Kubernetes basics.",
            "explanation": "Python is listed as a skill and mentioned via workshop attendance, but no resume evidence shows it being used to build or ship anything.",
            "evidence_location": "Experience: IT Support Specialist, Meridian Office Solutions",
        },
        {
            "requirement": "AWS (Lambda, S3)",
            "requirement_type": "must_have_skills",
            "status": "partial",
            "confidence": "low",
            "evidence": "Attended internal workshops covering Python, AWS, and Kubernetes basics.",
            "explanation": "AWS appears as a skill keyword and a workshop topic; no Lambda or S3 usage is described.",
            "evidence_location": "Experience: IT Support Specialist, Meridian Office Solutions",
        },
        {
            "requirement": "REST API design",
            "requirement_type": "must_have_skills",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "REST APIs are listed as a skill keyword only; not mentioned anywhere in the experience section.",
            "evidence_location": None,
        },
        {
            "requirement": "PostgreSQL",
            "requirement_type": "must_have_skills",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "PostgreSQL appears only in the skills list with no supporting experience.",
            "evidence_location": None,
        },
        {
            "requirement": "Kubernetes",
            "requirement_type": "nice_to_have_skills",
            "status": "partial",
            "confidence": "low",
            "evidence": "Attended internal workshops covering Python, AWS, and Kubernetes basics.",
            "explanation": "Workshop-level exposure only; no hands-on usage described.",
            "evidence_location": "Experience: IT Support Specialist, Meridian Office Solutions",
        },
        {
            "requirement": "Docker",
            "requirement_type": "nice_to_have_skills",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "Docker appears only in the skills list with no supporting experience.",
            "evidence_location": None,
        },
        {
            "requirement": "Event-driven architecture",
            "requirement_type": "nice_to_have_skills",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "Listed as a skill keyword only; not mentioned in any project or role.",
            "evidence_location": None,
        },
        {
            "requirement": "Production backend systems",
            "requirement_type": "experience_requirements",
            "status": "unclear",
            "confidence": "high",
            "evidence": "Supported employee laptops, printers, and network connectivity issues.",
            "explanation": "Experience section describes IT support and help-desk work, not backend development; no production backend systems evidence found.",
            "evidence_location": "Experience: IT Support Specialist, Meridian Office Solutions",
        },
        {
            "requirement": "Bachelor's degree in Computer Science or related field",
            "requirement_type": "education_requirements",
            "status": "missing",
            "confidence": "high",
            "evidence": "Certificate in IT Support, Local Community College (2019).",
            "explanation": "The only listed credential is a support certificate, not a bachelor's degree in Computer Science or a related field.",
            "evidence_location": "Education",
        },
        {
            "requirement": "Platform / infrastructure engineering",
            "requirement_type": "domain_requirements",
            "status": "unclear",
            "confidence": "medium",
            "evidence": None,
            "explanation": "No resume evidence addressing platform or infrastructure engineering work.",
            "evidence_location": None,
        },
    ],
}


def mock_analyze_candidate(profile_key: str) -> list[dict[str, Any]]:
    """Return the canned per-requirement matches for a mock resume profile.

    Real implementation (src/services/llm_service.py, Prompt 2 in plan.md
    #7) will generate these per resume/JD pair; this mock is intentionally
    hand-authored per sample profile rather than computed, since faking a
    heuristic evidence-matcher would misrepresent what an LLM call actually
    does. The deterministic score is calculated for real from this data --
    see app/services/scoring.py.
    """
    return MOCK_CANDIDATE_MATCHES.get(profile_key, [])


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
