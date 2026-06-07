"""Palette constants for ROM-extracted sprite rendering."""

from __future__ import annotations

from bragi_theme_zelda.rom import palettes


def test_dmg_palette_has_four_rgb_tuples() -> None:
    assert len(palettes.PALETTE_DMG) == 4
    for entry in palettes.PALETTE_DMG:
        assert isinstance(entry, tuple)
        assert len(entry) == 3
        for channel in entry:
            assert 0 <= channel <= 255


def test_pocket_palette_has_four_rgb_tuples() -> None:
    assert len(palettes.PALETTE_POCKET) == 4
    for entry in palettes.PALETTE_POCKET:
        assert len(entry) == 3
        for channel in entry:
            assert 0 <= channel <= 255


def test_palettes_dict_exposes_both_by_string_key() -> None:
    assert palettes.PALETTES["dmg"] is palettes.PALETTE_DMG
    assert palettes.PALETTES["pocket"] is palettes.PALETTE_POCKET


def test_palette_indices_are_ordered_lightest_to_darkest() -> None:
    # Index 0 is the lightest, index 3 is the darkest in canonical GB order.
    # Compare luminance using the standard ITU-R BT.601 coefficients.
    def luma(rgb: tuple[int, int, int]) -> float:
        r, g, b = rgb
        return 0.299 * r + 0.587 * g + 0.114 * b

    for palette in (palettes.PALETTE_DMG, palettes.PALETTE_POCKET):
        lumas = [luma(p) for p in palette]
        assert lumas == sorted(
            lumas, reverse=True
        ), f"palette must go lightest→darkest: {palette}"
