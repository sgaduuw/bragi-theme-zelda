"""In-process LRU wrapper around the extraction pipeline.

The cache key is (site_slug, game, palette, sprite_name). Per-process;
multi-worker deployments do not coordinate. Cost of a miss is sub-
millisecond and PNG bytes are small (~2 KB), so duplicating the cache
across workers is cheap. Restart -> cache empties; browsers continue
serving from their own HTTP cache.

Invalidation is the writer's responsibility: the cache is keyed by
ROM path, not by ROM content. After every ``store_rom`` /
``rom_path_for_site(...).unlink()`` (i.e. every operator-initiated
upload, replace, or delete via the admin Blueprint), the caller MUST
call ``_cached_png.cache_clear()`` to avoid serving stale bytes from
the previous ROM at the same path. See ``admin/routes.py`` for the
production wiring.

The fixture-tile entry ``_fixture_tile`` is exposed only when the
test data module is importable (it lives in ``tests/data/``). In
production deployments, the lookup raises KeyError naturally because
the manifest doesn't include it.
"""

from __future__ import annotations

import functools
import io
from pathlib import Path

from PIL import Image

from bragi_theme_zelda.rom.decoder import SpriteRef, render_sprite
from bragi_theme_zelda.rom.manifest_la import SPRITES_LA
from bragi_theme_zelda.rom.palettes import PALETTES, Palette
from bragi_theme_zelda.rom.upload import rom_path_for_site

MANIFESTS: dict[str, dict[str, SpriteRef]] = {"la": SPRITES_LA}


def _resolve_sprite_ref(game: str, sprite_name: str) -> SpriteRef:
    """Look up a SpriteRef; raise KeyError if unknown."""
    if game not in MANIFESTS:
        raise KeyError(f"unknown game: {game!r}")
    manifest = MANIFESTS[game]
    if sprite_name not in manifest:
        # Lazy-import test fixture overlay so production deployments don't
        # depend on the test data module.
        try:
            from tests.data.rom_fixtures import FIXTURE_TILE_REF

            if sprite_name == "_fixture_tile":
                return FIXTURE_TILE_REF
        except ImportError:
            pass
        raise KeyError(f"unknown sprite for game {game!r}: {sprite_name!r}")
    return manifest[sprite_name]


@functools.lru_cache(maxsize=32)
def _cached_png(
    rom_path_str: str, game: str, palette_name: str, sprite_name: str
) -> bytes:
    """Cache key is a string-tuple so it hashes cleanly through lru_cache."""
    rom = Path(rom_path_str).read_bytes()
    ref = _resolve_sprite_ref(game, sprite_name)
    palette: Palette = PALETTES[palette_name]
    img: Image.Image = render_sprite(rom, ref, palette)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def get_sprite_png(
    attachments_root: Path,
    site_slug: str,
    game: str,
    palette: str,
    sprite_name: str,
) -> bytes:
    """Public extraction API. Returns PNG bytes for one named sprite.

    May raise: ``KeyError`` (unknown sprite/game/palette),
    ``FileNotFoundError`` (no ROM stored for site), ``IndexError``
    (manifest offset out of bounds in this ROM -- caller logs and 404s).
    """
    if palette not in PALETTES:
        raise KeyError(f"unknown palette: {palette!r}")
    # Verify the ROM file exists before checking the LRU (a different
    # ROM at the same path would produce wrong results from a stale entry).
    rom_path = read_rom_path(attachments_root, site_slug, game)
    return _cached_png(str(rom_path), game, palette, sprite_name)


def read_rom_path(attachments_root: Path, site_slug: str, game: str) -> Path:
    """Return the rom path, raising FileNotFoundError if it does not exist."""
    path = rom_path_for_site(attachments_root, site_slug, game)
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path


def _cache_clear() -> None:
    """Clear the LRU. For test isolation."""
    _cached_png.cache_clear()
