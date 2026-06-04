"""bragi_theme_zelda plugin hookimpls.

Registers the Zelda (Link's Awakening) theme via `register_theme`.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import jinja2
from bragi.api import ThemeSpec, hookimpl

# Resolve the package's static/ directory at import time so the path is
# stable even when the package is installed as a zip-imported wheel.
_STATIC_DIR: Path = Path(str(files("bragi_theme_zelda"))) / "static"


@hookimpl
def register_theme() -> ThemeSpec:
    """Return the Zelda ThemeSpec.

    Sites set `Site.theme = "zelda"` to pick this theme. `template_loader` is
    a PackageLoader rooted at this package's `templates/` directory; the
    delivery app's Jinja chain walks this loader before falling back to
    bragi's default templates, so any template at the same path as a bragi
    template shadows the default.
    """
    return ThemeSpec(
        slug="zelda",
        display_name="Zelda (Link's Awakening)",
        template_loader=jinja2.PackageLoader("bragi_theme_zelda", "templates"),
        static_dir=_STATIC_DIR,
    )


__all__ = ["register_theme"]
