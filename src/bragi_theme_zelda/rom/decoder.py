"""GB 2bpp tile decoding and multi-tile sprite composition.

The decoder is pure pixel math operating on bytes; it has no knowledge
of ROM file format, banks, mappers, or storage. Higher layers
(``rom.__init__.get_sprite_png``, ``rom.cache``) compose this with the
manifest and storage to produce request-time PNGs.

Format reference: a GB tile is 8x8 pixels, stored as 16 bytes (8 rows,
2 bytes per row). Each row's two bytes are bitplanes: byte 0 holds the
low bit of each of the 8 pixels (leftmost pixel uses the high bit of
the byte), byte 1 holds the high bit. Pixel value is therefore one of
four indices (0..3).
"""

from __future__ import annotations


def render_tile(rom: bytes, addr: int) -> list[list[int]]:
    """Decode one 8x8 GB tile starting at ``rom[addr]`` (16 bytes long).

    Returns an 8-row, 8-column nested list of palette indices in 0..3.
    """
    rows: list[list[int]] = []
    for y in range(8):
        lo = rom[addr + 2 * y]
        hi = rom[addr + 2 * y + 1]
        row = [
            ((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)
            for x in range(8)
        ]
        rows.append(row)
    return rows
