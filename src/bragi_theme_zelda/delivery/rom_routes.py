"""Flask route that serves ROM-extracted sprite PNGs.

URL shape::

    /zelda/rom/<game>/<palette>/<sprite_name>.png

The ``rom`` segment is intentional and visible: it tells anyone
reading the URL that the response is extracted live from the
operator-uploaded ROM, not pre-shipped art.

Configuration the Flask app must provide:

- ``app.config["BRAGI_ATTACHMENTS_ROOT"]`` -- absolute path string to
  the attachments root (where ROMs live under ``zelda-roms/<site>/``).
- ``app.config["ZELDA_TEST_SITE_SLUG"]`` (test only) or production
  resolution via ``g.site.slug`` (Flask global set by bragi during
  request resolution).
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, abort, current_app, g

from bragi_theme_zelda.rom import get_sprite_png
from bragi_theme_zelda.rom.cache import MANIFESTS
from bragi_theme_zelda.rom.palettes import PALETTES

VALID_GAMES = frozenset(MANIFESTS.keys())
VALID_PALETTES = frozenset(PALETTES.keys())


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
    raw = current_app.config.get("BRAGI_ATTACHMENTS_ROOT")
    if not raw:
        abort(404)
    return Path(raw)


def build_rom_blueprint() -> Blueprint:
    """Construct the Flask blueprint serving ROM-extracted sprites."""
    bp = Blueprint("zelda_rom", __name__, url_prefix="/zelda/rom")

    @bp.route("/<game>/<palette>/<sprite_name>.png")
    def sprite(game: str, palette: str, sprite_name: str):  # type: ignore[no-untyped-def]
        # Validate enum-shaped path segments before any I/O.
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
        except (KeyError, OSError, IndexError):
            abort(404)

        return Response(png_bytes, mimetype="image/png")

    return bp
