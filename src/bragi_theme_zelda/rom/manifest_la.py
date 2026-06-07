"""Sprite manifest for the Link's Awakening (1993, Game Boy) ROM.

Each entry names a sprite that the theme expects to extract from an
operator-uploaded LA ROM. Adding a new sprite is a theme PR + minor
version bump, never a ROM re-upload -- the ROM is the operator's data;
the manifest is the theme's contract.

ROM offsets are absolute byte positions in the .gb file. Values below
are PLACEHOLDERS to be replaced with addresses sourced from the LA
disassembly (github.com/zladx/LADX-Disassembly) during implementation
of Task 5b. Leaving them as placeholders during initial development is
fine -- the extraction pipeline works against the fixture ROM, and the
real values are filled in once the disassembly research lands.

Sprite-name convention: lowercase, underscore-separated, matches the
basename of the corresponding placeholder PNG under
``static/sprites/``. v0.1.6 placeholders use names like "marin",
"tarin", "owl", "ulrira"; this manifest uses those same names so the
placeholder-invariant test in Task 10 can assert manifest_keys subset
existing placeholder filenames.
"""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import SpriteRef

# Character portraits (16x16 NPC sprites, 2x2 tiles).
# rom_addr is a placeholder; fill in from LA disassembly during Task 5b.
SPRITES_LA: dict[str, SpriteRef] = {
    "marin": SpriteRef(
        rom_addr=0x68_2A0,
        tiles_w=2,
        tiles_h=2,
        label="Marin",
    ),
    "tarin": SpriteRef(
        rom_addr=0x68_3E0,
        tiles_w=2,
        tiles_h=2,
        label="Tarin",
    ),
    "owl": SpriteRef(
        rom_addr=0x68_520,
        tiles_w=2,
        tiles_h=2,
        label="Owl",
    ),
    "ulrira": SpriteRef(
        rom_addr=0x69_120,
        tiles_w=2,
        tiles_h=2,
        label="Grandpa Ulrira",
    ),
    # Items (8x8 inventory icons or 16x16 world objects).
    "heart_container": SpriteRef(
        rom_addr=0x36_4A0,
        tiles_w=1,
        tiles_h=1,
        label="Heart container",
    ),
    "rupee_green": SpriteRef(
        rom_addr=0x36_5C0,
        tiles_w=1,
        tiles_h=1,
        label="Rupee (green)",
    ),
    "owl_statue": SpriteRef(
        rom_addr=0x4A_280,
        tiles_w=2,
        tiles_h=2,
        transparent_bg=False,
        label="Owl Statue",
    ),
}

__all__ = ["SPRITES_LA"]
