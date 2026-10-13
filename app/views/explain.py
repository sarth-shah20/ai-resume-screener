"""Explainability tabs for the candidate report.

Everything here is computed deterministically from the persisted report with
the same scoring code the backend uses. No model calls are made.
"""

from __future__ import annotations

import json
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from app.services.screening_client import BackendRequestError, BackendUnavailable, get_client
from app.theme import COLORS
from src.models.schemas import EvidenceStatus, JobRequirement, RequirementMatch
from src.services.explain_service import (
    Contribution,
    contrast,
    next_band_target,
    score_breakdown,
    shortest_path,
)
from src.services.scoring_service import (
    BAND_THRESHOLDS,
    CATEGORY_WEIGHTS,
    POTENTIAL,
    VERIFIED,
    score_statuses,
)

_STATUS_COLOR = {
    "demonstrated": COLORS["success"],
    "partial": COLORS["warning"],
    "claimed": COLORS["primary"],
    "missing": COLORS["danger"],
    "unproven": "#C9CBD6",
}
_PARTS = {
    "Verified by evidence": COLORS["success"],
    "Claimed, not yet verified": COLORS["warning"],
    "Not evidenced": "#D9DBE3",
}
_STATUSES = [status.value for status in EvidenceStatus]


def _title(value: str) -> str:
    return value.replace("_", " ").title()


def _short(text: str, limit: int = 58) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _labels(requirements: list[JobRequirement]) -> dict[str, str]:
    """Short, unique axis labels keyed by requirement id."""
    labels: dict[str, str] = {}
    for item in requirements:
        label = _short(item.description)
        labels[item.id] = f"{label} ({item.id})" if label in labels.values() else label
    return labels


def _parse(job: dict[str, Any], report: dict[str, Any]) -> tuple[list[JobRequirement], list[RequirementMatch]]:
    return (
        [JobRequirement.model_validate(item) for item in job["requirements"]],
        [RequirementMatch.model_validate(item) for item in report["requirement_matches"]],
    )


def render_attribution(job: dict[str, Any], report: dict[str, Any]) -> None:
    requirements, matches = _parse(job, report)
    breakdown = score_breakdown(requirements, matches)
    labels = _labels(requirements)
    verified = sum(item.verified_points for item in breakdown)
    uplift = sum(item.uplift_points for item in breakdown)
    lost = sum(item.lost_points for item in breakdown)

    st.markdown("### Where the score comes from")
    st.caption(
        "Each bar is one job requirement and its exact share of the 100 points. "
        "The score is a weighted sum, so this attribution is exact rather than an estimate."
    )
    first, second, third = st.columns(3)
    first.metric("Verified by evidence", f"{verified:.1f} pts")
    second.metric("Claimed, not yet verified", f"{uplift:.1f} pts")
    third.metric("Not evidenced", f"{lost:.1f} pts")

    ordered = sorted(breakdown, key=lambda item: item.max_points - item.verified_points, reverse=True)
    rows = [
        {
            "Requirement": labels[item.requirement_id],
            "Part": part,
            "Points": round(points, 1),
            "Status": _title(item.status.value),
            "Category": _title(item.category),
            "order": index,
        }
        for item in ordered
        for index, (part, points) in enumerate(
            zip(_PARTS, (item.verified_points, item.uplift_points, item.lost_points), strict=True)
        )
    ]
    chart = (
        alt.Chart(pd.DataFrame(rows))
        .mark_bar()
        .encode(
            x=alt.X("Points:Q", stack="zero", title="Points out of 100"),
            y=alt.Y(
                "Requirement:N",
                sort=[labels[item.requirement_id] for item in ordered],
                title=None,
                axis=alt.Axis(labelLimit=340),
            ),
            color=alt.Color(
                "Part:N",
                scale=alt.Scale(domain=list(_PARTS), range=list(_PARTS.values())),
                legend=alt.Legend(orient="top", title=None),
            ),
            order=alt.Order("order:Q"),
            tooltip=["Requirement", "Status", "Category", "Part", "Points"],
        )
        .properties(height=max(160, 30 * len(ordered)))
    )
    st.altair_chart(chart, width="stretch")
    st.caption(
        f"Green segments add up to the verified score of **{report['verified_score']}**; "
        f"green plus amber gives the potential score of **{report['potential_score']}**."
    )

    st.markdown("#### By category")
    categories: dict[str, list[Contribution]] = {}
    for item in breakdown:
        categories.setdefault(item.category, []).append(item)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Category": _title(category),
                    "Requirements": len(items),
                    "Verified points": round(sum(i.verified_points for i in items), 1),
                    "Points available": round(sum(i.max_points for i in items), 1),
                }
                for category, items in categories.items()
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    _methodology(job, report, breakdown)


