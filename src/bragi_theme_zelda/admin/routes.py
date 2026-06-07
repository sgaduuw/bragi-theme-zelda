"""Admin blueprint routes for the Zelda theme's ROM management.

The factory ``build_admin_blueprint`` accepts callables for site
resolution and role gating so the blueprint can be tested without
standing up a full bragi admin app. In production
:mod:`bragi_theme_zelda.plugin` wires bragi's real implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import (
    Blueprint,
    abort,
    render_template,
    request,
)

from bragi_theme_zelda.rom.manifest_la import SPRITES_LA

SiteResolver = Callable[[str], Any]
RoleChecker = Callable[[str, int], None]


def build_admin_blueprint(
    *,
    current_site: SiteResolver,
    require_role: RoleChecker,
) -> Blueprint:
    """Build the ROM-management admin blueprint.

    Parameters
    ----------
    current_site
        Callable ``(site_slug: str) -> Site | None``. Returns
        ``None`` (or raises ``abort(404)`` directly) if no such site
        or the user can't see it. The route handler guards on
        ``None`` for safety.
    require_role
        Callable ``(role: str, site_id: int) -> None`` that aborts
        with 403 if the user lacks the role. Bragi's standard
        implementation; pass the real ``bragi.api.require_role``
        in production.
    """
    bp = Blueprint(
        "zelda_admin",
        __name__,
        template_folder="templates",
        url_prefix="/admin/sites/<site_slug>/zelda/rom",
    )

    @bp.route("/upload", methods=["GET", "POST"])
    def upload(site_slug: str):  # type: ignore[no-untyped-def]
        site = current_site(site_slug)
        if site is None:
            abort(404)
        require_role("editor", site.id)

        if request.method == "POST":
            return _handle_post(site)

        return render_template(
            "admin/zelda_rom.html",
            site=site,
            rom_sha=site.extra_settings.get("zelda_rom_la_sha256"),
            sprite_names=list(SPRITES_LA.keys()),
        )

    def _handle_post(site: Any):  # type: ignore[no-untyped-def]
        # Implemented in Task 14.
        abort(405)

    return bp
