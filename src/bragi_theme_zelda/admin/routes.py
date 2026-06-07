"""Admin blueprint routes for the Zelda theme's ROM management.

The factory ``build_admin_blueprint`` accepts callables for site
resolution and role gating so the blueprint can be tested without
standing up a full bragi admin app. In production
:mod:`bragi_theme_zelda.plugin` wires bragi's real implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from bragi_theme_zelda.rom.cache import _cached_png
from bragi_theme_zelda.rom.manifest_la import SPRITES_LA
from bragi_theme_zelda.rom.upload import (
    RomValidationError,
    store_rom,
    validate_la_rom,
)

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
        action = request.form.get("action", "")
        if action == "upload" or action == "replace":
            return _handle_upload(site)
        if action == "delete":
            return _handle_delete(site)
        abort(400)

    def _handle_upload(site: Any):  # type: ignore[no-untyped-def]
        uploaded = request.files.get("rom")
        if not uploaded or not uploaded.filename:
            flash("No file selected.", "error")
            return redirect(url_for(".upload", site_slug=site.slug))

        data = uploaded.read()
        try:
            validate_la_rom(data)
        except RomValidationError as exc:
            flash(f"Rejected: {exc}", "error")
            return redirect(url_for(".upload", site_slug=site.slug))

        attachments_root = Path(current_app.config["BRAGI_ATTACHMENTS_ROOT"])
        sha = store_rom(
            data,
            attachments_root=attachments_root,
            site_slug=site.slug,
            game="la",
        )
        site.extra_settings["zelda_rom_la_sha256"] = sha
        site.save()

        # Bust LRU so the next request sees the new ROM if the path is identical.
        _cached_png.cache_clear()

        flash(f"ROM uploaded. sha256: {sha[:12]}…", "success")
        return redirect(url_for(".upload", site_slug=site.slug))

    def _handle_delete(site: Any):  # type: ignore[no-untyped-def]
        # Implemented in Task 15.
        abort(501)

    return bp
