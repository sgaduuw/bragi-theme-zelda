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
        With ``mirror_right`` set, ``tiles_w`` describes the LEFT half
        that lives in ROM; rendered output ends up ``tiles_w * 2`` wide.
        With ``vstack_groups > 1``, the per-2x2-group geometry is
        ``tiles_w x tiles_h`` and rendered output ends up
        ``tiles_h * vstack_groups`` tall.
    transparent_bg
        GB OBJ convention: palette index 0 is rendered as transparent
        (alpha 0) so the sprite can be composited over arbitrary
        backgrounds. Set to ``False`` for tiles meant to be opaque
        (e.g. tilemap chunks used as standalone art).
    oam_8x16
        LA stores multi-column NPC sprites in 8x16 OAM-mode column-major
        order: tiles in ROM are ``[col0_top, col0_bot, col1_top,
        col1_bot, ...]`` (vertical pair first, then move right). The
        default ``False`` keeps the historical row-major iteration
        (``tile_idx = ty * tiles_w + tx``) used by single-tile and
        single-column extractions and by the fixture-based decoder
        tests. Set ``True`` on multi-column sprites authored in 8x16
        OAM mode (i.e. virtually every LA character portrait and most
        item icons) to swap to column-major iteration; for
        ``tiles_w == 1`` the two orderings are identical so the flag
        is a no-op.
    mirror_right
        Nintendo aggressively used OAM x-flip on 1MB-and-smaller carts
        to halve the ROM footprint of symmetric sprites. When set, the
        manifest declares the LEFT half only and the renderer composes
        the right half by horizontally mirroring the left column.
        Final image is ``tiles_w * 2`` * 8 wide. The heart container,
        owl statue (wings spread), and owl character (wings folded) all
        live in ROM as mirror-storage in the original LA dump.
    palette_invert
        LA can drive sprites through either OBP0 or OBP1; an OAM
        attribute bit picks which palette renders any given OBJ tile.
        Tiles drawn under OBP1 visually have their palette indices
        inverted relative to tiles drawn under OBP0. Since the decoder
        operates on raw pixel bytes (which don't know about OAM
        attributes), this flag tells the manifest "render with
        indices swapped (0<->3, 1<->2)". All four character portraits
        (Marin, Tarin, Owl, Ulrira) plus both owl-statue variants set
        this; the items (heart, rupee) don't.
    vstack_groups
        Some LA NPCs occupy more than one 2x2 OAM 8x16 sprite group on
        screen (Grandpa Ulrira is tall enough to need two groups
        stacked). When > 1, the renderer pulls ``N`` consecutive 2x2
        groups from offsets ``rom_addr + g * 64`` and stacks them
        vertically. Each group is rendered using ``tiles_w x tiles_h``
        (typically 2x2) and the standard flags above. The default ``1``
        means a single group is rendered (no stacking). Ignored unless
        ``tiles_w == 2 and tiles_h == 2``.
    label
        Human-readable label for the admin sprite-preview grid.
    """

    rom_addr: int
    tiles_w: int
    tiles_h: int
    transparent_bg: bool = True
    oam_8x16: bool = False
    mirror_right: bool = False
    palette_invert: bool = False
    vstack_groups: int = 1
    label: str = ""


def _invert_palette(p: Palette) -> Palette:
    """Swap 0<->3, 1<->2 in the 4-entry palette tuple."""
    return (p[3], p[2], p[1], p[0])


def _render_one_group(
    rom: bytes,
    addr: int,
    tiles_w: int,
    tiles_h: int,
    transparent_bg: bool,
    oam_8x16: bool,
    palette: Palette,
) -> Image.Image:
    """Render a single 2D tile block at ``addr``.

    Internal helper. Public callers go through ``render_sprite`` which
    applies the per-SpriteRef composition flags (mirror_right,
    vstack_groups, palette_invert).
    """
    w, h = tiles_w * 8, tiles_h * 8
    mode = "RGBA" if transparent_bg else "RGB"
    img = Image.new(mode, (w, h))
    px = img.load()
    assert px is not None  # PIL.Image.new always returns a loadable image.

    for ty in range(tiles_h):
        for tx in range(tiles_w):
            if oam_8x16:
                tile_idx = tx * tiles_h + ty
            else:
                tile_idx = ty * tiles_w + tx
            tile_addr = addr + tile_idx * 16
            tile = render_tile(rom, tile_addr)
            for y in range(8):
                for x in range(8):
                    idx = tile[y][x]
                    if transparent_bg and idx == 0:
                        px[tx * 8 + x, ty * 8 + y] = (0, 0, 0, 0)
                    elif transparent_bg:
                        r, g, b = palette[idx]
                        px[tx * 8 + x, ty * 8 + y] = (r, g, b, 255)
                    else:
                        px[tx * 8 + x, ty * 8 + y] = palette[idx]

    return img


def render_sprite(rom: bytes, ref: SpriteRef, palette: Palette) -> Image.Image:
    """Compose a multi-tile sprite from its 8x8 tiles.

    Tiles live as a contiguous run starting at ``ref.rom_addr``. The
    in-ROM ordering depends on ``ref.oam_8x16``: when ``False``
    (default), tiles are read row-major (TL, TR, BL, BR for a 2x2);
    when ``True``, column-major (TL, BL, TR, BR), matching LA's 8x16
    OAM-mode storage convention for character portraits and most
    item icons.

    Composition flags applied after the base render:

    - ``ref.palette_invert``: swap palette indices (0<->3, 1<->2)
      before any tile decode, matching LA's OBP1 sprite-rendering
      path.
    - ``ref.vstack_groups``: when > 1, render that many consecutive
      2x2 groups from offsets ``rom_addr + g * 64`` and stack them
      vertically. Only honoured when tiles_w == tiles_h == 2.
    - ``ref.mirror_right``: after stacking, double the image width
      by pasting a horizontally-flipped copy of the rendered left
      half to the right. Matches Nintendo's OAM x-flip storage
      convention for symmetric sprites.
    """
    palette = _invert_palette(palette) if ref.palette_invert else palette

    if ref.vstack_groups > 1 and ref.tiles_w == 2 and ref.tiles_h == 2:
        groups = [
            _render_one_group(
                rom,
                ref.rom_addr + g * 64,
                ref.tiles_w,
                ref.tiles_h,
                ref.transparent_bg,
                ref.oam_8x16,
                palette,
            )
            for g in range(ref.vstack_groups)
        ]
        gw, gh = groups[0].size
        stacked = Image.new(groups[0].mode, (gw, gh * len(groups)))
        for i, g in enumerate(groups):
            if g.mode == "RGBA":
                stacked.paste(g, (0, i * gh), g)
            else:
                stacked.paste(g, (0, i * gh))
        left = stacked
    else:
        left = _render_one_group(
            rom,
            ref.rom_addr,
            ref.tiles_w,
            ref.tiles_h,
            ref.transparent_bg,
            ref.oam_8x16,
            palette,
        )

    if not ref.mirror_right:
        return left

    lw, lh = left.size
    out = Image.new(left.mode, (lw * 2, lh))
    if left.mode == "RGBA":
        out.paste(left, (0, 0), left)
        flipped = left.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        out.paste(flipped, (lw, 0), flipped)
    else:
        out.paste(left, (0, 0))
        out.paste(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (lw, 0))
    return out
