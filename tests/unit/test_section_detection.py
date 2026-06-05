"""Section detection: walk a page's ancestors to the section root."""

from __future__ import annotations

from dataclasses import dataclass

from bragi_theme_zelda.section import detect_section


@dataclass
class FakePage:
    slug: str
    parent: FakePage | None


SECTION_MAP = {"links-awakening": "la", "ocarina-of-time": "oot"}


def test_top_level_la_page_is_la_section() -> None:
    page = FakePage(slug="links-awakening", parent=None)
    assert detect_section(page, SECTION_MAP) == ("la", "Link's Awakening")


def test_top_level_oot_page_is_oot_section() -> None:
    page = FakePage(slug="ocarina-of-time", parent=None)
    assert detect_section(page, SECTION_MAP) == ("oot", "Ocarina of Time")


def test_nested_la_page_walks_to_la_section() -> None:
    section_root = FakePage(slug="links-awakening", parent=None)
    dungeon = FakePage(slug="tail-cave", parent=section_root)
    room = FakePage(slug="compass-room", parent=dungeon)
    assert detect_section(room, SECTION_MAP) == ("la", "Link's Awakening")


def test_page_outside_known_sections_returns_empty() -> None:
    page = FakePage(slug="about", parent=None)
    assert detect_section(page, SECTION_MAP) == ("", "")


def test_none_page_returns_empty() -> None:
    assert detect_section(None, SECTION_MAP) == ("", "")
