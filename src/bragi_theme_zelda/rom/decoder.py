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

from dataclasses import dataclass

from PIL import Image

from bragi_theme_zelda.rom.palettes import Palette


def render_tile(rom: bytes, addr: int) -> list[list[int]]:
    """Decode one 8x8 GB tile starting at ``rom[addr]`` (16 bytes long).

    Returns an 8-row, 8-column nested list of palette indices in 0..3.
    """
    rows: list[list[int]] = []
    for y in range(8):
        lo = rom[addr + 2 * y]
        hi = rom[addr + 2 * y + 1]
        row = [((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1) for x in range(8)]
        rows.append(row)
    return rows


@dataclass(frozen=True)
class SpriteRef:
    """A reference to one named sprite inside an LA ROM file.

    Attributes
    ----------
    rom_addr
        Absolute byte offset in the .gb file where the first tile starts.
    tiles_w, tiles_h
        Sprite dimensions in 8x8 tiles. A 16x16 NPC sprite is 2x2 tiles.
    transparent_bg
        GB OBJ convention: palette index 0 is rendered as transparent
        (alpha 0) so the sprite can be composited over arbitrary
        backgrounds. Set to ``False`` for tiles meant to be opaque
        (e.g. tilemap chunks used as standalone art).
    label
        Human-readable label for the admin sprite-preview grid.
    """

    rom_addr: int
    tiles_w: int
    tiles_h: int
    transparent_bg: bool = True
    label: str = ""


def render_sprite(rom: bytes, ref: SpriteRef, palette: Palette) -> Image.Image:
    """Compose a multi-tile sprite from its row-major 8x8 tiles.

    Tiles are laid out in the ROM as a contiguous run starting at
    ``ref.rom_addr``, in row-major order: top-left, top-right,
    bottom-left, bottom-right for a 2x2 sprite.
    """
    w, h = ref.tiles_w * 8, ref.tiles_h * 8
    mode = "RGBA" if ref.transparent_bg else "RGB"
    img = Image.new(mode, (w, h))
    px = img.load()
    assert px is not None  # PIL.Image.new always returns a loadable image.

    for ty in range(ref.tiles_h):
        for tx in range(ref.tiles_w):
            tile_idx = ty * ref.tiles_w + tx
            tile_addr = ref.rom_addr + tile_idx * 16
            tile = render_tile(rom, tile_addr)
            for y in range(8):
                for x in range(8):
                    idx = tile[y][x]
                    if ref.transparent_bg and idx == 0:
                        px[tx * 8 + x, ty * 8 + y] = (0, 0, 0, 0)
                    elif ref.transparent_bg:
                        r, g, b = palette[idx]
                        px[tx * 8 + x, ty * 8 + y] = (r, g, b, 255)
                    else:
                        px[tx * 8 + x, ty * 8 + y] = palette[idx]

    return img
