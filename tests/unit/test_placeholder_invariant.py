"""Invariant: every sprite in the manifest has a corresponding placeholder PNG.

The placeholder is what the helper serves when no ROM is uploaded.
This invariant catches the easy mistake of adding a manifest entry
without shipping a placeholder, which would render a broken-image
icon to every visitor of an unconfigured site.
"""

from __future__ import annotations

from importlib.resources import files

from bragi_theme_zelda.rom.manifest_la import SPRITES_LA

_STATIC = files("bragi_theme_zelda") / "static" / "sprites"


def _existing_placeholder_basenames() -> set[str]:
    """All placeholder PNG basenames (without extension), recursively."""
    found: set[str] = set()
    # importlib.resources.files returns Traversable; iterate via .iterdir().
    for sub in ("portraits", "items", "ui"):
        directory = _STATIC / sub
        if directory.is_dir():
            for entry in directory.iterdir():
                name = entry.name
                if name.endswith(".png"):
                    found.add(name.removesuffix(".png"))
    return found


def test_every_manifest_sprite_has_a_placeholder() -> None:
    manifest_keys = set(SPRITES_LA.keys())
    placeholders = _existing_placeholder_basenames()
    missing = manifest_keys - placeholders
    assert not missing, (
        f"Manifest sprites without a placeholder PNG: {missing}. "
        f"Add static/sprites/{{portraits,items,ui}}/<name>.png for each, "
        f"or remove from SPRITES_LA."
    )
