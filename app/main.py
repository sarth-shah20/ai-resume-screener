"""Streamlit recruiter dashboard.

Run with: streamlit run app/main.py
"""

from __future__ import annotations

import streamlit as st

from app.components.layout import disclaimer_banner, page_header
from app.components.nav import render_sidebar
from app.state import init_session_state
from app.theme import apply_theme
from app.views import analysis, dashboard, report

st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_session_state()
render_sidebar()

page = st.session_state["current_page"]

if page == "new_analysis":
    page_header(
        eyebrow="New screening",
        title="Analyze candidates",
        subtitle=(
            "Submit one job description and a configured batch of resumes. Requirement "
            "extraction, evidence analysis, scoring, GitHub verification, and "
            "persistence run together."
        ),
    )
    disclaimer_banner()
    analysis.render()
elif page == "report":
    page_header(
        eyebrow="Candidate report",
        title="Evidence-based assessment",
        subtitle="Review scores, evidence, uncertainty, GitHub checks, and interview questions.",
    )
    disclaimer_banner()
    report.render()
else:
    page_header(
        eyebrow="Recruiter workspace",
        title="Screening dashboard",
        subtitle="Browse saved job analyses and open complete candidate reports.",
    )
    disclaimer_banner()
    dashboard.render()
