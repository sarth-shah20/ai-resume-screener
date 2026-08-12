"""Design-system CSS for the recruiter screening UI.

Streamlit's ``[theme]`` section in ``.streamlit/config.toml`` sets the base
palette (primary/background/text colors, font). This module layers on the
structural CSS that config.toml cannot express: card surfaces, the sidebar
stepper, badges, and spacing rules that make the app read as one coherent
product instead of a stack of default Streamlit widgets.
"""

from __future__ import annotations

import streamlit as st

# Design tokens shared with component modules so badge/card colors stay in
# sync with this stylesheet instead of being re-guessed per component.
COLORS: dict[str, str] = {
    "primary": "#4F46E5",
    "primary_soft": "#EEF0FD",
    "success": "#15803D",
    "success_soft": "#EAF7EE",
    "warning": "#B45309",
    "warning_soft": "#FDF3E7",
    "danger": "#B91C1C",
    "danger_soft": "#FBEAEA",
    "neutral": "#5B5F6E",
    "neutral_soft": "#F0F1F5",
    "border": "#E4E5EC",
    "text": "#1A1D29",
    "text_muted": "#6B6F7D",
}

_CSS = """
<style>
#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1080px;
}

[data-testid="stSidebar"] {
    border-right: 1px solid %(border)s;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

h1, h2, h3 {
    letter-spacing: -0.01em;
}

/* App brand mark in the sidebar */
.brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1.75rem;
}
.brand-mark {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: %(primary)s;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.05rem;
    flex-shrink: 0;
}
.brand-text .brand-title {
    font-weight: 700;
    font-size: 1.02rem;
    color: %(text)s;
    line-height: 1.2;
}
.brand-text .brand-subtitle {
    font-size: 0.74rem;
    color: %(text_muted)s;
    line-height: 1.2;
}

/* Sidebar step nav buttons get their current/upcoming distinction from
   Streamlit's native primary/secondary button styling (see .stButton below);
   this just tightens their spacing so the list reads as one control. */
[data-testid="stSidebar"] .stButton {
    margin-bottom: 0.15rem;
}
[data-testid="stSidebar"] .stButton > button {
    text-align: left;
    justify-content: flex-start;
}

/* Native bordered containers (st.container(border=True)) act as our card
   surface; round the corners a touch beyond Streamlit's default. */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
}

/* Page header */
.page-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.72rem;
    font-weight: 700;
    color: %(primary)s;
    margin-bottom: 0.3rem;
}
.page-subtitle {
    color: %(text_muted)s;
    font-size: 0.95rem;
    margin-top: -0.6rem;
    margin-bottom: 1.25rem;
}

/* Disclaimer banner */
.disclaimer-banner {
    display: flex;
    gap: 0.6rem;
    align-items: flex-start;
    background: %(warning_soft)s;
    border: 1px solid #F0DCB8;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    font-size: 0.82rem;
    color: %(warning)s;
    margin-bottom: 1.25rem;
}

/* Status badges (matched / partial / missing / unproven) */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 600;
    white-space: nowrap;
}
.badge-success { background: %(success_soft)s; color: %(success)s; }
.badge-warning { background: %(warning_soft)s; color: %(warning)s; }
.badge-danger  { background: %(danger_soft)s;  color: %(danger)s; }
.badge-neutral { background: %(neutral_soft)s; color: %(neutral)s; }
.badge-primary { background: %(primary_soft)s; color: %(primary)s; }

/* Empty / error / success inline states */
.state-panel {
    text-align: center;
    padding: 2.75rem 1.5rem;
    border: 1px dashed %(border)s;
    border-radius: 12px;
    background: %(neutral_soft)s;
}
.state-panel .state-icon {
    font-size: 2rem;
    margin-bottom: 0.6rem;
}
.state-panel .state-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: %(text)s;
    margin-bottom: 0.3rem;
}
.state-panel .state-desc {
    color: %(text_muted)s;
    font-size: 0.88rem;
    max-width: 440px;
    margin: 0 auto;
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}
.stButton > button[kind="primary"] {
    background: %(primary)s;
    border-color: %(primary)s;
}
</style>
"""


def apply_theme() -> None:
    """Inject the app's structural CSS. Call once near the top of main.py."""
    st.markdown(_CSS % COLORS, unsafe_allow_html=True)
