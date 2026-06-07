"""Tests for the rom_sprite / rom_sprite_url Jinja helpers."""

from __future__ import annotations

import pytest

from bragi_theme_zelda.template_helpers import make_rom_sprite_helpers


class FakeSite:
    def __init__(self, sha: str | None = None) -> None:
        self.extra_settings: dict[str, str] = {}
        if sha:
            self.extra_settings["zelda_rom_la_sha256"] = sha


def _helpers(site: FakeSite):
    return make_rom_sprite_helpers(get_site=lambda: site)


def test_rom_sprite_url_with_no_rom_returns_placeholder_path() -> None:
    site = FakeSite()
    _, rom_sprite_url = _helpers(site)
    url = rom_sprite_url("marin", palette="dmg")
    assert url.startswith("/static/sprites/")
    assert url.endswith("marin.png")


def test_rom_sprite_url_with_rom_returns_extraction_url_with_v_query() -> None:
    site = FakeSite(sha="49aa12bd6a32" + "0" * 52)
    _, rom_sprite_url = _helpers(site)
    url = rom_sprite_url("marin", palette="dmg")
    assert url == "/zelda/rom/la/dmg/marin.png?v=49aa12bd6a32"


def test_rom_sprite_with_no_rom_emits_img_to_placeholder() -> None:
    site = FakeSite()
    rom_sprite, _ = _helpers(site)
    html = str(rom_sprite("marin", alt="Marin says"))
    assert "<img " in html
    assert 'src="/static/sprites/' in html and "marin.png" in html
    assert 'alt="Marin says"' in html


def test_rom_sprite_with_rom_emits_picture_with_both_palettes() -> None:
    site = FakeSite(sha="49aa12bd6a32" + "0" * 52)
    rom_sprite, _ = _helpers(site)
    html = str(rom_sprite("marin", alt="Marin says"))
    assert "<picture>" in html
    assert 'media="(prefers-color-scheme: dark)"' in html
    assert "/zelda/rom/la/pocket/marin.png?v=49aa12bd6a32" in html
    assert "/zelda/rom/la/dmg/marin.png?v=49aa12bd6a32" in html
    assert 'alt="Marin says"' in html


def test_rom_sprite_unknown_name_raises_keyerror() -> None:
    site = FakeSite(sha="x" * 64)
    rom_sprite, _ = _helpers(site)
    with pytest.raises(KeyError):
        rom_sprite("no_such_sprite")
