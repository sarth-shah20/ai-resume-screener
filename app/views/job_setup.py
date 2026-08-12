"""Job Setup step: paste/load a job description and extract requirements."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import streamlit as st

from app.components.badges import badge_row
from app.components.layout import card
from app.components.states import error_state
from app.services import fixtures
from app.services.screening_client import get_client

_DRAFT_KEY = "job_setup_draft_text"
_SAMPLE_SELECT_KEY = "job_setup_sample_choice"
_ERROR_KEY = "job_setup_error"

# Overall scoring-category weights as documented in plan.md #5. Shown here
# purely as informational copy -- the deterministic score itself is
# calculated by src/services/scoring_service.py, never by the UI.
_CATEGORY_WEIGHT = {
    "must_have_skills": 40,
    "experience_requirements": 25,
    "nice_to_have_skills": 15,
    "education_requirements": 10,
    "domain_requirements": 10,
}


def _load_sample_into_draft() -> None:
    samples = fixtures.list_sample_job_descriptions()
    choice = st.session_state.get(_SAMPLE_SELECT_KEY)
    if choice and choice in samples:
        st.session_state[_DRAFT_KEY] = Path(samples[choice]).read_text(encoding="utf-8")
        st.session_state[_ERROR_KEY] = None


def _clear_job() -> None:
    st.session_state["job"] = None
    st.session_state["job_requirements"] = None
    st.session_state[_DRAFT_KEY] = ""
    st.session_state[_ERROR_KEY] = None


def _run_extraction() -> None:
    draft = st.session_state.get(_DRAFT_KEY, "")
    if not draft.strip():
        st.session_state[_ERROR_KEY] = (
            "Paste or load a job description before extracting requirements."
        )
        return
    try:
        requirements = get_client().extract_requirements(draft)
    except ValueError as exc:
        st.session_state[_ERROR_KEY] = str(exc)
        return
    st.session_state[_ERROR_KEY] = None
    st.session_state["job"] = {"raw_description": draft, "title": requirements["job_title"]}
    st.session_state["job_requirements"] = requirements


def _requirement_card(
    key: str,
    title: str,
    items: list[dict[str, Any]],
    render_labels: Callable[[dict[str, Any]], str],
    variant: str,
) -> None:
    weight = _CATEGORY_WEIGHT.get(key)
    with card():
        heading = f"**{title}**"
        if weight is not None:
            heading += f"  ·  {weight}% of score"
        st.markdown(heading)
        badge_row([render_labels(item) for item in items], variant=variant)


def render() -> None:
    samples = fixtures.list_sample_job_descriptions()

    if samples:
        col_select, col_button = st.columns([3, 1])
        with col_select:
            st.selectbox(
                "Load a sample job description",
                options=list(samples.keys()),
                key=_SAMPLE_SELECT_KEY,
                label_visibility="collapsed",
                placeholder="Load a sample job description...",
            )
        with col_button:
            st.button(
                "Load sample",
                key="job_setup_load_sample_btn",
                on_click=_load_sample_into_draft,
                use_container_width=True,
                disabled=not st.session_state.get(_SAMPLE_SELECT_KEY),
            )

    st.text_area(
        "Job description",
        key=_DRAFT_KEY,
        height=220,
        placeholder="Paste the job description here...",
        label_visibility="collapsed",
        on_change=lambda: st.session_state.update({_ERROR_KEY: None}),
    )

    st.button(
        "Extract Requirements",
        key="job_setup_extract_btn",
        type="primary",
        on_click=_run_extraction,
    )

    if st.session_state.get(_ERROR_KEY):
        error_state(st.session_state[_ERROR_KEY])

    requirements = st.session_state.get("job_requirements")
    if not requirements:
        return

    st.success(f"Requirements extracted for **{requirements['job_title']}**", icon="✅")

    _requirement_card(
        "must_have_skills",
        "Must-have skills",
        requirements["must_have_skills"],
        lambda item: item["name"],
        variant="primary",
    )
    _requirement_card(
        "nice_to_have_skills",
        "Nice-to-have skills",
        requirements["nice_to_have_skills"],
        lambda item: item["name"],
        variant="neutral",
    )
    _requirement_card(
        "experience_requirements",
        "Experience",
        requirements["experience_requirements"],
        lambda item: f"{item['name']} ({item['minimum_years']}+ yrs)",
        variant="warning",
    )
    _requirement_card(
        "education_requirements",
        "Education",
        requirements["education_requirements"],
        lambda item: item["name"],
        variant="neutral",
    )
    _requirement_card(
        "domain_requirements",
        "Domain relevance",
        requirements["domain_requirements"],
        lambda item: item["name"],
        variant="neutral",
    )

    st.button("Start over", key="job_setup_reset_btn", on_click=_clear_job)
