"""Integration tests for the v0.2.0 ROM hookimpls.

Exercises the actual bragi admin + delivery apps to catch signature
drift in ``bragi.core.permissions`` and ``bragi.hookspecs`` that the
stub-based tests in tests/integration/ would miss. See issue #27.
"""

from __future__ import annotations

import inspect

import bragi.hookspecs as bragi_hookspecs
import pluggy
import pytest
from flask import Blueprint, Flask


@pytest.fixture
def pm() -> pluggy.PluginManager:
    """Plugin manager with only this theme registered."""
    from bragi_theme_zelda import plugin as theme_plugin

    pm = pluggy.PluginManager("bragi")
    pm.add_hookspecs(bragi_hookspecs)
    pm.register(theme_plugin)
    return pm


# ── 1. Hookimpl return shapes ────────────────────────────────────────────


def test_register_admin_blueprint_returns_blueprint_with_upload_rule(
    pm: pluggy.PluginManager,
) -> None:
    results = pm.hook.register_admin_blueprint()
    assert len(results) == 1
    bp = results[0]
    assert isinstance(bp, Blueprint)
    # The blueprint factory mounts at /admin/sites/<site_slug>/zelda/rom.
    assert bp.url_prefix == "/admin/sites/<site_slug>/zelda/rom"
    # Walk the registered routes via the URL map of a temporary Flask app;
    # blueprints store deferred functions, not rules, until mounted.
    temp = Flask(__name__)
    temp.register_blueprint(bp)
    paths = {rule.rule for rule in temp.url_map.iter_rules()}
    assert "/admin/sites/<site_slug>/zelda/rom/upload" in paths


def test_register_delivery_blueprint_returns_blueprint_with_sprite_rule(
    pm: pluggy.PluginManager,
) -> None:
    results = pm.hook.register_delivery_blueprint()
    assert len(results) == 1
    bp = results[0]
    assert isinstance(bp, Blueprint)
    assert bp.url_prefix == "/zelda/rom"
    temp = Flask(__name__)
    temp.register_blueprint(bp)
    paths = {rule.rule for rule in temp.url_map.iter_rules()}
    assert "/zelda/rom/<game>/<palette>/<sprite_name>.png" in paths


# ── 2. Real-app mounting ─────────────────────────────────────────────────


@pytest.fixture
def real_admin_app(patched_session_locals) -> Flask:  # type: ignore[no-untyped-def]
    """A real bragi admin app with the theme entry-point loaded.

    Mirrors conftest.bragi_app_with_theme's shape but for the admin
    side. patched_session_locals redirects all bragi SessionLocal()
    calls to the in-memory test DB.
    """
    from bragi.apps.admin import create_admin_app

    return create_admin_app()


@pytest.fixture
def real_delivery_app(patched_session_locals) -> Flask:  # type: ignore[no-untyped-def]
    from bragi.apps.delivery import create_delivery_app

    return create_delivery_app()


def test_real_admin_app_mounts_rom_upload_route(real_admin_app: Flask) -> None:
    paths = {rule.rule for rule in real_admin_app.url_map.iter_rules()}
    assert "/admin/sites/<site_slug>/zelda/rom/upload" in paths, (
        f"register_admin_blueprint did not wire into create_admin_app(); "
        f"sample routes: {sorted(paths)[:10]}"
    )


def test_real_delivery_app_mounts_rom_sprite_route(real_delivery_app: Flask) -> None:
    paths = {rule.rule for rule in real_delivery_app.url_map.iter_rules()}
    assert "/zelda/rom/<game>/<palette>/<sprite_name>.png" in paths, (
        f"register_delivery_blueprint did not wire into create_delivery_app(); "
        f"sample routes: {sorted(paths)[:10]}"
    )


# ── 3. Delivery 404 happy-ish path ───────────────────────────────────────


def test_delivery_sprite_route_404s_for_unknown_site(
    real_delivery_app: Flask,
) -> None:
    """The sprite route runs end-to-end. With no site matched for the test
    host in the in-memory DB, the site_resolver middleware sets g.site to
    None, and the handler aborts 404. Proves the route handler runs through
    the validation + resolve + abort path without exception.
    """
    client = real_delivery_app.test_client()
    resp = client.get("/zelda/rom/la/dmg/marin.png")
    assert resp.status_code == 404


# ── 4. bragi.core.permissions signature stability ────────────────────────


def test_resolve_site_or_abort_signature_stable() -> None:
    """plugin.py calls resolve_site_or_abort(db, site_slug) inside the
    _current_site closure passed to build_admin_blueprint. Catches a rename
    or signature change in bragi.core.permissions.
    """
    from bragi.core.permissions import resolve_site_or_abort

    sig = inspect.signature(resolve_site_or_abort)
    params = list(sig.parameters.values())
    # Expect: at least two positional parameters (db, slug).
    assert len(params) >= 2, f"resolve_site_or_abort signature changed: {sig}"


def test_require_role_signature_stable() -> None:
    """plugin.py passes require_role directly as the role gate for the
    admin blueprint factory. The factory's RoleChecker contract is
    (role: str, site_id: int) -> None; bragi.core.permissions.require_role
    must accept that shape.
    """
    from bragi.core.permissions import require_role

    sig = inspect.signature(require_role)
    params = list(sig.parameters.values())
    # Expect at least two positional parameters (role/min_role, site_id).
    assert len(params) >= 2, f"require_role signature changed: {sig}"
