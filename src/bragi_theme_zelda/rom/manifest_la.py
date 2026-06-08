"""Sprite manifest for the Link's Awakening (1993, Game Boy) ROM.

Each entry names a sprite that the theme expects to extract from an
operator-uploaded LA ROM. Adding a new sprite is a theme PR + minor
version bump, never a ROM re-upload -- the ROM is the operator's data;
the manifest is the theme's contract.

ROM offsets, geometries, and per-sprite render flags were tuned in the
v0.4.6 -> v0.4.8 cycle against a real LA-1993 ROM dump using
``_claude/scripts/sprite_explore.py``. The exploration found that the
LA-disassembly-derived spritesheet-group tables (zladx/LADX-Disassembly)
are *not* ground truth for original-LA: the agent's
"IndoorEntitySpritesheetsTable group $2F slot 3 = Npc2Tiles row 42 =
Tarin" was wrong; Tarin actually lives at Npc1Tiles row 14 ($38E00).
Per-sprite visual verification against the real ROM is the canonical
check, not the disassembly slot mapping.

Five render-time flags on ``SpriteRef`` (decoder.py) capture the
patterns we observed in the actual ROM data:

- ``oam_8x16``: multi-column NPC sprites are stored in 8x16 OAM-mode
  column-major order (``[col0_top, col0_bot, col1_top, col1_bot]``).
  Every 2-tile-wide sprite in this manifest sets it.
- ``mirror_right``: Nintendo stored symmetric sprites as the LEFT half
  only and used OAM x-flip to draw the right half. The heart container,
  owl (wings folded), and owl statue (wings spread) all live this way.
- ``palette_invert``: LA can drive sprites through OBP0 or OBP1; tiles
  drawn under OBP1 visually invert the palette indices. All four
  character portraits (Marin, Tarin, Owl, Ulrira) plus both owl-statue
  variants set this; the items (heart, rupee) don't.
- ``vstack_groups``: Grandpa Ulrira is taller than 16px and his sprite
  lives as two adjacent 2x2 OAM groups in ROM that the renderer stacks
  vertically. He's currently the only consumer.

The bonus discoveries from the v0.4.8 exploration -- Link-in-bed
sprites at ``$38D00`` (sleeping), ``$38D40`` (awake facing camera),
``$38D80`` (awake facing right) -- are documented in MEMORY.md for
future expansion (PUSH START splash already uses sleeping-Link
iconography; the home pause-menu could grow an awake-Link avatar).
Not in the v0.4.8 manifest.

Sprite-name convention: lowercase, underscore-separated, matches the
basename of the corresponding placeholder PNG under
``static/sprites/``. The placeholder-invariant test asserts manifest
keys are a subset of existing placeholder filenames.
"""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import SpriteRef

SPRITES_LA: dict[str, SpriteRef] = {
    # ----- Character portraits (palette_invert=True on all four) -----
    # Npc1Tiles row 15 ($38F00) position 0-3, the canonical walking-south
    # 2x2 portrait of Marin (tiles $60-$63).
    "marin": SpriteRef(
        rom_addr=0x38_F00,
        tiles_w=2,
        tiles_h=2,
        oam_8x16=True,
        palette_invert=True,
        label="Marin",
    ),
    # Npc1Tiles row 14 ($38E00) position 0-3, Tarin facing forward.
    # The agent's slot-table research had pointed at Npc2Tiles row 42;
    # that turned out to hold the sleep-Z icon, not Tarin. The actual
    # Tarin sprite shares Npc1Tiles row 14 with the Link-in-bed sprites
    # (positions 0-3 = Tarin forward, 4-7 = Tarin sleeping, 8-11 =
    # Tarin facing left). See MEMORY.md 2026-06-08 for the calibration.
    "tarin": SpriteRef(
        rom_addr=0x38_E00,
        tiles_w=2,
        tiles_h=2,
        oam_8x16=True,
        palette_invert=True,
        label="Tarin",
    ),
    # Wings-folded perched owl character ($3A280, position 8 of Npc1Tiles
    # row 34). Stored as the left half only (1x2 in ROM, mirrored on
    # render) with OBP1 palette inversion. This is the Wind Fish's
    # messenger in his iconic "perched on a branch giving advice" pose.
    "owl": SpriteRef(
        rom_addr=0x3A_280,
        tiles_w=1,
        tiles_h=2,
        mirror_right=True,
        palette_invert=True,
        label="Owl",
    ),
    # Two stacked 2x2 OAM groups at $44600 (Npc2Tiles row 6, positions
    # 0-3 and 4-7). Ulrira is tall enough that his sprite occupies two
    # 16x16 chunks vertically; vstack_groups=2 pulls $44600 and $44640
    # and stacks them. Final image is 16x32.
    "ulrira": SpriteRef(
        rom_addr=0x44_600,
        tiles_w=2,
        tiles_h=2,
        oam_8x16=True,
        palette_invert=True,
        vstack_groups=2,
        label="Grandpa Ulrira",
    ),
    # ----- Items -----
    # Green rupee drop sprite at tile $A6 ($30A60). 8x16, two tiles
    # stacked vertically (top of diamond, bottom of diamond). Not
    # mirrored — the diamond is symmetric but stored full, presumably
    # because the rupee in 8x16 OAM mode is a single OAM entry already.
    "rupee_green": SpriteRef(
        rom_addr=0x30_A60,
        tiles_w=1,
        tiles_h=2,
        label="Rupee (green)",
    ),
    # Heart container boss-drop sprite at tile $AA ($30AA0). Left half
    # only in ROM (1x2 = top-of-heart + bottom-of-heart), mirrored to
    # render the right half. Items render under OBP0 so no palette
    # invert.
    "heart_container": SpriteRef(
        rom_addr=0x30_AA0,
        tiles_w=1,
        tiles_h=2,
        mirror_right=True,
        label="Heart container",
    ),
    # Wings-spread owl statue at $3A2C0 (position 12 of Npc1Tiles row
    # 34). The dungeon stone-owl statue in its dramatic wings-out
    # pose, used as a Stone Beak destination. 2x2 in ROM stored as the
    # left half (so on-screen 32x16 after mirror). transparent_bg
    # stays True; the statue is rendered on the overworld with the
    # background showing through where the sprite has no opaque pixels.
    "owl_statue": SpriteRef(
        rom_addr=0x3A_2C0,
        tiles_w=2,
        tiles_h=2,
        oam_8x16=True,
        mirror_right=True,
        palette_invert=True,
        label="Owl Statue",
    ),
}

__all__ = ["SPRITES_LA"]
