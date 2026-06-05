"""GB-frame wrapper for body images.

Takes the HTML for an already-pictureified <picture> block and wraps it
in <figure class="gb-frame"> with a pixel-font caption bar. The caption
comes from the markdown directive or, if absent, from the inner img alt.

Caption is uppercased to match the in-game text-box label convention.
"""

from __future__ import annotations


def wrap_picture(picture_html: str, caption: str = "") -> str:
    label_html = ""
    if caption:
        label_html = f'<span class="gb-frame__label">{caption.upper()}</span>'
    return (
        f'<figure class="gb-frame">'
        f"{label_html}"
        f'<div class="gb-frame__inner">{picture_html}</div>'
        f"</figure>"
    )
