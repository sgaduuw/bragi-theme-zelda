"""Section detection: walks a page's ancestors to find the section root.

The MAP sidebar, OoT chrome flip, and breadcrumbs all need to know which
top-level "section" the current page belongs to (Link's Awakening or
Ocarina of Time). This module owns that walk so the templates can stay
thin and the logic stays unit-testable.

Why not in a Jinja macro: the walk + the slug-to-section lookup table is
easier to test in Python than in Jinja, and base.html stays declarative.

The page duck-type contract: page objects only need `.slug` (str) and
`.parent` (None or another page-shaped object).

Bragi's Page model has `parent_id` (FK int) but no `.parent` relationship
attribute. The `plugin.py` wrapper `_section_helper` resolves the chain
via DB queries on `parent_id` for that case. This module's
`detect_section` stays a pure-Python helper for unit-testable cases
where the caller has a `.parent`-having object (e.g. NavNode, FakePage).

This separation is deliberate: the SQL-walk lives in plugin.py where it
can be deferred until app boot completes, while detect_section here stays
unit-testable without touching a DB. Don't inline this into the wrapper,
losing the pure-function form would lose test coverage of the algorithm
independent of the SQL plumbing.
"""

from __future__ import annotations

from typing import Any

# (slug, human label) — kept in sync with the section root pages in the bragi
# database. New top-level Zelda sections (e.g. "Twilight Princess") get one
# new entry here plus new --gb-* / --accent-* tokens in theme.css.
DEFAULT_SECTION_LABELS: dict[str, str] = {
    "la": "Link's Awakening",
    "oot": "Ocarina of Time",
}


def detect_section(
    page: Any | None,
    section_map: dict[str, str],
    labels: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (section_slug, section_label) for `page`.

    Walks the page's `.parent` chain until a parent is `None` (top-level
    page). If the top-level page's slug is in `section_map`, returns the
    mapped slug + its human label; otherwise returns ("", "").

    Page objects only need `.slug` (str) and `.parent` (None or another
    page-shaped object). Bragi's real Page rows lack `.parent`; production
    use goes through `plugin._section_helper` which walks `parent_id` via
    SQL. This function stays the unit-testable reference; tests use a
    dataclass duck-type.
    """
    if page is None:
        return ("", "")

    labels = labels if labels is not None else DEFAULT_SECTION_LABELS

    current = page
    while current.parent is not None:
        current = current.parent

    section = section_map.get(current.slug, "")
    label = labels.get(section, "")
    return (section, label)
