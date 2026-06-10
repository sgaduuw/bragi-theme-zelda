"""Shared pytest fixtures for bragi-theme-zelda tests."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from tests.data.rom_fixtures import build_fixture_rom, checkerboard_tile

if TYPE_CHECKING:
    from flask import Flask
    from sqlalchemy.engine import Engine


# Seed values for ``bragi_admin_app_with_zelda_site``. Module-level so
# tests can import them by name rather than re-destructuring the
# fixture tuple. See spec
# ``_claude/specs/2026-06-08-real-admin-app-fixture-design.md``.
ADMIN_EDITOR_EMAIL = "editor@example.test"
ADMIN_EDITOR_PASSWORD = "test-editor-password-correct-horse-battery-staple"
ADMIN_TEST_SITE_SLUG = "testsite"
ADMIN_TEST_SITE_HOSTNAME = "testsite.example.test"


def csrf_token(client: FlaskClient, *, path: str = "/auth/login") -> str:
    """Fetch the session's CSRF token via the test client.

    The CSRF guard fires as a before_request hook on every request,
    including GETs; hitting any path is enough to populate the session.
    The default ``/auth/login`` is a public endpoint on the admin app
    so the call works pre-auth. Tests against a non-default path pass
    ``path=`` explicitly (the token is bound to the session, not the
    path, but rotating per-request means later GETs see a fresh
    token).
    """
    client.get(path)
    with client.session_transaction() as sess:
        token = sess.get("_csrf_token")
    assert isinstance(token, str) and token, (
        "CSRF token was not populated on the session"
    )
    return token


def login_editor(
    client: FlaskClient,
    email: str,
    password: str,
) -> None:
    """POST /auth/login with the CSRF token included.

    After this returns, the client carries the authenticated session
    cookie. Subsequent requests resolve ``g.user`` to the editor row.
    """
    token = csrf_token(client, path="/auth/login")
    resp = client.post(
        "/auth/login",
        data={"email": email, "password": password, "_csrf_token": token},
    )
    assert resp.status_code in (302, 303), (
        f"Login did not redirect (got {resp.status_code}); body: {resp.data[:200]!r}"
    )


@pytest.fixture
def db_engine() -> Iterator[Engine]:
    """Fresh in-memory SQLite with all bragi tables created.

    Uses `Base.metadata.create_all` (not alembic) to keep tests fast
    and isolated from migration history, matching bragi's own test
    convention.
    """
    from bragi.core.models import Base

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: Engine) -> sessionmaker[Session]:
    """Session factory bound to the test engine."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )


@pytest.fixture
def db_session(db_session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A live session for direct DB manipulation in tests."""
    with db_session_factory() as session:
        yield session


@pytest.fixture
def patched_session_locals(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> sessionmaker[Session]:
    """Redirect every `SessionLocal()` call in bragi to the test engine.

    `bragi.core.db.SessionLocal` is a `_SessionFactoryProxy` shared by
    every `from bragi.core.db import SessionLocal` importer. Rebinding
    `_factory` on it propagates to every call site in one patch.
    """
    from bragi.core import db

    monkeypatch.setattr(db.SessionLocal, "_factory", db_session_factory)
    return db_session_factory


@pytest.fixture
def bragi_app_with_theme(
    patched_session_locals: sessionmaker[Session],
) -> Generator[Flask, None, None]:
    """A minimal bragi delivery app with this theme registered.

    Used by tests/contrib/ and tests/integration/. The delivery app
    is built against the in-memory test DB (patched_session_locals
    redirects all SessionLocal calls). Importing bragi inside the
    fixture so unit tests that don't need it can run without a
    working bragi install.
    """
    from bragi.apps.delivery import create_delivery_app

    app = create_delivery_app()
    yield app


@pytest.fixture(scope="session")
def fixture_rom_bytes() -> bytes:
    """Synthetic 1 MB GB-shaped ROM with one known checkerboard tile at 0x10000.

    Session-scoped because the bytes are deterministic — nothing
    inside a test mutates the bytes.
    """
    return build_fixture_rom(tile_at_0x10000=checkerboard_tile())


@pytest.fixture
def fixture_rom_path(tmp_path: Path, fixture_rom_bytes: bytes) -> Path:
    """Per-test temp .gb file containing the fixture ROM bytes."""
    path = tmp_path / "la.gb"
    path.write_bytes(fixture_rom_bytes)
    return path


@pytest.fixture
def bragi_admin_app_with_zelda_site(
    db_session: Session,
    patched_session_locals: sessionmaker[Session],
) -> Generator[tuple[Flask, str, str, str], None, None]:
    """Real bragi admin app + a zelda-themed test site + an editor user.

    Yields ``(admin_app, site_slug, editor_email, editor_password)``.

    Seeds, in order:

    - Owner ``User`` (separate identity so the editor stays editor
      and doesn't become implicit-admin via bragi's site-owner-is-
      implicit-admin rule).
    - Editor ``User`` + ``LocalCredential`` with a known password.
    - Zelda-themed ``Site`` at ``slug=ADMIN_TEST_SITE_SLUG``.
    - ``UserSiteRole(role="editor")`` binding editor to the site.

    Resolves the test DB via ``patched_session_locals`` so every
    bragi ``SessionLocal()`` call (admin auth, role checks, the
    theme's ``_persist_site_extra_setting`` helper) sees the
    in-memory engine.

    Replaces the previous stub Flask app fixture in
    ``tests/integration/test_rom_admin.py`` per #43; see spec for
    rationale.
    """
    from bragi.apps.admin import create_admin_app
    from bragi.contrib.auth_local.passwords import hash_password
    from bragi.core.models import LocalCredential, Site, User, UserSiteRole

    owner = User(
        email="_owner@example.test",
        display_name="Owner",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(owner)
    db_session.flush()

    editor = User(
        email=ADMIN_EDITOR_EMAIL,
        display_name="Editor",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(editor)
    db_session.flush()
    db_session.add(
        LocalCredential(
            user_id=editor.id,
            password_hash=hash_password(ADMIN_EDITOR_PASSWORD),
        ),
    )

    site = Site(
        slug=ADMIN_TEST_SITE_SLUG,
        hostname=ADMIN_TEST_SITE_HOSTNAME,
        title="Test Site",
        canonical_url=f"https://{ADMIN_TEST_SITE_HOSTNAME}",
        active=True,
        owner_user_id=owner.id,
        theme="zelda",
    )
    db_session.add(site)
    db_session.flush()

    db_session.add(
        UserSiteRole(user_id=editor.id, site_id=site.id, role="editor"),
    )
    db_session.commit()

    yield (
        create_admin_app(),
        ADMIN_TEST_SITE_SLUG,
        ADMIN_EDITOR_EMAIL,
        ADMIN_EDITOR_PASSWORD,
    )
