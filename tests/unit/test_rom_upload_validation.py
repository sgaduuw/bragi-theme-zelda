"""Tests for LA ROM upload header validation."""

from __future__ import annotations

import pytest

from bragi_theme_zelda.rom.upload import RomValidationError, validate_la_rom
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
