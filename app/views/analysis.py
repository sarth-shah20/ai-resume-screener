"""New analysis form backed entirely by POST /api/v1/analyze."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.services.screening_client import (
    BackendRequestError,
    BackendUnavailable,
    Upload,
    get_client,
)
from app.state import navigate

_SAMPLE_JOB = Path(__file__).resolve().parents[2] / "sample_data/job_descriptions/backend_engineer.txt"


def _upload(file: object) -> Upload:
    return Upload(
        filename=file.name,
        content=file.getvalue(),
        content_type=file.type or "application/octet-stream",
    )


def render() -> None:
    try:
        limits = get_client().health()
    except (BackendUnavailable, BackendRequestError):
        limits = {"max_resumes_per_request": 5, "max_file_size_mb": 5}
    max_resumes = int(limits["max_resumes_per_request"])
    max_size = int(limits["max_file_size_mb"])

    with st.form("analysis_form"):
        st.markdown("### 1. Job description")
        source = st.radio(
            "Job description source",
            ["Paste text", "Upload PDF, DOCX, or TXT"],
            horizontal=True,
        )
        job_text = ""
        job_file = None
        if source == "Paste text":
            default = (
                _SAMPLE_JOB.read_text(encoding="utf-8")
                if st.session_state.pop("load_sample_job", False)
                else ""
            )
            job_text = st.text_area(
                "Job description",
                value=default,
                height=220,
                placeholder="Paste the complete job description...",
            )
            st.form_submit_button(
                "Load backend engineer sample",
                on_click=lambda: st.session_state.update({"load_sample_job": True}),
            )
        else:
            job_file = st.file_uploader(
                "Job description file", type=["pdf", "docx", "txt"]
            )

        st.markdown("### 2. Candidates")
        resume_files = st.file_uploader(
            "Resume files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help=(
                f"Upload up to {max_resumes} resumes; each file may be up to "
                f"{max_size} MB. GitHub repository hyperlinks are detected automatically."
            ),
        )
        resume_text = st.text_area(
            "Optional pasted resume",
            height=140,
            placeholder="You may paste one resume in addition to uploaded files.",
        )
        blind_mode = st.toggle(
            "Blind review mode",
            value=True,
            help=(
                "Redacts common email addresses, phone numbers, and LinkedIn links "
                "before model analysis. This is basic redaction, not full anonymization."
            ),
        )
        submitted = st.form_submit_button(
            "Run evidence-based analysis", type="primary", use_container_width=True
        )

    if not submitted:
        st.caption(
            "The backend extracts requirements, evaluates candidates concurrently, "
            "calculates deterministic scores, verifies public GitHub repositories, "
            "and saves the complete reports."
        )
        return

    errors = []
    if source == "Paste text" and not job_text.strip():
        errors.append("Paste a job description.")
    if source != "Paste text" and job_file is None:
        errors.append("Upload a job description file.")
    candidate_count = len(resume_files or []) + (1 if resume_text.strip() else 0)
    if not 1 <= candidate_count <= max_resumes:
        errors.append(f"Provide between one and {max_resumes} resumes.")
    if errors:
        for error in errors:
            st.error(error)
        return

    try:
        with st.spinner(
            "Extracting requirements, evaluating evidence, checking GitHub, and saving reports..."
        ):
            result = get_client().analyze(
                job_text=job_text.strip() or None,
                job_file=_upload(job_file) if job_file else None,
                resume_text=resume_text.strip() or None,
                resume_files=[_upload(file) for file in resume_files or []],
                blind_mode=blind_mode,
            )
    except (BackendUnavailable, BackendRequestError) as exc:
        st.error(str(exc), icon="🚫")
        return

    st.session_state["latest_analysis"] = result
    first = result["candidates"][0]
    navigate("report", result["request_id"], first["candidate_id"])
    st.rerun()
