"""Palette token presence + value tests.

Parses theme.css and verifies the documented tokens exist with the right
hex values per the spec. Catches drift between the spec table and the CSS.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CSS_PATH = (
    Path(__file__).parents[2]
    / "src"
    / "bragi_theme_zelda"
    / "static"
    / "css"
    / "theme.css"
)


@pytest.fixture
def css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _extract_block(css: str, selector: str) -> str:
    """Return the body of the first `selector { ... }` block."""
    pattern = re.compile(
        re.escape(selector) + r"\s*\{([^}]*)\}",
        re.DOTALL,
    )
    m = pattern.search(css)
    assert m is not None, f"Selector {selector!r} not found"
    return m.group(1)


def _extract_token(block: str, token: str) -> str:
    pattern = re.compile(rf"{re.escape(token)}\s*:\s*([^;]+);")
    m = pattern.search(block)
    assert m is not None, f"Token {token!r} not found"
    return m.group(1).strip()


LA_LIGHT_TOKENS = {
    "--gb-0": "#0f380f",
    "--gb-1": "#306230",
    "--gb-2": "#8bac0f",
    "--gb-3": "#9bbc0f",
    "--accent-link": "#0a4a0c",
    "--accent-warn": "#a8201a",
    "--accent-info": "#3a6ba5",
}

OOT_LIGHT_TOKENS = {
    "--gb-0": "#1a2438",
    "--gb-1": "#2c3a52",
    "--gb-2": "#9da7c4",
    "--gb-3": "#c5cbe0",
    "--accent-link": "#3d4f8a",
}


def test_la_light_tokens_on_root(css: str) -> None:
    block = _extract_block(css, ":root")
    for token, value in LA_LIGHT_TOKENS.items():
        assert _extract_token(block, token) == value, f"{token} drift"


def test_oot_tokens_in_data_section_oot(css: str) -> None:
    block = _extract_block(css, '[data-section="oot"]')
    for token, value in OOT_LIGHT_TOKENS.items():
        assert _extract_token(block, token) == value, f"{token} drift"


def test_dark_mode_media_query_exists(css: str) -> None:
    assert "@media (prefers-color-scheme: dark)" in css
    # And the Pocket-greyscale tokens land inside it.
    dark_match = re.search(
        r"@media \(prefers-color-scheme: dark\)\s*\{.*?\}\s*\}",
        css,
        re.DOTALL,
    )
    assert dark_match is not None
    assert "#0a0a0a" in dark_match.group(0)
    assert "#c0c0c0" in dark_match.group(0)


def test_manual_theme_override_selectors_exist(css: str) -> None:
    assert '[data-theme="la-green"]' in css
    assert '[data-theme="gb-pocket"]' in css


# The manual-toggle blocks must re-declare the accent tokens so they don't
# leak from prefers-color-scheme. Without this, force-selecting la-green under
# an OS dark color-scheme drew the dark link colour (#a8a8c8) on the green
# page (#9bbc0f) at ~1:1 contrast (the 2026-06-15 readability fix).
LA_GREEN_MANUAL_ACCENTS = {
    "--accent-link": "#0a4a0c",
    "--accent-warn": "#a8201a",
    "--accent-info": "#3a6ba5",
}
GB_POCKET_MANUAL_ACCENTS = {
    "--accent-link": "#a8a8c8",
    "--accent-warn": "#d05050",
    "--accent-info": "#7090c0",
}


def test_manual_la_green_redeclares_light_accents(css: str) -> None:
    block = _extract_block(css, '[data-theme="la-green"]')
    for token, value in LA_GREEN_MANUAL_ACCENTS.items():
        assert _extract_token(block, token) == value, f"{token} drift"


def test_manual_gb_pocket_redeclares_dark_accents(css: str) -> None:
    block = _extract_block(css, '[data-theme="gb-pocket"]')
    for token, value in GB_POCKET_MANUAL_ACCENTS.items():
        assert _extract_token(block, token) == value, f"{token} drift"


def test_prose_links_carry_non_colour_affordance(css: str) -> None:
    """On the GB palette a link can't get a strong colour gap from body text
    and still clear AA against the page, so prose links must read as links via
    weight + a clear underline (colour-axis-independent). Guards the fix that
    stopped links from looking like ordinary underlined text."""
    block = _extract_block(css, ".zelda-prose a")
    assert "font-weight: 600" in block
    assert "text-decoration: underline" in block
    assert "text-decoration-thickness: 2px" in block
    # The interaction states exist (hover feedback + keyboard focus ring).
    assert ".zelda-prose a:hover" in css
    assert ".zelda-prose a:focus-visible" in css


def test_manual_theme_preserves_oot_link_tint(css: str) -> None:
    """Forced theme + OoT keeps the blue section link via the combined selector."""
    la_oot = _extract_block(css, '[data-theme="la-green"][data-section="oot"]')
    assert _extract_token(la_oot, "--accent-link") == "#3d4f8a"
    gb_oot = _extract_block(css, '[data-theme="gb-pocket"][data-section="oot"]')
    assert _extract_token(gb_oot, "--accent-link") == "#b4c0e0"
