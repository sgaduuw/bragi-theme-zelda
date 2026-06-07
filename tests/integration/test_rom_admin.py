"""Integration tests for the admin ROM upload Blueprint.

These tests stand up a minimal Flask app with the blueprint mounted
(no bragi admin app or DB), and inject a stub ``current_site()`` helper
via the blueprint factory.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from bragi_theme_zelda.admin.routes import build_admin_blueprint
from bragi_theme_zelda.rom.cache import _cache_clear
from bragi_theme_zelda.rom.upload import store_rom
from tests.data.rom_fixtures import build_fixture_rom


class StubSite:
    """Minimal Site stand-in for tests."""

    def __init__(self, slug: str = "testsite") -> None:
        self.slug = slug
        self.id = 1
        self.extra_settings: dict[str, str] = {}

    def save(self) -> None:
        """Mock save (test-only — no actual DB persistence)."""


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    _cache_clear()


@pytest.fixture
def site() -> StubSite:
    return StubSite()


@pytest.fixture
def app(tmp_path: Path, site: StubSite) -> Flask:
    flask_app = Flask(__name__, template_folder=None)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"  # flask.flash needs sessions
    flask_app.config["BRAGI_ATTACHMENTS_ROOT"] = str(tmp_path)
    flask_app.register_blueprint(
        build_admin_blueprint(
            current_site=lambda _slug: site,
            require_role=lambda _role, _site_id: None,
        ),
    )
    return flask_app


def test_status_get_with_no_rom_shows_empty_state(app: Flask) -> None:
    resp = app.test_client().get("/admin/sites/testsite/zelda/rom/upload")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "No ROM uploaded" in body
    assert "Drop your .gb file" in body or "Choose file" in body


def test_status_get_with_active_rom_shows_sha_and_preview_grid(
    app: Flask, site: StubSite, tmp_path: Path,
) -> None:
    rom = build_fixture_rom()
    sha = store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    site.extra_settings["zelda_rom_la_sha256"] = sha

    resp = app.test_client().get("/admin/sites/testsite/zelda/rom/upload")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "ROM active" in body
    assert sha[:12] in body  # truncated SHA shown
    # Preview grid should reference each manifest sprite.
    for name in ("marin", "tarin", "owl", "ulrira", "heart_container"):
        assert name in body
