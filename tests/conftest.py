"""Shared pytest fixtures for bragi-theme-zelda tests."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from flask import Flask
    from sqlalchemy.engine import Engine


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
