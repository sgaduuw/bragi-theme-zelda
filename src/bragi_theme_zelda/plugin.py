"""bragi_theme_zelda plugin hookimpls.

Registers the Zelda (Link's Awakening) theme via `register_theme`, and
exposes `section_helper` to Jinja templates via `register_template_globals`.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import jinja2
from bragi.api import ThemeSpec, hookimpl

from bragi_theme_zelda.section import DEFAULT_SECTION_LABELS, detect_section

# Resolve the package's static/ directory at import time so the path is
# stable even when the package is installed as a zip-imported wheel.
_STATIC_DIR: Path = Path(str(files("bragi_theme_zelda"))) / "static"

# Section slug map: which top-level page-slug maps to which section short
# code. Kept here (not in section.py) because it's site-specific
# configuration, whereas section.py is generic logic.
_SECTION_SLUG_MAP: dict[str, str] = {
    "links-awakening": "la",
    "ocarina-of-time": "oot",
}


def _section_helper(page: Any) -> tuple[str, str]:
    """Wrapper exposed to Jinja as `section_helper(page)` -> (slug, label)."""
    return detect_section(page, _SECTION_SLUG_MAP, DEFAULT_SECTION_LABELS)


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


@hookimpl
def register_template_globals(env: jinja2.Environment) -> None:
    """Expose the section_helper to delivery templates.

    bragi's hookspec mutates the Jinja `env` in place (adding globals,
    filters, or tests). We inject `section_helper` so base.html can call
    `section_helper(page)` without importing Python from a template.

    Note: the hookspec signature is `(env: jinja2.Environment) -> None`,
    not `dict[str, Any]`. The plan's assumed signature differed; this
    implementation matches the actual bragi hookspec.
    """
    env.globals["section_helper"] = _section_helper


__all__ = ["register_theme", "register_template_globals"]
