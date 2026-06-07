"""Sprite manifest for the Link's Awakening (1993, Game Boy) ROM.

Each entry names a sprite that the theme expects to extract from an
operator-uploaded LA ROM. Adding a new sprite is a theme PR + minor
version bump, never a ROM re-upload -- the ROM is the operator's data;
the manifest is the theme's contract.

ROM offsets are absolute byte positions in the .gb file, sourced from
the LA disassemblies and verified to land on the right tile data:

- Primary semantic source: github.com/zladx/LADX-Disassembly. That
  project targets LA DX (1998 GBC) but the NPC tile banks (Npc1Tiles
  bank $0E, Npc2Tiles bank $11) have identical layout in the original
  1993 ROM -- the engine added colour but did not reshuffle these
  banks.
- Cross-verified against github.com/jverkoey/windfish's
  ``projects/Links_Awakening_gb.windfish`` (commit
  7437552 / depth-1 clone). windfish's bank_08.asm contains the same
  IndoorEntitySpritesheetsTable / OverworldEntitySpritesheetsTable
  4-byte group entries byte-for-byte, confirming the spritesheet
  indexing scheme is shared between LA-1993 and LA-DX.
- Computation: ``rom_addr = bank * 0x4000 + offset_in_bank``. The
  spritesheet group encoding is ``bbtttttt`` where ``bb`` indexes
  into NpcTilesBankTable (``$00, $11, $0E, $12``) and ``tttttt`` is
  the 16-tile row number within the bank; row offset = ``row * 0x100``.

Two geometry caveats from the research:

- ``owl`` extracts the walking sprite (tiles $78-$7B, contiguous 2x2)
  at the base of Npc1Tiles row 34, not the dialogue sprite (tiles
  $7C and $7E, non-contiguous and not extractable as a contiguous
  block).
- ``owl_statue`` is rendered in-game as a 1-wide x 4-tall column in
  8x16 OAM mode; tiles_h=4 (rather than 2) matches the actual art.

Sprite-name convention: lowercase, underscore-separated, matches the
basename of the corresponding placeholder PNG under
``static/sprites/``. v0.1.6 placeholders use names like "marin",
"tarin", "owl", "ulrira"; this manifest uses those same names so the
placeholder-invariant test can assert manifest_keys is a subset of
existing placeholder filenames.
"""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import SpriteRef

SPRITES_LA: dict[str, SpriteRef] = {
    # Character portraits (16x16 NPC sprites, 2x2 tiles).
    # IndoorEntitySpritesheetsTable group $2F slot 2 = $8F = Npc1Tiles
    # row 15 ($38000 + 15 * $100). Marin's walking-south 2x2 portrait
    # occupies tiles $60-$63 at positions 0-3 of that row.
    "marin": SpriteRef(
        rom_addr=0x38_F00,
        tiles_w=2,
        tiles_h=2,
        label="Marin",
    ),
    # IndoorEntitySpritesheetsTable group $2F slot 3 = $6A = Npc2Tiles
    # row 42 ($44000 + 42 * $100). Tarin's walking-south portrait sits
    # at positions 8-11 (tiles $78-$7B), so the 2x2 block starts at
    # offset +$80 from the row base.
    "tarin": SpriteRef(
        rom_addr=0x46_A80,
        tiles_w=2,
        tiles_h=2,
        label="Tarin",
    ),
    # OverworldEntitySpritesheetsTable group $07 slot 3 = $A2 =
    # Npc1Tiles row 34 ($38000 + 34 * $100). Owl's walking sprite is
    # contiguous tiles $78-$7B at positions 0-3. (The dialogue sprite
    # uses non-contiguous tiles $7C/$7E and cannot be extracted as a
    # single contiguous block.)
    "owl": SpriteRef(
        rom_addr=0x3A_200,
        tiles_w=2,
        tiles_h=2,
        label="Owl",
    ),
    # IndoorEntitySpritesheetsTable group $09 slot 3 = $46 = Npc2Tiles
    # row 6 ($44000 + 6 * $100). Ulrira's walking-south 2x2 portrait
    # is at positions 0-3 (tiles $70-$73).
    "ulrira": SpriteRef(
        rom_addr=0x44_600,
        tiles_w=2,
        tiles_h=2,
        label="Grandpa Ulrira",
    ),
    # Items (8x8 inventory icons or 16x16 world objects).
    # InventoryEquipmentItemsTiles base = bank $0C offset $800 = $30800.
    # Tile $AA (heart container) at +$2A0; tile $A6 (rupee) at +$260.
    # DroppableHeartContainerSpriteVariants in bank3.asm references
    # tile $AA; DroppableRupeeSprite references tile $A6.
    "heart_container": SpriteRef(
        rom_addr=0x30_AA0,
        tiles_w=1,
        tiles_h=1,
        label="Heart container",
    ),
    "rupee_green": SpriteRef(
        rom_addr=0x30_A60,
        tiles_w=1,
        tiles_h=1,
        label="Rupee (green)",
    ),
    # IndoorEntitySpritesheetsTable group $07 slot 1 = $91 = Npc1Tiles
    # row 17 ($38000 + 17 * $100). Owl Statue is rendered as a 1x4
    # vertical column in 8x16 OAM mode, so tiles_h=4 (not 2) matches
    # the in-game silhouette. Extraction reads tiles $50-$53 (top half
    # of the four 8x16 paired chunks $50/$51, $52/$53); rendering as
    # 1x4 stacks them vertically.
    "owl_statue": SpriteRef(
        rom_addr=0x39_100,
        tiles_w=1,
        tiles_h=4,
        transparent_bg=False,
        label="Owl Statue",
    ),
}

__all__ = ["SPRITES_LA"]
