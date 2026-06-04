"""Shared pytest fixtures for bragi-theme-zelda tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from flask import Flask


@pytest.fixture
def bragi_app_with_theme(tmp_path: Path) -> Generator[Flask, None, None]:
    """A minimal bragi delivery app with this theme registered.

    Used by tests/contrib/ and tests/integration/. Importing bragi inside the
    fixture (not at module top) so unit tests that don't need it can run
    without a working bragi install.
    """
    from bragi.apps.delivery import create_delivery_app

    # Test database in tmp_path so fixtures don't bleed across tests.
    db_path = tmp_path / "bragi.db"
    app = create_delivery_app(
        config_overrides={
            "DATABASE_URL": f"sqlite:///{db_path}",
            "SECRET_KEY": "test-only",
        }
    )
    yield app
    # Teardown hook: future tasks add explicit close/cleanup here.
    # tmp_path handles the SQLite file itself; nothing else to do today.
