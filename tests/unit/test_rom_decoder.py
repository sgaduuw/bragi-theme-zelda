"""Tests for the 2bpp GB tile decoder."""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import render_tile


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
