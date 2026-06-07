"""Synthetic ROM byte builders for tests.

Nothing here is taken from or derived from a real LA cartridge. The
title bytes ``b"ZELDA"`` are a 5-character ASCII string we write
literally to satisfy our upload-validation title-prefix check; the
cartridge type byte 0x03 is a hardware constant defined in the GB
technical specification; the checkerboard tile is geometric.
"""

from __future__ import annotations

from bragi_theme_zelda.rom.decoder import SpriteRef


def checkerboard_tile() -> bytes:
    """An 8x8 checkerboard tile in 2bpp format.

    Alternating rows of 4-pixel runs at index 3 followed by 4-pixel
    runs at index 0 (and vice versa on the next row). With both
    bitplanes equal, each pixel is either index 0 (binary 00) or
    index 3 (binary 11) — no mid-tone indices.
    """
    out = bytearray()
    for y in range(8):
        pattern = 0b1111_0000 if y % 2 == 0 else 0b0000_1111
        # Low bitplane = high bitplane -> each lit pixel decodes to index 3
        # and each dark pixel to index 0.
        out.extend([pattern, pattern])
    return bytes(out)


def build_fixture_rom(tile_at_0x10000: bytes | None = None) -> bytes:
    """Construct a synthetic 1 MB GB-shaped ROM that passes our upload
    validator.

    The header at 0x0100-0x014F satisfies::

        title starts with b"ZELDA"          (offset 0x0134)
        cartridge type == 0x03 (MBC1+RAM+BATTERY)  (offset 0x0147)

    If a tile is supplied via ``tile_at_0x10000`` (16 bytes), it is
    placed at offset 0x10000. The default (None) leaves that region as
    zeros (which decodes to an all-index-0 tile).
    """
    rom = bytearray(0x100000)  # 1 MB zeros
    rom[0x0134:0x013F] = b"ZELDA\x00\x00\x00\x00\x00\x00"  # 11 bytes title region
    rom[0x0147] = 0x03  # MBC1+RAM+BATTERY
    if tile_at_0x10000 is not None:
        assert len(tile_at_0x10000) == 16, "tile must be 16 bytes (one 8x8 2bpp tile)"
        rom[0x10000 : 0x10000 + 16] = tile_at_0x10000
    return bytes(rom)


# Used by tests/unit/test_rom_cache.py and tests/integration/test_rom_route.py.
# The fixture tile lives at offset 0x10000 in the synthetic ROM; this entry
# names that offset so test code can ask for sprite ``_fixture_tile`` and
# get back the checkerboard tile rendered through the normal pipeline.
FIXTURE_TILE_REF = SpriteRef(
    rom_addr=0x10000,
    tiles_w=1,
    tiles_h=1,
    transparent_bg=False,
    label="Fixture tile",
)
