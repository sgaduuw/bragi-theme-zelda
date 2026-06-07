"""Integration tests for the admin ROM upload Blueprint.

These tests stand up a minimal Flask app with the blueprint mounted
(no bragi admin app or DB), and inject a stub ``current_site()`` helper
via the blueprint factory.
"""

from __future__ import annotations

import io
from pathlib import Path

import jinja2
import pytest
from flask import Flask

from bragi_theme_zelda.admin.routes import build_admin_blueprint
from bragi_theme_zelda.rom.cache import _cache_clear
from bragi_theme_zelda.rom.upload import rom_path_for_site, store_rom
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
def app(
    tmp_path: Path,
    site: StubSite,
    monkeypatch: pytest.MonkeyPatch,
) -> Flask:
    # Theme reads bragi.settings.settings.attachments_root for the storage
    # path. Pin it at tmp_path so each test gets a clean attachments dir,
    # matching what the production bragi admin app would resolve from env.
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    flask_app = Flask(__name__, template_folder=None)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"  # flask.flash needs sessions
    flask_app.register_blueprint(
        build_admin_blueprint(
            current_site=lambda _slug: site,
            require_role=lambda _role, _site_id: None,
        ),
    )
    # The zelda_rom.html template extends "admin/base.html" (bragi's admin
    # chrome) and calls csrf_token() (bragi's CSRF middleware). The real
    # admin app provides both; this stub provides minimal stand-ins so the
    # template renders. Asserting on chrome shape or real CSRF rejection is
    # a separate concern covered by the contrib tests that exercise the
    # real bragi admin app.
    flask_app.jinja_env.loader = jinja2.ChoiceLoader(
        [
            flask_app.jinja_env.loader,
            jinja2.DictLoader(
                {
                    "admin/base.html": (
                        "<!doctype html><html><head>"
                        "<title>{% block title %}{% endblock %}</title>"
                        "</head><body>{% block content %}{% endblock %}</body></html>"
                    ),
                },
            ),
        ],
    )
    flask_app.jinja_env.globals["csrf_token"] = lambda: "test-csrf-token"
    return flask_app


def test_status_get_with_no_rom_shows_empty_state(app: Flask) -> None:
    resp = app.test_client().get("/admin/sites/testsite/zelda/rom/upload")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "No ROM uploaded" in body
    assert "Drop your .gb file" in body or "Choose file" in body


def test_status_get_with_active_rom_shows_sha_and_preview_grid(
    app: Flask,
    site: StubSite,
    tmp_path: Path,
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


def test_upload_post_with_valid_rom_stores_file_and_sha(
    app: Flask,
    site: StubSite,
    tmp_path: Path,
) -> None:
    rom = build_fixture_rom()
    resp = app.test_client().post(
        "/admin/sites/testsite/zelda/rom/upload",
        data={
            "action": "upload",
            "rom": (io.BytesIO(rom), "la.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)  # redirect after POST
    assert rom_path_for_site(tmp_path, "testsite", "la").read_bytes() == rom
    assert site.extra_settings.get("zelda_rom_la_sha256") is not None
    assert len(site.extra_settings["zelda_rom_la_sha256"]) == 64


def test_upload_post_with_invalid_rom_rejects_and_keeps_state_clean(
    app: Flask,
    site: StubSite,
    tmp_path: Path,
) -> None:
    bad = b"not a ROM, just a small text file."
    resp = app.test_client().post(
        "/admin/sites/testsite/zelda/rom/upload",
        data={
            "action": "upload",
            "rom": (io.BytesIO(bad), "fake.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Either re-renders the form (200) or redirects (302) with a flash.
    assert resp.status_code in (200, 302, 303)
    assert not rom_path_for_site(tmp_path, "testsite", "la").exists()
    assert "zelda_rom_la_sha256" not in site.extra_settings


def test_upload_post_without_file_returns_error(app: Flask, tmp_path: Path) -> None:
    resp = app.test_client().post(
        "/admin/sites/testsite/zelda/rom/upload",
        data={"action": "upload"},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (200, 302, 303, 400)
    assert not rom_path_for_site(tmp_path, "testsite", "la").exists()


def test_upload_post_with_oversize_body_returns_413(
    app: Flask,
    tmp_path: Path,
) -> None:
    """Regression: oversize uploads must 413 before buffering the body.

    Defends against admin-worker OOM (issue #26): the cap is checked
    via Content-Length before any request.files access. Posting 8 MiB
    of arbitrary bytes (well past the 4 MiB ROM cap + 64 KiB envelope
    margin) must return 413 and never write a file.
    """
    oversize = b"\x00" * (8 * 1024 * 1024)
    resp = app.test_client().post(
        "/admin/sites/testsite/zelda/rom/upload",
        data={
            "action": "upload",
            "rom": (io.BytesIO(oversize), "huge.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 413
    assert not rom_path_for_site(tmp_path, "testsite", "la").exists()


def test_delete_post_removes_file_and_clears_sha(
    app: Flask,
    site: StubSite,
    tmp_path: Path,
) -> None:
    rom = build_fixture_rom()
    sha = store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    site.extra_settings["zelda_rom_la_sha256"] = sha

    resp = app.test_client().post(
        "/admin/sites/testsite/zelda/rom/upload",
        data={"action": "delete"},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert not rom_path_for_site(tmp_path, "testsite", "la").exists()
    assert "zelda_rom_la_sha256" not in site.extra_settings