def _methodology(job: dict[str, Any], report: dict[str, Any], breakdown: list[Contribution]) -> None:
    with st.expander("How this score is calculated"):
        st.markdown(
            "The language model only classifies each requirement and quotes evidence. "
            "The score itself is calculated in application code:"
        )
        st.code(
            "requirement points = category weight x (requirement weight / total weight in category)\n"
            "                     x status factor, rescaled so the categories present total 100",
            language=None,
        )
        weights, factors = st.columns(2)
        weights.dataframe(
            pd.DataFrame(
                [{"Category": _title(category.value), "Weight": weight} for category, weight in CATEGORY_WEIGHTS.items()]
            ),
            hide_index=True,
            width="stretch",
        )
        factors.dataframe(
            pd.DataFrame(
                [
                    {"Status": _title(status.value), "Verified factor": VERIFIED[status], "Potential factor": POTENTIAL[status]}
                    for status in EvidenceStatus
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        bands = ", ".join(f"{_title(band)} from {minimum}" for band, minimum in BAND_THRESHOLDS.items())
        st.caption(f"Fit bands use the verified score: {bands}; below that, Limited Evidence.")

    audit = {
        "job_title": job["title"],
        "candidate": report["source_name"],
        "verified_score": report["verified_score"],
        "potential_score": report["potential_score"],
        "fit_band": report["fit_band"],
        "category_weights": {category.value: weight for category, weight in CATEGORY_WEIGHTS.items()},
        "status_factors": {
            status.value: {"verified": VERIFIED[status], "potential": POTENTIAL[status]} for status in EvidenceStatus
        },
        "band_thresholds": BAND_THRESHOLDS,
        "attribution": [item.model_dump(mode="json") for item in breakdown],
        "requirement_matches": report["requirement_matches"],
        "warnings": report["warnings"],
    }
    st.download_button(
        "Download audit report (JSON)",
        data=json.dumps(audit, indent=2),
        file_name=f"audit_{report['candidate_id']}.json",
        mime="application/json",
    )


def render_what_if(job: dict[str, Any], report: dict[str, Any], scope: str) -> None:
    requirements, matches = _parse(job, report)
    current = {match.requirement_id: match.status for match in matches}
    base = {item.id: current.get(item.id, EvidenceStatus.UNPROVEN).value for item in requirements}
    keys = {item.id: f"whatif_{scope}_{item.id}" for item in requirements}

    def apply(statuses: dict[str, str]) -> None:
        for requirement_id, status in statuses.items():
            st.session_state[keys[requirement_id]] = status

    st.markdown("### What would change this score?")
    st.caption(
        "Change the status of any requirement to see the effect immediately. "
        "This is a simulation; the saved report is not altered."
    )

    target = next_band_target(report["verified_score"])
    if target is None:
        st.success("This candidate is already in the highest fit band.")
    else:
        band, minimum = target
        steps = shortest_path(requirements, matches, minimum)
        with st.container(border=True):
            st.markdown(f"**Fewest changes to reach {_title(band)} ({minimum}+)**")
            if not steps:
                st.caption("No combination of requirements reaches this band.")
            for index, step in enumerate(steps, start=1):
                st.markdown(
                    f"{index}. **{_short(step.description, 90)}** — now {_title(step.current_status.value)}; "
                    f"if demonstrated: **+{step.gain:.1f} pts**, score {step.score_after}"
                )
            if steps:
                st.caption("These are the highest-value points to confirm at interview.")
                st.button(
                    "Apply to simulator",
                    on_click=apply,
                    args=({step.requirement_id: "demonstrated" for step in steps},),
                )

    st.button("Reset simulator", on_click=apply, args=(base,))
    columns = st.columns(2)
    simulated: dict[str, EvidenceStatus] = {}
    for index, item in enumerate(requirements):
        st.session_state.setdefault(keys[item.id], base[item.id])
        choice = columns[index % 2].selectbox(
            _short(item.description, 70),
            options=_STATUSES,
            format_func=_title,
            key=keys[item.id],
            help=f"{_title(item.category.value)} · saved status: {_title(base[item.id])}",
        )
        simulated[item.id] = EvidenceStatus(choice)

    verified, potential, band = score_statuses(requirements, simulated)
    first, second, third = st.columns(3)
    first.metric("Simulated verified score", f"{verified}/100", delta=verified - report["verified_score"])
    second.metric("Simulated potential score", f"{potential}/100", delta=potential - report["potential_score"])
    third.metric("Simulated fit band", _title(band))

    changed = [item for item in requirements if simulated[item.id].value != base[item.id]]
    if changed:
        st.markdown("**Changes applied**")
        for item in changed:
            st.markdown(
                f"- {_short(item.description, 90)}: {_title(base[item.id])} → {_title(simulated[item.id].value)}"
            )


def render_compare(job_payload: dict[str, Any], job_id: str, report: dict[str, Any]) -> None:
    job = job_payload["job"]
    st.markdown("### Compare candidates")
    if len(job_payload["candidates"]) < 2:
        st.info("Analyze two or more resumes in the same screening run to compare candidates.")
        return

    client = get_client()
    try:
        reports = {
            item["candidate_id"]: report
            if item["candidate_id"] == report["candidate_id"]
            else client.get_candidate(job_id, item["candidate_id"])
            for item in job_payload["candidates"]
        }
    except (BackendUnavailable, BackendRequestError) as exc:
        st.error(str(exc))
        return

    requirements = [JobRequirement.model_validate(item) for item in job["requirements"]]
    labels = _labels(requirements)
    breakdowns = {
        candidate_id: score_breakdown(requirements, _parse(job, item)[1]) for candidate_id, item in reports.items()
    }
    ranked = sorted(reports.values(), key=lambda item: item["verified_score"], reverse=True)

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Candidate": item["source_name"],
                    "Verified": item["verified_score"],
                    "Potential": item["potential_score"],
                    "Fit band": _title(item["fit_band"]),
                }
                for item in ranked
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    rows = [
        {
            "Requirement": labels[item.requirement_id],
            "Candidate": candidate["source_name"],
            "Status": _title(item.status.value),
            "Verified points": round(item.verified_points, 1),
            "Points available": round(item.max_points, 1),
        }
        for candidate in ranked
        for item in breakdowns[candidate["candidate_id"]]
    ]
    heatmap = (
        alt.Chart(pd.DataFrame(rows))
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=alt.X(
                "Candidate:N",
                sort=[item["source_name"] for item in ranked],
                title=None,
                axis=alt.Axis(orient="top", labelAngle=0, labelLimit=180),
            ),
            y=alt.Y(
                "Requirement:N",
                sort=[labels[item.id] for item in requirements],
                title=None,
                axis=alt.Axis(labelLimit=340),
            ),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(
                    domain=[_title(status) for status in _STATUS_COLOR], range=list(_STATUS_COLOR.values())
                ),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["Candidate", "Requirement", "Status", "Verified points", "Points available"],
        )
        .properties(height=max(160, 30 * len(requirements)))
    )
    st.altair_chart(heatmap, width="stretch")

    others = [item for item in ranked if item["candidate_id"] != report["candidate_id"]]
    names = {item["candidate_id"]: item["source_name"] for item in others}
    other_id = st.selectbox(
        f"Explain the difference between {report['source_name']} and",
        options=list(names),
        format_func=lambda value: names[value],
    )
    other = reports[other_id]
    differences = contrast(breakdowns[report["candidate_id"]], breakdowns[other_id])
    gap = report["verified_score"] - other["verified_score"]
    if gap:
        leader, trailer = (report, other) if gap > 0 else (other, report)
        st.markdown(
            f"**{leader['source_name']}** is {abs(gap)} verified points ahead of **{trailer['source_name']}**. "
            "The requirements below account for the difference."
        )
    else:
        st.markdown("Both candidates have the same verified score.")
    if not differences:
        st.caption("Both candidates have the same status on every requirement.")
    for mine, theirs, delta in differences:
        st.markdown(
            f"- **{_short(mine.description, 90)}** — {report['source_name']}: {_title(mine.status.value)}, "
            f"{other['source_name']}: {_title(theirs.status.value)} "
            f"(**+{abs(delta):.1f} pts** for {(report if delta > 0 else other)['source_name']})"
        )
