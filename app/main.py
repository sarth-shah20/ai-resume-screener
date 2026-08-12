"""Entry point for the recruiter screening UI.

Run with: streamlit run app/main.py

This is a single-page wizard rather than Streamlit's native multipage
``pages/`` convention: the sidebar stepper needs to reflect data-driven
completion state (has a JD been extracted? have candidates been screened?)
rather than a static file list, and view state needs to be shared across
steps via ``st.session_state``. Each step's content lives in
``app.views.<step>`` and is dispatched below.
"""

from __future__ import annotations

import streamlit as st

from app.components.layout import disclaimer_banner, page_header
from app.components.nav import render_sidebar
from app.components.states import empty_state
from app.state import STEPS, init_session_state
from app.theme import apply_theme

st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_session_state()
render_sidebar()

_STEP_LABELS = {step["key"]: step["label"] for step in STEPS}
_STEP_COPY = {
    "job_setup": (
        "Paste a job description and let the assistant extract structured, "
        "weighted requirements.",
        "📋",
        "No job description yet",
        "Start by pasting or loading a sample job description in the Job "
        "Setup step. This module is built next.",
    ),
    "candidates": (
        "Upload PDF or DOCX resumes for the candidates you want screened.",
        "📄",
        "No candidates uploaded yet",
        "Once a job description is set, upload resumes here.",
    ),
    "screening": (
        "Run evidence-grounded analysis against the extracted requirements.",
        "🔍",
        "Nothing to screen yet",
        "Complete job setup and candidate upload first, then run screening.",
    ),
    "report": (
        "Review each candidate's score, matched evidence, and gaps.",
        "📊",
        "No results yet",
        "Results will appear here once screening has run.",
    ),
    "gaps": (
        "See uncertainty-driven interview questions generated from evidence gaps.",
        "💬",
        "No interview questions yet",
        "Gap-based questions are generated after screening completes.",
    ),
    "compare": (
        "Compare candidates side by side once more than one has been screened.",
        "⚖️",
        "Nothing to compare yet",
        "Screen at least two candidates to unlock the comparison view.",
    ),
}

current_step = st.session_state["current_step"]
subtitle, icon, empty_title, empty_desc = _STEP_COPY[current_step]

page_header(
    eyebrow=f"Step {[s['key'] for s in STEPS].index(current_step) + 1} of {len(STEPS)}",
    title=_STEP_LABELS[current_step],
    subtitle=subtitle,
)
disclaimer_banner()
empty_state(icon=icon, title=empty_title, description=empty_desc)
