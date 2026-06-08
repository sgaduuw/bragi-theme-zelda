"""Jinja template helpers for ROM-extracted sprites.

Two helpers, returned together from :func:`make_rom_sprite_helpers`
so they share a site-lookup callable:

- ``rom_sprite(name, alt='')`` returns a ``<picture>`` element with
  ``dmg`` and ``pocket`` variants when a ROM is uploaded, or a plain
  ``<img>`` pointing at the static placeholder when not.
- ``rom_sprite_url(name, palette='dmg')`` returns just the URL string,
  for cases that need to construct the element manually (inline CSS
  background-image, JS, etc.).

The factory pattern keeps the helpers testable without Flask globals.

Names not in :data:`SPRITES_LA` (decorative-only sprites like
``la_pearl``, ``kokiri_emerald``, ``triforce_piece``) fall back to the
static placeholder path rather than raising. Anything ROM-extractable
is in the manifest by construction; anything outside it can never be
ROM-extracted regardless of whether a ROM is uploaded.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from markupsafe import Markup, escape

from bragi_theme_zelda.rom.manifest_la import SPRITES_LA

try:
    THEME_VERSION: str = version("bragi-theme-zelda")
except PackageNotFoundError:
    # Editable / source-checkout fallback; only reachable before
    # `poetry install` records the dist-info. Tests run after install
    # so they get the real version.
    THEME_VERSION = "dev"


def _cache_buster(rom_sha: str) -> str:
    """Compose the ``?v=`` value mixing ROM SHA and theme version.

    Closes #68: the previous ``?v={sha[:12]}`` invalidated browser
    cache on ROM swap but not on theme upgrade. Manifest changes
    between theme versions (addresses, geometries, render flags)
    produce different PNG bytes at the same URL; with
    ``Cache-Control: ..., immutable`` browsers would serve the old
    bytes for 24h. Adding the theme version makes every theme bump
    auto-invalidate the relevant URLs.
    """
    return f"{rom_sha[:12]}-{THEME_VERSION}"


def make_rom_sprite_helpers(
    *,
    get_site: Callable[[], Any],
    static_prefix: str = "/theme/zelda/static/sprites",
) -> tuple[Callable[..., Markup], Callable[..., str]]:
    """Build ``rom_sprite`` and ``rom_sprite_url`` helpers bound to ``get_site``.

    ``static_prefix`` is the URL prefix at which bragi mounts the
    theme's ``static_dir``. Default matches bragi's
    ``/theme/<slug>/static/sprites`` convention for the zelda theme.
    """

    def _placeholder_path(name: str) -> str:
        # Heuristic: known character names live in portraits/, everything
        # else (items, decorative sprites) in items/. The classification
        # matches the on-disk static-sprite layout.
        if name in {"marin", "tarin", "owl", "ulrira"}:
            sub = "portraits"
        else:
            sub = "items"
        return f"{static_prefix}/{sub}/{name}.png"

    def rom_sprite_url(name: str, palette: str = "dmg") -> str:
        # Names outside the manifest are decorative-only and resolve
        # directly to their placeholder file; the ROM extraction
        # pipeline cannot produce them regardless of upload state.
        if name not in SPRITES_LA:
            return _placeholder_path(name)
        site = get_site()
        sha = site.extra_settings.get("zelda_rom_la_sha256")
        if not sha:
            return _placeholder_path(name)
        return f"/zelda/rom/la/{palette}/{name}.png?v={_cache_buster(sha)}"

    def rom_sprite(name: str, alt: str = "") -> Markup:
        safe_alt = escape(alt)
        # Same manifest-membership check as rom_sprite_url: not in
        # manifest → static <img> only, no <picture> variants.
        if name not in SPRITES_LA:
            src = _placeholder_path(name)
            return Markup(f'<img src="{src}" alt="{safe_alt}" class="rom-sprite">')
        site = get_site()
        sha = site.extra_settings.get("zelda_rom_la_sha256")
        if not sha:
            src = _placeholder_path(name)
            return Markup(f'<img src="{src}" alt="{safe_alt}" class="rom-sprite">')
        v = _cache_buster(sha)
        dark_src = f"/zelda/rom/la/pocket/{name}.png?v={v}"
        light_src = f"/zelda/rom/la/dmg/{name}.png?v={v}"
        return Markup(
            f"<picture>"
            f'<source media="(prefers-color-scheme: dark)" srcset="{dark_src}">'
            f'<img src="{light_src}" alt="{safe_alt}" '
            f'class="rom-sprite" loading="lazy">'
            f"</picture>"
        )

    return rom_sprite, rom_sprite_url
