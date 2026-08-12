"""Entry point for the recruiter screening UI.

Run with: streamlit run app/main.py

This is a single-page wizard rather than Streamlit's native multipage
``pages/`` convention: the sidebar stepper needs to reflect data-driven
completion state (has a JD been extracted? have candidates been screened?)
rather than a static file list, and view state needs to be shared across
steps via ``st.session_state``. Each step's content lives in
``app.views.<step>`` and is dispatched below; steps not yet built fall back
to a placeholder empty state.
"""

from __future__ import annotations

import streamlit as st

from app.components.layout import disclaimer_banner, page_header
from app.components.nav import render_sidebar
from app.components.states import empty_state
from app.state import STEPS, init_session_state
from app.theme import apply_theme
from app.views import candidates, job_setup, screening

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

_STEP_SUBTITLE = {
    "job_setup": (
        "Paste a job description and let the assistant extract structured, "
        "weighted requirements."
    ),
    "candidates": "Upload PDF or DOCX resumes for the candidates you want screened.",
    "screening": "Run evidence-grounded analysis against the extracted requirements.",
    "report": "Review each candidate's score, matched evidence, and gaps.",
    "gaps": "See uncertainty-driven interview questions generated from evidence gaps.",
    "compare": "Compare candidates side by side once more than one has been screened.",
}

# icon, title, description -- shown for steps that don't have a real view yet.
_EMPTY_STATE_COPY = {
    "report": (
        "📊",
        "No results yet",
        "Results will appear here once screening has run.",
    ),
    "gaps": (
        "💬",
        "No interview questions yet",
        "Gap-based questions are generated after screening completes.",
    ),
    "compare": (
        "⚖️",
        "Nothing to compare yet",
        "Screen at least two candidates to unlock the comparison view.",
    ),
}

_VIEW_RENDERERS = {
    "job_setup": job_setup.render,
    "candidates": candidates.render,
    "screening": screening.render,
}

current_step = st.session_state["current_step"]

page_header(
    eyebrow=f"Step {[s['key'] for s in STEPS].index(current_step) + 1} of {len(STEPS)}",
    title=_STEP_LABELS[current_step],
    subtitle=_STEP_SUBTITLE[current_step],
)
disclaimer_banner()

if current_step in _VIEW_RENDERERS:
    _VIEW_RENDERERS[current_step]()
else:
    icon, empty_title, empty_desc = _EMPTY_STATE_COPY[current_step]
    empty_state(icon=icon, title=empty_title, description=empty_desc)
