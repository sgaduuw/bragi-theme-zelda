"""ROM upload validation and atomic file storage.

Header validation rejects files that are obviously not LA ROMs
(wrong size, wrong title field, wrong cartridge type byte). It does
not validate the Nintendo logo bytes at 0x0104-0x0133 — that would
require embedding the canonical 48-byte logo in our test data, which
adds legal fuzziness without rigour gain. The title-prefix and
cartridge-type checks already reject every plausible wrong file.

Storage uses atomic write-then-rename so concurrent readers never see
a half-written file: writers create a sibling `.partial` file, fsync,
then ``os.replace`` it to the final path. Readers ``mmap`` the final
path; old workers keep their inode mapping until they release.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

MAX_ROM_SIZE = 4 * 1024 * 1024  # 4 MB — LA is 1 MB; cap blocks obvious mistakes
MIN_ROM_SIZE = 0x150  # bytes — minimum to contain a full GB header

TITLE_OFFSET = 0x0134
TITLE_PREFIX = b"ZELDA"
CART_TYPE_OFFSET = 0x0147
ACCEPTED_CART_TYPES = frozenset({0x01, 0x02, 0x03})  # MBC1, MBC1+RAM, MBC1+RAM+BATTERY


class RomValidationError(ValueError):
    """Raised when an uploaded file fails LA ROM validation."""


def validate_la_rom(data: bytes) -> None:
    """Validate that ``data`` is a plausibly-real LA ROM.

    Raises :class:`RomValidationError` with a human-readable message
    on the first failed check. Returns ``None`` on success.

    Checks (in order): file size, header readable, title prefix,
    cartridge type byte. All fail-closed.
    """
    if len(data) > MAX_ROM_SIZE:
        raise RomValidationError(
            f"file is too large ({len(data)} bytes, max {MAX_ROM_SIZE})"
        )
    if len(data) < MIN_ROM_SIZE:
        raise RomValidationError(
            f"file is too small ({len(data)} bytes,"
            f" need at least {MIN_ROM_SIZE} for a GB header)"
        )

    title = data[TITLE_OFFSET : TITLE_OFFSET + len(TITLE_PREFIX)]
    if title != TITLE_PREFIX:
        raise RomValidationError(
            f"header title does not start with {TITLE_PREFIX!r}; got {title!r}"
        )

    cart_type = data[CART_TYPE_OFFSET]
    if cart_type not in ACCEPTED_CART_TYPES:
        raise RomValidationError(
            f"cartridge type byte 0x{cart_type:02X} is not an MBC1 variant "
            f"(expected one of {sorted(hex(c) for c in ACCEPTED_CART_TYPES)})"
        )


def rom_path_for_site(attachments_root: Path, site_slug: str, game: str) -> Path:
    """Filesystem path where ``site_slug``'s ROM for ``game`` lives.

    Layout: ``<attachments_root>/zelda-roms/<site_slug>/<game>.gb``.
    Per-site directory matches bragi's multisite scoping; the filename
    is normalized (we know the game), so the original upload filename
    is not preserved.
    """
    return attachments_root / "zelda-roms" / site_slug / f"{game}.gb"


def store_rom(
    data: bytes,
    *,
    attachments_root: Path,
    site_slug: str,
    game: str,
) -> str:
    """Atomically write ``data`` to the per-site ROM path and return its sha256.

    Writes to a sibling ``.partial`` path first, fsyncs, then
    ``os.replace`` to the final path. Concurrent readers either see
    the old file or the new file, never a half-written one.

    Caller is responsible for having called :func:`validate_la_rom`
    first.
    """
    final = rom_path_for_site(attachments_root, site_slug, game)
    final.parent.mkdir(parents=True, exist_ok=True)
    partial = final.with_suffix(final.suffix + ".partial")

    # Write + fsync the partial file first, then atomic rename.
    with partial.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(partial, final)

    return hashlib.sha256(data).hexdigest()


def read_rom(attachments_root: Path, site_slug: str, game: str) -> bytes:
    """Read the stored ROM for ``site_slug`` and ``game``.

    Raises :class:`FileNotFoundError` if the file is missing on disk.
    """
    return rom_path_for_site(attachments_root, site_slug, game).read_bytes()
