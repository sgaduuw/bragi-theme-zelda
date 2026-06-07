"""Integration tests for /zelda/rom/la/<palette>/<sprite>.png."""

from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from bragi_theme_zelda.delivery.rom_routes import build_rom_blueprint
from bragi_theme_zelda.rom.cache import _cache_clear
from bragi_theme_zelda.rom.upload import store_rom
from tests.data.rom_fixtures import build_fixture_rom, checkerboard_tile


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    _cache_clear()


@pytest.fixture
def app(tmp_path: Path) -> Flask:
    """Minimal Flask app with the ROM blueprint mounted.

    Avoids spinning up the full bragi delivery app for fast tests.
    The blueprint resolves `attachments_root` from a config key so
    the test fixture can point it at tmp_path.
    """
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["BRAGI_ATTACHMENTS_ROOT"] = str(tmp_path)
    # Override site-slug resolution to a fixed value for these tests.
    flask_app.config["ZELDA_TEST_SITE_SLUG"] = "testsite"
    flask_app.register_blueprint(build_rom_blueprint())
    return flask_app


def test_unknown_game_returns_404(app: Flask) -> None:
    resp = app.test_client().get("/zelda/rom/ot/dmg/marin.png")
    assert resp.status_code == 404


def test_unknown_palette_returns_404(app: Flask, tmp_path: Path) -> None:
    rom = build_fixture_rom(tile_at_0x10000=checkerboard_tile())
    store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    resp = app.test_client().get("/zelda/rom/la/neon/_fixture_tile.png")
    assert resp.status_code == 404


def test_unknown_sprite_returns_404(app: Flask, tmp_path: Path) -> None:
    rom = build_fixture_rom(tile_at_0x10000=checkerboard_tile())
    store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    resp = app.test_client().get("/zelda/rom/la/dmg/no_such_sprite.png")
    assert resp.status_code == 404


def test_no_rom_uploaded_returns_404(app: Flask) -> None:
    resp = app.test_client().get("/zelda/rom/la/dmg/_fixture_tile.png")
    assert resp.status_code == 404
