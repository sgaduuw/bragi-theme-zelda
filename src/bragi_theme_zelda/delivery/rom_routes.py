"""Flask route that serves ROM-extracted sprite PNGs.

URL shape::

    /zelda/rom/<game>/<palette>/<sprite_name>.png

Response shape::

    HTTP/1.1 200 OK
    Content-Type: image/png
    ETag: "sha256:<hex>"
    Cache-Control: public, max-age=86400, immutable

ETag matches via ``If-None-Match`` return 304.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from bragi.settings import settings
from flask import Blueprint, Response, abort, current_app, g, request

from bragi_theme_zelda.rom import get_sprite_png
from bragi_theme_zelda.rom.cache import MANIFESTS
from bragi_theme_zelda.rom.palettes import PALETTES

VALID_GAMES = frozenset(MANIFESTS.keys())
VALID_PALETTES = frozenset(PALETTES.keys())

CACHE_CONTROL = "public, max-age=86400, immutable"


def _resolve_site_slug() -> str:
    """Resolve current site slug.

    Production: bragi sets ``g.site`` during request resolution.
    Tests: ``ZELDA_TEST_SITE_SLUG`` overrides for unit testing the
    blueprint without standing up a full bragi app.
    """
    override = current_app.config.get("ZELDA_TEST_SITE_SLUG")
    if override:
        return str(override)
    site = getattr(g, "site", None)
    if site is None:
        abort(404)
    return str(site.slug)


def _attachments_root() -> Path:
    """Read the attachments root from bragi's Settings.

    Same pattern as bragi.contrib.attachments (and the admin upload
    handler since v0.4.1). The previous Flask-config approach was a
    v0.2.0 plan-time choice that bragi never populated, so this route
    always 404'd post-deploy. Closes #59 (delivery half of #48)."""
    return Path(settings.attachments_root)


def build_rom_blueprint() -> Blueprint:
    bp = Blueprint("zelda_rom", __name__, url_prefix="/zelda/rom")

    @bp.route("/<game>/<palette>/<sprite_name>.png")
    def sprite(game: str, palette: str, sprite_name: str):  # type: ignore[no-untyped-def]
        if game not in VALID_GAMES:
            abort(404)
        if palette not in VALID_PALETTES:
            abort(404)

        site_slug = _resolve_site_slug()
        attachments_root = _attachments_root()

        try:
            png_bytes = get_sprite_png(
                attachments_root=attachments_root,
                site_slug=site_slug,
                game=game,
                palette=palette,
                sprite_name=sprite_name,
            )
        except KeyError, OSError, IndexError:
            abort(404)

        etag = f'"sha256:{hashlib.sha256(png_bytes).hexdigest()}"'

        # Conditional GET: honour If-None-Match.
        if request.if_none_match.contains(etag.strip('"')):
            resp = Response(status=304)
            resp.headers["ETag"] = etag
            resp.headers["Cache-Control"] = CACHE_CONTROL
            return resp

        resp = Response(png_bytes, mimetype="image/png")
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = CACHE_CONTROL
        return resp

    return bp
