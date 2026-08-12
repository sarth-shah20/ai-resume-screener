"""Candidates step: upload resumes, validate them, and build the roster."""

from __future__ import annotations

import uuid

import streamlit as st

from app.components.badges import badge_html
from app.services.screening_client import get_client
from app.state import candidate_label

_UPLOADER_KEY = "candidates_uploader_files"


def _existing_filenames() -> set[str]:
    return {c["filename"] for c in st.session_state["candidates"]}


def _process_uploads() -> None:
    files = st.session_state.get(_UPLOADER_KEY) or []
    client = get_client()
    already = _existing_filenames()

    for file in files:
        if file.name in already:
            continue
        try:
            parsed = client.parse_resume(file.getvalue(), file.name)
        except ValueError as exc:
            st.session_state["candidates"].append(
                {
                    "id": str(uuid.uuid4()),
                    "filename": file.name,
                    "display_name": file.name,
                    "resume_text": None,
                    "profile_key": None,
                    "status": "error",
                    "error_message": str(exc),
                }
            )
        else:
            st.session_state["candidates"].append(
                {
                    "id": str(uuid.uuid4()),
                    "filename": file.name,
                    "display_name": parsed["display_name"],
                    "resume_text": parsed["resume_text"],
                    "profile_key": parsed.get("profile_key"),
                    "status": "parsed",
                    "error_message": None,
                }
            )
        already.add(file.name)


def _remove_candidate(candidate_id: str) -> None:
    st.session_state["candidates"] = [
        c for c in st.session_state["candidates"] if c["id"] != candidate_id
    ]


def _clear_all() -> None:
    st.session_state["candidates"] = []


def render() -> None:
    st.toggle(
        "Blind Review Mode",
        key="blind_review",
        help=(
            "Hides candidate names and filenames from this roster so screening "
            "can proceed without identity bias. Does not affect scoring."
        ),
    )

    st.file_uploader(
        "Upload resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key=_UPLOADER_KEY,
        label_visibility="collapsed",
    )

    st.button(
        "Process Uploads",
        key="candidates_process_btn",
        type="primary",
        on_click=_process_uploads,
        disabled=not st.session_state.get(_UPLOADER_KEY),
    )

    candidates = st.session_state["candidates"]
    if not candidates:
        return

    st.markdown(f"**{len(candidates)} candidate(s) in roster**")

    blind = st.session_state.get("blind_review", False)
    for position, candidate in enumerate(candidates, start=1):
        name = candidate_label(candidate, position, blind)
        badge = (
            badge_html("Parsed", "success")
            if candidate["status"] == "parsed"
            else badge_html("Error", "danger")
        )
        col_info, col_remove = st.columns([5, 1])
        with col_info:
            st.markdown(f"{badge}&nbsp;&nbsp;**{name}**", unsafe_allow_html=True)
            if candidate["status"] == "error":
                st.caption(f"⚠️ {candidate['error_message']}")
            elif not blind:
                st.caption(candidate["filename"])
        with col_remove:
            st.button(
                "Remove",
                key=f"remove_{candidate['id']}",
                on_click=_remove_candidate,
                args=(candidate["id"],),
                use_container_width=True,
            )

    st.button("Clear all", key="candidates_clear_btn", on_click=_clear_all)
