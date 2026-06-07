"""Tests for the 2bpp GB tile decoder."""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import SpriteRef, render_sprite, render_tile
from bragi_theme_zelda.rom.palettes import PALETTE_DMG


def test_all_zeros_tile_decodes_to_all_zeros() -> None:
    rom = bytes(16)  # 16 bytes of zero = one all-index-0 tile at offset 0
    grid = render_tile(rom, 0)
    assert grid == [[0] * 8 for _ in range(8)]


def test_all_ones_tile_decodes_to_all_index_three() -> None:
    # Both bitplanes all-1 means every pixel decodes to index 3 (binary 11).
    rom = bytes([0xFF] * 16)
    grid = render_tile(rom, 0)
    assert grid == [[3] * 8 for _ in range(8)]


def test_low_bitplane_only_decodes_to_index_one() -> None:
    # Each row has low byte = 0xFF, high byte = 0x00.
    # Decoded: every pixel = (1 | (0 << 1)) = 1.
    rom = bytes([0xFF, 0x00] * 8)
    grid = render_tile(rom, 0)
    assert grid == [[1] * 8 for _ in range(8)]


def test_high_bitplane_only_decodes_to_index_two() -> None:
    # low byte = 0x00, high byte = 0xFF → every pixel = (0 | (1 << 1)) = 2.
    rom = bytes([0x00, 0xFF] * 8)
    grid = render_tile(rom, 0)
    assert grid == [[2] * 8 for _ in range(8)]


def test_leftmost_pixel_uses_high_bit_of_byte() -> None:
    # Row 0: low=0b10000000 (0x80), high=0b00000000 → leftmost pixel only is index 1
    rom = bytes([0x80, 0x00] + [0x00] * 14)
    grid = render_tile(rom, 0)
    assert grid[0] == [1, 0, 0, 0, 0, 0, 0, 0]


def test_decoder_respects_addr_offset() -> None:
    # Place a known tile at offset 16, expect decoder to read from there.
    rom = bytes(16) + bytes([0xFF] * 16) + bytes(16)
    grid = render_tile(rom, 16)
    assert grid == [[3] * 8 for _ in range(8)]


def test_single_tile_sprite_returns_8x8_image() -> None:
    rom = bytes([0xFF] * 16)
    ref = SpriteRef(rom_addr=0, tiles_w=1, tiles_h=1, transparent_bg=False)
    img = render_sprite(rom, ref, PALETTE_DMG)
    assert img.size == (8, 8)
    assert img.mode == "RGB"
    # Every pixel should be the darkest palette entry (index 3).
    expected = PALETTE_DMG[3]
    for y in range(8):
        for x in range(8):
            assert img.getpixel((x, y)) == expected


def test_two_by_two_sprite_returns_16x16_image() -> None:
    # 4 tiles of all-1s = a 16x16 sprite all darkest.
    rom = bytes([0xFF] * 64)
    ref = SpriteRef(rom_addr=0, tiles_w=2, tiles_h=2, transparent_bg=False)
    img = render_sprite(rom, ref, PALETTE_DMG)
    assert img.size == (16, 16)


def test_two_by_two_tile_order_is_row_major() -> None:
    # Build 4 distinct tiles: each tile is all one index.
    # Tile 0 (top-left)     = all index 0
    # Tile 1 (top-right)    = all index 1
    # Tile 2 (bottom-left)  = all index 2
    # Tile 3 (bottom-right) = all index 3
    def tile_for_index(idx: int) -> bytes:
        # low byte = bit 0 of idx repeated 8x; high byte = bit 1 repeated 8x.
        lo = 0xFF if (idx & 1) else 0x00
        hi = 0xFF if (idx & 2) else 0x00
        return bytes([lo, hi] * 8)

    rom = b"".join(tile_for_index(i) for i in range(4))
    ref = SpriteRef(rom_addr=0, tiles_w=2, tiles_h=2, transparent_bg=False)
    img = render_sprite(rom, ref, PALETTE_DMG)

    # Top-left quadrant should be PALETTE_DMG[0]; top-right [1]; etc.
    assert img.getpixel((0, 0)) == PALETTE_DMG[0]
    assert img.getpixel((8, 0)) == PALETTE_DMG[1]
    assert img.getpixel((0, 8)) == PALETTE_DMG[2]
    assert img.getpixel((8, 8)) == PALETTE_DMG[3]


def test_transparent_bg_turns_index_0_into_alpha_zero() -> None:
    rom = bytes(16)  # all-zeros tile = all index 0
    ref = SpriteRef(rom_addr=0, tiles_w=1, tiles_h=1, transparent_bg=True)
    img = render_sprite(rom, ref, PALETTE_DMG)
    assert img.mode == "RGBA"
    assert img.getpixel((0, 0)) == (0, 0, 0, 0)


def test_transparent_bg_keeps_other_indices_opaque() -> None:
    # All-1s tile = all index 3. Should be palette[3] with full alpha.
    rom = bytes([0xFF] * 16)
    ref = SpriteRef(rom_addr=0, tiles_w=1, tiles_h=1, transparent_bg=True)
    img = render_sprite(rom, ref, PALETTE_DMG)
    r, g, b = PALETTE_DMG[3]
    assert img.getpixel((0, 0)) == (r, g, b, 255)
