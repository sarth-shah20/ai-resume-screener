"""Persisted job and candidate dashboard."""

from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from app.components.badges import badge_html
from app.components.states import empty_state
from app.services.screening_client import BackendRequestError, BackendUnavailable, get_client
from app.state import navigate


def _date(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y · %H:%M")
    except ValueError:
        return value


def render() -> None:
    client = get_client()
    try:
        jobs = client.list_jobs()["jobs"]
    except (BackendUnavailable, BackendRequestError) as exc:
        st.error(str(exc), icon="🚫")
        return

    col_title, col_action = st.columns([4, 1])
    with col_title:
        st.markdown(f"### {len(jobs)} saved job analysis{'es' if len(jobs) != 1 else ''}")
    with col_action:
        if st.button("New analysis", type="primary", use_container_width=True):
            navigate("new_analysis")
            st.rerun()

    if not jobs:
        empty_state(
            "📂",
            "No saved analyses",
            "Run your first screening to create a job and candidate reports.",
        )
        return

    for job in jobs:
        with st.container(border=True):
            left, verified, potential, action = st.columns([4, 1, 1, 1.2])
            with left:
                st.markdown(f"#### {job['title']}")
                st.caption(
                    f"{_date(job['latest_analysis_at'])} · "
                    f"{job['candidate_count']} candidate(s)"
                )
            with verified:
                st.metric("Avg. verified", f"{job['average_verified_score']:.0f}")
            with potential:
                st.metric("Avg. potential", f"{job['average_potential_score']:.0f}")
            with action:
                if st.button(
                    "View candidates",
                    key=f"job_{job['job_id']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_job_id"] = job["job_id"]

            if st.session_state.get("selected_job_id") == job["job_id"]:
                _candidate_list(client, job["job_id"])


def _candidate_list(client: object, job_id: str) -> None:
    try:
        payload = client.list_candidates(job_id)
    except (BackendUnavailable, BackendRequestError) as exc:
        st.error(str(exc))
        return

    with st.expander("Job description and extracted requirements"):
        st.write(payload["raw_description"])
        for requirement in payload["job"]["requirements"]:
            priority = requirement["priority"].replace("_", " ").title()
            st.markdown(
                f"- **{requirement['description']}** · "
                f"{requirement['category'].replace('_', ' ').title()} · {priority}"
            )

    st.markdown("**Candidates — latest first**")
    for candidate in payload["candidates"]:
        variant = (
            "success"
            if candidate["fit_band"] == "strong_fit"
            else "warning"
            if candidate["fit_band"] == "moderate_fit"
            else "neutral"
        )
        label, scores, action = st.columns([4, 2, 1.3])
        with label:
            st.markdown(
                f"{badge_html(candidate['fit_band'].replace('_', ' ').title(), variant)} "
                f"<strong>{escape(candidate['source_name'])}</strong>",
                unsafe_allow_html=True,
            )
            st.caption(candidate["summary"])
        with scores:
            st.caption(
                f"Verified **{candidate['verified_score']}** · "
                f"Potential **{candidate['potential_score']}** · "
                f"GitHub **{candidate['github_project_count']}**"
            )
        with action:
            if st.button(
                "Open report",
                key=f"candidate_{job_id}_{candidate['candidate_id']}",
                use_container_width=True,
            ):
                navigate("report", job_id, candidate["candidate_id"])
                st.rerun()
