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
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from markupsafe import Markup, escape

from bragi_theme_zelda.rom.manifest_la import SPRITES_LA


def make_rom_sprite_helpers(
    *,
    get_site: Callable[[], Any],
    static_prefix: str = "/static/sprites",
) -> tuple[Callable[..., Markup], Callable[..., str]]:
    """Build ``rom_sprite`` and ``rom_sprite_url`` helpers bound to ``get_site``."""

    def _placeholder_path(name: str) -> str:
        # Heuristic: portraits live under portraits/, items under items/, etc.
        # Walk the manifest label or fall back to items/.
        ref = SPRITES_LA[name]
        # Character names live in portraits/, items in items/.
        if name in {"marin", "tarin", "owl", "ulrira"}:
            sub = "portraits"
        else:
            sub = "items"
        _ = ref  # label is only used in admin UI; placeholder path uses name
        return f"{static_prefix}/{sub}/{name}.png"

    def rom_sprite_url(name: str, palette: str = "dmg") -> str:
        if name not in SPRITES_LA:
            raise KeyError(f"unknown sprite: {name!r}")
        site = get_site()
        sha = site.extra_settings.get("zelda_rom_la_sha256")
        if not sha:
            return _placeholder_path(name)
        return f"/zelda/rom/la/{palette}/{name}.png?v={sha[:12]}"

    def rom_sprite(name: str, alt: str = "") -> Markup:
        if name not in SPRITES_LA:
            raise KeyError(f"unknown sprite: {name!r}")
        site = get_site()
        sha = site.extra_settings.get("zelda_rom_la_sha256")
        safe_alt = escape(alt)
        if not sha:
            src = _placeholder_path(name)
            return Markup(f'<img src="{src}" alt="{safe_alt}" class="rom-sprite">')
        v = sha[:12]
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
