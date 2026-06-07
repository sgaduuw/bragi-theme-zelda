"""Tests for the LRU-cached public extraction API."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from bragi_theme_zelda.rom import get_sprite_png
from bragi_theme_zelda.rom.cache import _cache_clear
from bragi_theme_zelda.rom.upload import store_rom
from tests.data.rom_fixtures import build_fixture_rom, checkerboard_tile


@pytest.fixture(autouse=True)
def clear_cache_between_tests() -> None:
    _cache_clear()


def test_get_sprite_png_returns_png_bytes(tmp_path: Path) -> None:
    rom = build_fixture_rom(tile_at_0x10000=checkerboard_tile())
    store_rom(rom, attachments_root=tmp_path, site_slug="s", game="la")

    png = get_sprite_png(
        attachments_root=tmp_path,
        site_slug="s",
        game="la",
        palette="dmg",
        sprite_name="_fixture_tile",  # special test-only entry
    )
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_sprite_png_caches_repeated_calls(tmp_path: Path) -> None:
    rom = build_fixture_rom(tile_at_0x10000=checkerboard_tile())
    store_rom(rom, attachments_root=tmp_path, site_slug="s", game="la")

    a = get_sprite_png(tmp_path, "s", "la", "dmg", "_fixture_tile")
    b = get_sprite_png(tmp_path, "s", "la", "dmg", "_fixture_tile")
    assert a is b  # identical object -> served from LRU


def test_get_sprite_png_different_palettes_cache_separately(tmp_path: Path) -> None:
    rom = build_fixture_rom(tile_at_0x10000=checkerboard_tile())
    store_rom(rom, attachments_root=tmp_path, site_slug="s", game="la")

    dmg = get_sprite_png(tmp_path, "s", "la", "dmg", "_fixture_tile")
    pocket = get_sprite_png(tmp_path, "s", "la", "pocket", "_fixture_tile")
    assert dmg != pocket  # different palettes -> different PNG bytes


def test_get_sprite_png_unknown_sprite_raises_keyerror(tmp_path: Path) -> None:
    rom = build_fixture_rom()
    store_rom(rom, attachments_root=tmp_path, site_slug="s", game="la")
    with pytest.raises(KeyError):
        get_sprite_png(tmp_path, "s", "la", "dmg", "no_such_sprite")


def test_swapping_rom_at_same_path_returns_new_bytes(tmp_path: Path) -> None:
    """Regression: post-swap reads must reflect the new ROM, not the LRU.

    Covers the multi-worker staleness gap (issue #25): mtime is part of
    the cache key, so an atomic replacement at the same path produces a
    fresh entry on the next request. No _cache_clear() call between
    requests, mimicking another worker that didn't handle the upload.
    """
    rom_a = build_fixture_rom(tile_at_0x10000=bytes([0xFF] * 16))
    rom_b = build_fixture_rom(tile_at_0x10000=bytes([0x00] * 16))

    store_rom(rom_a, attachments_root=tmp_path, site_slug="s", game="la")
    a = get_sprite_png(tmp_path, "s", "la", "dmg", "_fixture_tile")

    # Sleep just long enough to guarantee a measurable mtime delta on
    # filesystems with millisecond (or coarser) mtime resolution.
    # macOS APFS and ext4 both have ns resolution but some FS round.
    time.sleep(0.01)
    store_rom(rom_b, attachments_root=tmp_path, site_slug="s", game="la")
    b = get_sprite_png(tmp_path, "s", "la", "dmg", "_fixture_tile")

    assert a != b, "Cache returned stale bytes after ROM swap -- mtime not in key?"
