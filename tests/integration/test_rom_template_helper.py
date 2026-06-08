"""Tests for the rom_sprite / rom_sprite_url Jinja helpers."""

from __future__ import annotations

from bragi_theme_zelda.template_helpers import THEME_VERSION, make_rom_sprite_helpers


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
    assert url.startswith("/theme/zelda/static/sprites/")
    assert url.endswith("marin.png")


def test_rom_sprite_url_with_rom_returns_extraction_url_with_v_query() -> None:
    site = FakeSite(sha="49aa12bd6a32" + "0" * 52)
    _, rom_sprite_url = _helpers(site)
    url = rom_sprite_url("marin", palette="dmg")
    assert url == f"/zelda/rom/la/dmg/marin.png?v=49aa12bd6a32-{THEME_VERSION}"


def test_rom_sprite_url_cache_buster_includes_theme_version() -> None:
    """Closes #68: a theme upgrade that changes the manifest must
    auto-invalidate any browser-cached PNGs even when the operator's
    ROM SHA is unchanged. Mixing the theme version into the ``?v=``
    value is what produces a fresh URL on every theme bump."""
    site = FakeSite(sha="49aa12bd6a32" + "0" * 52)
    _, rom_sprite_url = _helpers(site)
    url = rom_sprite_url("marin", palette="dmg")
    assert "?v=49aa12bd6a32-" in url
    assert url.endswith(THEME_VERSION)
    # The theme version is non-trivial (so a future "dev"/empty fallback
    # doesn't silently regress the cache invalidation).
    assert len(THEME_VERSION) >= 3


def test_rom_sprite_with_no_rom_emits_img_to_placeholder() -> None:
    site = FakeSite()
    rom_sprite, _ = _helpers(site)
    html = str(rom_sprite("marin", alt="Marin says"))
    assert "<img " in html
    assert 'src="/theme/zelda/static/sprites/' in html and "marin.png" in html
    assert 'alt="Marin says"' in html


def test_rom_sprite_with_rom_emits_picture_with_both_palettes() -> None:
    site = FakeSite(sha="49aa12bd6a32" + "0" * 52)
    rom_sprite, _ = _helpers(site)
    html = str(rom_sprite("marin", alt="Marin says"))
    assert "<picture>" in html
    assert 'media="(prefers-color-scheme: dark)"' in html
    assert f"/zelda/rom/la/pocket/marin.png?v=49aa12bd6a32-{THEME_VERSION}" in html
    assert f"/zelda/rom/la/dmg/marin.png?v=49aa12bd6a32-{THEME_VERSION}" in html
    assert 'alt="Marin says"' in html


def test_rom_sprite_url_unknown_name_falls_back_to_placeholder() -> None:
    """Decorative-only sprites (la_pearl, kokiri_emerald, etc.) aren't in
    the manifest. The helper resolves them to the static placeholder
    path rather than raising — the ROM extraction pipeline cannot
    produce them regardless of upload state."""
    site = FakeSite(sha="x" * 64)
    _, rom_sprite_url = _helpers(site)
    url = rom_sprite_url("la_pearl")
    assert url.startswith("/theme/zelda/static/sprites/")
    assert url.endswith("la_pearl.png")


def test_rom_sprite_unknown_name_emits_static_img() -> None:
    """rom_sprite of a decorative-only sprite renders a plain <img>
    pointing at the placeholder, no <picture> variants."""
    site = FakeSite(sha="x" * 64)
    rom_sprite, _ = _helpers(site)
    html = str(rom_sprite("la_pearl", alt="LA Pearl"))
    assert "<img " in html
    assert "<picture>" not in html
    assert 'src="/theme/zelda/static/sprites/' in html and "la_pearl.png" in html
