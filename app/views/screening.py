"""Screening step: run evidence-grounded analysis for each parsed candidate."""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from app.components.badges import badge_html
from app.components.states import empty_state
from app.services.screening_client import ScreeningClient, get_client
from app.state import candidate_label

_ANALYSIS_DELAY_SECONDS = 0.4  # deliberate, so per-candidate progress is visible


def _position_map() -> dict[str, int]:
    return {c["id"]: i + 1 for i, c in enumerate(st.session_state["candidates"])}


def _screened_ids() -> set[str]:
    return {r["candidate_id"] for r in st.session_state["screening_results"]}


def _run_screening(queue: list[dict[str, Any]], requirements: dict[str, Any], blind: bool) -> None:
    client = get_client()
    positions = _position_map()
    total = len(queue)
    progress = st.progress(0.0, text="Starting screening...")

    for index, candidate in enumerate(queue):
        label = candidate_label(candidate, positions[candidate["id"]], blind)
        progress.progress(index / total, text=f"Analyzing {label}...")
        time.sleep(_ANALYSIS_DELAY_SECONDS)
        _screen_one(client, candidate, requirements)

    progress.progress(1.0, text="Screening complete.")
    time.sleep(0.3)


def _screen_one(
    client: ScreeningClient, candidate: dict[str, Any], requirements: dict[str, Any]
) -> None:
    try:
        result = client.analyze_candidate(candidate, requirements)
    except ValueError as exc:
        st.session_state["screening_results"].append(
            {
                "candidate_id": candidate["id"],
                "display_name": candidate["display_name"],
                "status": "error",
                "error_message": str(exc),
                "overall_score": None,
                "category_scores": None,
                "recommendation": None,
                "confidence_label": None,
                "matches": None,
            }
        )
    else:
        st.session_state["screening_results"].append(
            {
                "candidate_id": candidate["id"],
                "display_name": candidate["display_name"],
                "status": "complete",
                "error_message": None,
                **result,
            }
        )


def _retry_candidate(candidate_id: str, requirements: dict[str, Any]) -> None:
    candidate = next(
        (c for c in st.session_state["candidates"] if c["id"] == candidate_id), None
    )
    if candidate is None:
        return
    st.session_state["screening_results"] = [
        r for r in st.session_state["screening_results"] if r["candidate_id"] != candidate_id
    ]
    client = get_client()
    _screen_one(client, candidate, requirements)


def _clear_results() -> None:
    st.session_state["screening_results"] = []


_CONFIDENCE_VARIANT = {"High": "success", "Medium": "warning", "Low": "danger"}


def _score_variant(confidence_label: str) -> str:
    """Badge color for a result, keyed off the same confidence tier the
    recommendation text uses (see scoring.recommendation_for) so the badge
    color and the recommendation next to it never contradict each other.
    """
    return _CONFIDENCE_VARIANT.get(confidence_label, "neutral")


def render() -> None:
    requirements = st.session_state.get("job_requirements")
    parsed_candidates = [c for c in st.session_state["candidates"] if c["status"] == "parsed"]

    if not requirements:
        empty_state(
            icon="📋",
            title="Complete Job Setup first",
            description="Extract requirements from a job description before screening candidates.",
        )
        return

    if not parsed_candidates:
        empty_state(
            icon="📄",
            title="No parsed candidates yet",
            description="Upload and process at least one resume in the Candidates step.",
        )
        return

    blind = st.session_state.get("blind_review", False)
    screened_ids = _screened_ids()
    queue = [c for c in parsed_candidates if c["id"] not in screened_ids]

    if queue:
        st.caption(f"{len(queue)} candidate(s) ready to screen.")
    run_clicked = st.button(
        "Run Screening",
        type="primary",
        disabled=not queue,
        key="run_screening_btn",
    )
    if run_clicked:
        _run_screening(queue, requirements, blind)

    results = st.session_state["screening_results"]
    if not results:
        return

    positions = _position_map()
    st.markdown(f"**{len(results)} result(s)**")

    for result in results:
        candidate = next(
            (c for c in st.session_state["candidates"] if c["id"] == result["candidate_id"]),
            None,
        )
        position = positions.get(result["candidate_id"], 0)
        label = (
            candidate_label(candidate, position, blind)
            if candidate
            else result["display_name"]
        )

        with st.container(border=True):
            if result["status"] == "error":
                st.markdown(f"{badge_html('Error', 'danger')}&nbsp;&nbsp;**{label}**", unsafe_allow_html=True)
                st.caption(f"⚠️ {result['error_message']}")
                st.button(
                    "Retry",
                    key=f"retry_{result['candidate_id']}",
                    on_click=_retry_candidate,
                    args=(result["candidate_id"], requirements),
                )
                continue

            score = result["overall_score"]
            variant = _score_variant(result["confidence_label"])
            col_label, col_score = st.columns([4, 1])
            with col_label:
                st.markdown(f"**{label}**")
                st.caption(result["recommendation"])
            with col_score:
                st.markdown(
                    f'<div style="text-align:right;">{badge_html(f"{score}/100", variant)}</div>',
                    unsafe_allow_html=True,
                )
            st.caption(f"Confidence: {result['confidence_label']}")

    st.button("Clear results", key="screening_clear_btn", on_click=_clear_results)
