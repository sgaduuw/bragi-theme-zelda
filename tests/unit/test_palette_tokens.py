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
    "--accent-link": "#08400a",
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
