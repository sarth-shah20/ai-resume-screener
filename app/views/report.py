"""Complete persisted candidate report."""

from __future__ import annotations

import streamlit as st

from app.components.badges import badge_html
from app.components.states import empty_state
from app.services.screening_client import BackendRequestError, BackendUnavailable, get_client
from app.state import navigate
from app.views import explain

_STATUS_VARIANT = {
    "demonstrated": "success",
    "partial": "warning",
    "claimed": "primary",
    "missing": "danger",
    "unproven": "neutral",
}


def render() -> None:
    job_id = st.session_state.get("selected_job_id")
    candidate_id = st.session_state.get("selected_candidate_id")
    if not job_id or not candidate_id:
        empty_state(
            "📊",
            "No candidate selected",
            "Open a candidate from the dashboard or complete a new analysis.",
        )
        return

    client = get_client()
    try:
        job_payload = client.list_candidates(job_id)
        report = client.get_candidate(job_id, candidate_id)
    except (BackendUnavailable, BackendRequestError) as exc:
        st.error(str(exc), icon="🚫")
        return

    if st.button("← Back to dashboard"):
        navigate("dashboard")
        st.rerun()

    candidates = job_payload["candidates"]
    labels = {
        item["candidate_id"]: item["source_name"]
        for item in candidates
    }
    selected = st.selectbox(
        "Candidate",
        options=list(labels),
        index=list(labels).index(candidate_id),
        format_func=lambda value: labels[value],
    )
    if selected != candidate_id:
        navigate("report", job_id, selected)
        st.rerun()

    st.markdown(f"### {report['source_name']}")
    st.caption(f"Against **{job_payload['job']['title']}**")
    verified, potential, band, github = st.columns(4)
    verified.metric("Verified score", f"{report['verified_score']}/100")
    potential.metric("Potential score", f"{report['potential_score']}/100")
    band.metric("Fit band", report["fit_band"].replace("_", " ").title())
    github.metric("GitHub projects", len(report["github_projects"]))
    st.info(report["summary"])

    evidence_tab, why_tab, what_if_tab, compare_tab = st.tabs(
        ["Evidence", "Why this score", "What-if", "Compare"]
    )
    with evidence_tab:
        _render_evidence(job_payload, report)
    with why_tab:
        explain.render_attribution(job_payload["job"], report)
    with what_if_tab:
        explain.render_what_if(job_payload["job"], report, f"{job_id}_{candidate_id}")
    with compare_tab:
        explain.render_compare(job_payload, job_id, report)


def _render_evidence(job_payload: dict, report: dict) -> None:
    requirement_by_id = {
        item["id"]: item for item in job_payload["job"]["requirements"]
    }
    st.markdown("### Requirement evidence")
    checked = [
        match["evidence_grounded"]
        for match in report["requirement_matches"]
        if match.get("evidence_grounded") is not None
    ]
    if checked:
        st.caption(
            f"Evidence quotes found in the resume text: **{sum(checked)} of {len(checked)}**. "
            "Quotes are checked in code, independently of the model."
        )
    for match in report["requirement_matches"]:
        requirement = requirement_by_id.get(match["requirement_id"], {})
        title = requirement.get("description", match["requirement_id"])
        variant = _STATUS_VARIANT.get(match["status"], "neutral")
        with st.expander(
            f"{match['status'].replace('_', ' ').title()} · {title}",
            expanded=match["status"] in {"partial", "claimed", "missing", "unproven"},
        ):
            st.markdown(
                badge_html(match["status"].replace("_", " ").title(), variant),
                unsafe_allow_html=True,
            )
            st.caption(f"Confidence: {match['confidence'].title()}")
            if match.get("evidence"):
                st.markdown(f"> {match['evidence']}")
                grounded = match.get("evidence_grounded")
                if grounded is not None:
                    st.markdown(
                        badge_html("Quote found in resume", "success")
                        if grounded
                        else badge_html("Quote not found in resume", "danger"),
                        unsafe_allow_html=True,
                    )
                if match.get("evidence_section"):
                    st.caption(f"Source section: {match['evidence_section']}")
            else:
                st.caption("No supporting evidence excerpt.")
            st.write(match["explanation"])

    left, right = st.columns(2)
    with left:
        st.markdown("### Gaps and uncertainty")
        if report["gaps"]:
            for gap in report["gaps"]:
                st.markdown(f"- {gap}")
        else:
            st.caption("No gaps were returned.")
    with right:
        st.markdown("### Interview questions")
        if report["interview_questions"]:
            for index, question in enumerate(report["interview_questions"], start=1):
                st.markdown(f"{index}. {question}")
        else:
            st.caption("No interview questions were returned.")

    st.markdown("### GitHub verification")
    if not report["github_projects"]:
        st.caption("No canonical public GitHub repository was found or verified.")
    for project in report["github_projects"]:
        repository = project["repository"]
        name = repository.get("name") or repository.get("url") or "Repository"
        with st.expander(f"{project['status'].replace('_', ' ').title()} · {name}"):
            if repository.get("description"):
                st.write(repository["description"])
            if repository.get("primary_language"):
                st.caption(f"Primary language: {repository['primary_language']}")
            st.markdown("**Supported claims**")
            for claim in project["supported_claims"]:
                st.markdown(f"- {claim}")
            if project["unsupported_claims"]:
                st.markdown("**Unsupported claims**")
                for claim in project["unsupported_claims"]:
                    st.markdown(f"- {claim}")
            st.markdown("**Evidence**")
            for evidence in project["evidence"]:
                st.markdown(f"- **{evidence['source']}** — {evidence['finding']}")
            for limitation in project["limitations"]:
                st.caption(f"Limitation: {limitation}")

    for warning in report["warnings"]:
        st.warning(warning)
