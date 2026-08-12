"""Shared page-layout primitives: header, disclaimer banner, card surface."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def page_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Render the consistent page-title block used at the top of every view."""
    st.markdown(f'<div class="page-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def disclaimer_banner() -> None:
    st.markdown(
        '<div class="disclaimer-banner">'
        "<span>&#9888;&#65039;</span>"
        "<span>This assistant supports recruiter review. It must not be used "
        "as the sole basis for employment decisions &mdash; a human reviewer "
        "makes the final call on every candidate.</span>"
        "</div>",
        unsafe_allow_html=True,
    )


@contextmanager
def card() -> Iterator[DeltaGenerator]:
    """Context manager that wraps its content in a bordered card surface.

    Uses Streamlit's native bordered container rather than raw HTML div
    open/close tags split across ``st.markdown`` calls -- Streamlit renders
    each markdown call as an isolated fragment, so an unclosed tag in one
    call never actually wraps widgets rendered by later calls.

    Usage:
        with card():
            st.write("content")
    """
    with st.container(border=True) as container:
        yield container
