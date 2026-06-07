"""Tests for LA ROM upload header validation and atomic file storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from bragi_theme_zelda.rom.upload import (
    RomValidationError,
    read_rom,
    rom_path_for_site,
    store_rom,
    validate_la_rom,
)
from tests.data.rom_fixtures import build_fixture_rom


def test_valid_fixture_rom_passes() -> None:
    rom = build_fixture_rom()
    # Should not raise.
    validate_la_rom(rom)


def test_rejects_oversize_file() -> None:
    rom = b"\x00" * (4 * 1024 * 1024 + 1)
    with pytest.raises(RomValidationError, match="too large"):
        validate_la_rom(rom)


def test_rejects_undersize_file() -> None:
    rom = b"\x00" * 0x100  # below 0x150 — no room for header
    with pytest.raises(RomValidationError, match="too small"):
        validate_la_rom(rom)


def test_rejects_wrong_title() -> None:
    rom = bytearray(build_fixture_rom())
    rom[0x0134:0x0139] = b"MARIO"  # not ZELDA
    with pytest.raises(RomValidationError, match="title"):
        validate_la_rom(bytes(rom))


def test_rejects_wrong_cartridge_type() -> None:
    rom = bytearray(build_fixture_rom())
    rom[0x0147] = 0x00  # ROM-only, not MBC1
    with pytest.raises(RomValidationError, match="cartridge"):
        validate_la_rom(bytes(rom))


def test_accepts_each_mbc1_variant() -> None:
    for cart_type in (0x01, 0x02, 0x03):
        rom = bytearray(build_fixture_rom())
        rom[0x0147] = cart_type
        validate_la_rom(bytes(rom))  # should not raise


def test_store_rom_writes_file_and_returns_sha256(tmp_path: Path) -> None:
    rom = build_fixture_rom()
    sha = store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    assert len(sha) == 64  # sha256 hex = 64 chars
    written = rom_path_for_site(tmp_path, "testsite", "la")
    assert written.read_bytes() == rom


def test_store_rom_swap_replaces_existing_atomically(tmp_path: Path) -> None:
    rom1 = build_fixture_rom(tile_at_0x10000=b"\x00" * 16)
    rom2 = build_fixture_rom(tile_at_0x10000=b"\xff" * 16)
    sha1 = store_rom(rom1, attachments_root=tmp_path, site_slug="testsite", game="la")
    sha2 = store_rom(rom2, attachments_root=tmp_path, site_slug="testsite", game="la")
    assert sha1 != sha2
    written = rom_path_for_site(tmp_path, "testsite", "la")
    assert written.read_bytes() == rom2


def test_read_rom_returns_bytes(tmp_path: Path) -> None:
    rom = build_fixture_rom()
    store_rom(rom, attachments_root=tmp_path, site_slug="testsite", game="la")
    assert read_rom(tmp_path, "testsite", "la") == rom


def test_read_rom_raises_if_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_rom(tmp_path, "nosuchsite", "la")
