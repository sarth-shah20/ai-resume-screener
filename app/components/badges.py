"""Reusable pill/badge rendering, backed by the .badge CSS classes in theme.py."""

from __future__ import annotations

import streamlit as st

_VARIANT_CLASS = {
    "success": "badge-success",
    "warning": "badge-warning",
    "danger": "badge-danger",
    "neutral": "badge-neutral",
    "primary": "badge-primary",
}


def badge_html(text: str, variant: str = "neutral") -> str:
    """Return the HTML for a single pill badge (for composing into a larger markdown string)."""
    css_class = _VARIANT_CLASS.get(variant, "badge-neutral")
    return f'<span class="badge {css_class}">{text}</span>'


def badge_row(items: list[str], variant: str = "neutral") -> None:
    """Render a wrapping row of pill badges in one markdown call."""
    if not items:
        st.caption("None specified")
        return
    html = " ".join(badge_html(item, variant) for item in items)
    st.markdown(f'<div style="line-height: 2.1;">{html}</div>', unsafe_allow_html=True)
