"""Integration tests for the admin ROM upload Blueprint.

Stands up a real bragi admin app via ``bragi_admin_app_with_zelda_site``
(in ``tests/conftest.py``) so the tests exercise real CSRF middleware,
real chrome inheritance, real auth, and real DB writes via the
production ``_persist_site_extra_setting`` helper. The previous
stub-app fixture missed two production bugs (#38 — template wasn't
extending ``admin/base.html``; #39 — forms lacked ``_csrf_token``)
that v0.3.1 hotfixed; this migration closes #43 by removing the
stub. See spec at
``_claude/specs/2026-06-08-real-admin-app-fixture-design.md``.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from bragi.core.models.site import Site
from flask import Flask
from sqlalchemy import select
from sqlalchemy.orm import Session

from bragi_theme_zelda.rom.cache import _cache_clear
from bragi_theme_zelda.rom.upload import rom_path_for_site, store_rom
from tests.conftest import csrf_token, login_editor


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    _cache_clear()


def _authed_client_with_csrf(
    admin_app: Flask,
    site_slug: str,
    editor_email: str,
    editor_password: str,
) -> tuple[object, str, str]:
    """Build an authed test client + a fresh CSRF token for the upload URL.

    Returns ``(client, token, upload_path)``. The CSRF token is bound
    to the session and rotated per-request; fetching it AFTER login
    via a GET on the upload URL itself gives a token the upload POST
    will accept.
    """
    client = admin_app.test_client()
    login_editor(client, editor_email, editor_password)
    upload_path = f"/admin/sites/{site_slug}/zelda/rom/upload"
    token = csrf_token(client, path=upload_path)
    return client, token, upload_path


def test_status_get_with_no_rom_shows_empty_state(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client = app.test_client()
    login_editor(client, email, password)

    resp = client.get(f"/admin/sites/{slug}/zelda/rom/upload")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "No ROM uploaded" in body
    assert "Drop your .gb file" in body or "Choose file" in body


def test_status_get_with_active_rom_shows_sha_and_preview_grid(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    db_session: Session,
    tmp_path: Path,
    fixture_rom_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site

    # Pre-seed the file + the SHA via the production helpers + a
    # direct DB write (not exercising the upload code path here, just
    # the GET render with a ROM already present).
    sha = store_rom(
        fixture_rom_bytes,
        attachments_root=tmp_path,
        site_slug=slug,
        game="la",
    )
    site_row = db_session.execute(
        select(Site).where(Site.slug == slug),
    ).scalar_one()
    site_row.extra_settings = {"zelda_rom_la_sha256": sha}
    db_session.commit()

    client = app.test_client()
    login_editor(client, email, password)

    resp = client.get(f"/admin/sites/{slug}/zelda/rom/upload")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "ROM active" in body
    assert sha[:12] in body
    for name in ("marin", "tarin", "owl", "ulrira", "heart_container"):
        assert name in body
    # Cross-host preview URL (v0.4.4): admin host vs delivery host.
    assert f"//{site_row.hostname}/zelda/rom/la/dmg/marin.png" in body


def test_upload_post_with_valid_rom_stores_file_and_sha(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    db_session: Session,
    tmp_path: Path,
    fixture_rom_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client, token, upload_path = _authed_client_with_csrf(app, slug, email, password)

    resp = client.post(
        upload_path,
        data={
            "action": "upload",
            "_csrf_token": token,
            "rom": (io.BytesIO(fixture_rom_bytes), "la.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert rom_path_for_site(tmp_path, slug, "la").read_bytes() == fixture_rom_bytes

    site_row = db_session.execute(
        select(Site).where(Site.slug == slug),
    ).scalar_one()
    db_session.refresh(site_row)
    sha = site_row.extra_settings.get("zelda_rom_la_sha256")
    assert sha is not None
    assert len(sha) == 64


def test_upload_post_with_invalid_rom_rejects_and_keeps_state_clean(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client, token, upload_path = _authed_client_with_csrf(app, slug, email, password)

    bad = b"not a ROM, just a small text file."
    resp = client.post(
        upload_path,
        data={
            "action": "upload",
            "_csrf_token": token,
            "rom": (io.BytesIO(bad), "fake.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (200, 302, 303)
    assert not rom_path_for_site(tmp_path, slug, "la").exists()

    site_row = db_session.execute(
        select(Site).where(Site.slug == slug),
    ).scalar_one()
    db_session.refresh(site_row)
    assert "zelda_rom_la_sha256" not in site_row.extra_settings


def test_upload_post_without_file_returns_error(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client, token, upload_path = _authed_client_with_csrf(app, slug, email, password)

    resp = client.post(
        upload_path,
        data={"action": "upload", "_csrf_token": token},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (200, 302, 303, 400)
    assert not rom_path_for_site(tmp_path, slug, "la").exists()


def test_upload_post_with_oversize_body_returns_413(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: oversize uploads must 413 before buffering the body.

    Defends against admin-worker OOM (#26): the cap is checked via
    Content-Length before any ``request.files`` access. Posting 8 MiB
    of arbitrary bytes (well past the 4 MiB ROM cap + 64 KiB envelope
    margin) must return 413 and never write a file.
    """
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client, token, upload_path = _authed_client_with_csrf(app, slug, email, password)

    oversize = b"\x00" * (8 * 1024 * 1024)
    resp = client.post(
        upload_path,
        data={
            "action": "upload",
            "_csrf_token": token,
            "rom": (io.BytesIO(oversize), "huge.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 413
    assert not rom_path_for_site(tmp_path, slug, "la").exists()


def test_delete_post_removes_file_and_clears_sha(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    db_session: Session,
    tmp_path: Path,
    fixture_rom_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site

    # Pre-seed: ROM file present + sha in DB.
    sha = store_rom(
        fixture_rom_bytes,
        attachments_root=tmp_path,
        site_slug=slug,
        game="la",
    )
    site_row = db_session.execute(
        select(Site).where(Site.slug == slug),
    ).scalar_one()
    site_row.extra_settings = {"zelda_rom_la_sha256": sha}
    db_session.commit()

    client, token, upload_path = _authed_client_with_csrf(app, slug, email, password)

    resp = client.post(
        upload_path,
        data={"action": "delete", "_csrf_token": token},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert not rom_path_for_site(tmp_path, slug, "la").exists()

    db_session.refresh(site_row)
    assert "zelda_rom_la_sha256" not in site_row.extra_settings


def test_upload_post_without_csrf_token_is_rejected(
    bragi_admin_app_with_zelda_site: tuple[Flask, str, str, str],
    tmp_path: Path,
    fixture_rom_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closes #43 directly: if a form drops ``_csrf_token``, CI fails.

    Guards against the v0.3.0 / v0.3.1 regression class (#39) — a
    future template change that omits the CSRF hidden input would
    have passed the stub-fixture tests (no CSRF middleware) but
    failed in production. The real fixture + real CSRF middleware now
    reject the POST.
    """
    from bragi.settings import settings as bragi_settings

    monkeypatch.setattr(bragi_settings, "attachments_root", str(tmp_path))

    app, slug, email, password = bragi_admin_app_with_zelda_site
    client = app.test_client()
    login_editor(client, email, password)
    upload_path = f"/admin/sites/{slug}/zelda/rom/upload"

    resp = client.post(
        upload_path,
        data={
            "action": "upload",
            "rom": (io.BytesIO(fixture_rom_bytes), "la.gb"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # CSRF middleware on bragi's admin app rejects without a token.
    assert resp.status_code in (400, 403)
    assert not rom_path_for_site(tmp_path, slug, "la").exists()
