"""Four-shade palettes for GB sprite rendering.

GB tiles store one of four index values (0..3) per pixel. The palette
maps those indices to RGB triples. Index 0 is the lightest shade
(typically the transparent background), index 3 is the darkest.

Two palettes ship: ``PALETTE_DMG`` (the original Game Boy LCD green
range) for light mode, and ``PALETTE_POCKET`` (Game Boy Pocket
greyscale) for dark mode. See CONTEXT.md "Why GB Pocket greyscale,
not invert" for why both exist.
"""

from __future__ import annotations

Rgb = tuple[int, int, int]
Palette = tuple[Rgb, Rgb, Rgb, Rgb]

PALETTE_DMG: Palette = (
    (0x9B, 0xBC, 0x0F),  # lightest LCD green
    (0x8B, 0xAC, 0x0F),
    (0x30, 0x62, 0x30),
    (0x0F, 0x38, 0x0F),  # darkest LCD green
)

PALETTE_POCKET: Palette = (
    (0xE0, 0xDB, 0xCD),  # lightest pocket grey
    (0xA8, 0xA3, 0x95),
    (0x70, 0x6B, 0x5E),
    (0x2B, 0x29, 0x21),  # near-black
)

PALETTES: dict[str, Palette] = {
    "dmg": PALETTE_DMG,
    "pocket": PALETTE_POCKET,
}

__all__ = ["PALETTES", "PALETTE_DMG", "PALETTE_POCKET", "Palette", "Rgb"]
