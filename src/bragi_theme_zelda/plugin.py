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

from bragi_theme_zelda.section import DEFAULT_SECTION_LABELS

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
    """Wrapper exposed to Jinja as `section_helper(page)` -> (slug, label).

    Bragi's Page model exposes `parent_id` (FK int) but no `.parent`
    relationship attribute, so we walk the chain by issuing per-step
    queries against the integer FK instead of relying on
    `detect_section`'s `.parent`-attribute walk.

    Yields the section slug + label for whichever top-level page sits at
    the root of the current page's ancestor chain, looked up against
    `_SECTION_SLUG_MAP`. Returns ("", "") when the page is None or its
    root slug isn't a known section.
    """
    if page is None:
        return ("", "")

    # Deferred imports: this module loads at app boot when the bragi DB
    # may not yet be connectable; deferring keeps register_theme cheap.
    from bragi.core.db import SessionLocal
    from bragi.core.models.page import Page as _Page
    from sqlalchemy import select

    root_slug: str = page.slug
    current_parent_id: int | None = page.parent_id
    if current_parent_id is None:
        # Top-level page — its own slug is the root.
        return _resolve_root(root_slug)

    # DB unavailability is fatal here: propagate so Flask returns 500
    # rather than silently mislabelling the section.
    with SessionLocal() as db:
        # 10 is well above any realistic walkthrough depth (~5-7 levels:
        # section -> game -> dungeon -> area -> room -> collectible) and
        # guards against infinite loops on malformed parent_id chains.
        for _ in range(10):
            ancestor = db.execute(
                select(_Page).where(_Page.id == current_parent_id)
            ).scalar_one_or_none()
            if ancestor is None:
                break
            root_slug = ancestor.slug
            if ancestor.parent_id is None:
                break
            current_parent_id = ancestor.parent_id

    return _resolve_root(root_slug)


# Two call sites in _section_helper: the top-level-page early return and
# the post-walk exit. Factoring keeps both branches identical.
def _resolve_root(root_slug: str) -> tuple[str, str]:
    """Map a section-root slug to (section_code, human_label)."""
    section = _SECTION_SLUG_MAP.get(root_slug, "")
    label = DEFAULT_SECTION_LABELS.get(section, "")
    return (section, label)


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
