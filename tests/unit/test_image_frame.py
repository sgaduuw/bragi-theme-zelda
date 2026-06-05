"""GB-frame wrapper logic: take a <picture> string, return a <figure>."""

from __future__ import annotations

from bragi_theme_zelda.image_frame import wrap_picture


def test_wraps_picture_in_figure_with_caption_from_alt() -> None:
    html = '<picture><img src="x.png" alt="Mabe Village"></picture>'
    out = wrap_picture(html, caption="Mabe Village")
    assert '<figure class="gb-frame">' in out
    assert '<span class="gb-frame__label">MABE VILLAGE</span>' in out
    assert html in out


def test_wraps_with_caption_override() -> None:
    html = '<picture><img src="x.png" alt="ignored alt"></picture>'
    out = wrap_picture(html, caption="KOKIRI FOREST")
    assert '<span class="gb-frame__label">KOKIRI FOREST</span>' in out


def test_skips_wrap_when_caption_empty() -> None:
    html = '<picture><img src="x.png" alt=""></picture>'
    out = wrap_picture(html, caption="")
    # No caption -> still wrapped in figure but with no label.
    assert '<figure class="gb-frame">' in out
    assert "gb-frame__label" not in out
