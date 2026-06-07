"""Runtime extraction of GB sprites from an operator-uploaded LA ROM.

Public API: :func:`get_sprite_png`. The :mod:`decoder` and :mod:`palettes`
submodules are pure functions on bytes; :mod:`upload` handles header
validation and atomic file storage; :mod:`cache` wraps the extraction
pipeline in an in-process LRU.

The manifest of named sprites lives in :mod:`manifest_la` and ships with
the theme version — adding a new sprite is a theme PR, never a ROM
re-upload.
"""

from __future__ import annotations
