"""bragi_theme_zelda plugin hookimpls.

Registers the Zelda (Link's Awakening) theme via `register_theme`,
exposes `section_helper` + `page_ancestors` to Jinja templates via
`register_template_globals`, serves the pause-menu inventory homepage
via `resolve_home` when the active site's theme is "zelda", and
installs themed 404/500 error pages via `on_app_init`.
"""

from __future__ import annotations

from collections.abc import Generator
from importlib.resources import files
from pathlib import Path
from typing import Any, ClassVar

import jinja2
from bragi.api import ThemeSpec, hookimpl
from flask import Flask, g, make_response, redirect, render_template, request
from werkzeug.wrappers import Response

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


class _NullSite:
    """Used by template helpers when no site is in scope (e.g. error pages).

    Returns an empty extra_settings so the rom-sprite helpers fall
    back to placeholders silently.
    """

    slug: str = ""
    extra_settings: ClassVar[dict[str, str]] = {}


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


def _page_ancestors(page: Any) -> list[Any]:
    """Return the chain from the section root down to `page`, inclusive.

    Bragi's Page model exposes `parent_id` but not `.parent`, so we walk
    via SQL the same way `_section_helper` does. Cap the walk at 10 hops
    against malformed parent_id chains.

    Returns an empty list if page is None. The list is ordered root-first
    (suitable for direct iteration in a breadcrumb template).
    """
    if page is None:
        return []

    # Deferred imports for the same reason as _section_helper.
    from bragi.core.db import SessionLocal
    from bragi.core.models.page import Page as _Page
    from sqlalchemy import select

    chain: list[Any] = [page]
    current_parent_id: int | None = page.parent_id
    if current_parent_id is None:
        return chain

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
            chain.append(ancestor)
            if ancestor.parent_id is None:
                break
            current_parent_id = ancestor.parent_id

    # Walked from leaf to root; reverse so the section root is first.
    chain.reverse()
    return chain


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
    """Expose section_helper, page_ancestors, rom_sprite, rom_sprite_url.

    bragi's hookspec mutates the Jinja `env` in place (adding globals,
    filters, or tests). We inject `section_helper(page)` for the OoT
    chrome flip in base.html and `page_ancestors(page)` for the
    breadcrumb partial; both bypass `page.parent` (absent on bragi's
    Page model) by walking `parent_id` via SQL.

    Also exposes the ROM-extracted sprite helpers `rom_sprite(name, alt)`
    (returns a `<picture>` element or a placeholder `<img>`) and
    `rom_sprite_url(name, palette)` (returns the URL string only).

    Note: the hookspec signature is `(env: jinja2.Environment) -> None`,
    not `dict[str, Any]`. The plan's assumed signature differed; this
    implementation matches the actual bragi hookspec.
    """
    from bragi_theme_zelda.template_helpers import make_rom_sprite_helpers

    env.globals["section_helper"] = _section_helper
    env.globals["page_ancestors"] = _page_ancestors

    def _get_current_site() -> Any:
        # bragi puts the current site on flask.g during request resolution.
        return getattr(g, "site", None) or _NullSite()

    rom_sprite, rom_sprite_url = make_rom_sprite_helpers(
        get_site=_get_current_site,
    )
    env.globals["rom_sprite"] = rom_sprite
    env.globals["rom_sprite_url"] = rom_sprite_url


@hookimpl(hookwrapper=True)
def resolve_home(site: Any) -> Generator[None, None, None]:
    """Pause-menu inventory grid wins at `/` when site.theme == 'zelda'.

    Implemented as a hookwrapper rather than a regular `@hookimpl` because
    bragi's `bragi.contrib.page` plugin's `resolve_home` is also decorated
    `@hookimpl(tryfirst=True)`. Two `tryfirst=True` impls compete on
    plugin-discovery order, which is non-deterministic across entry-point
    loads — surfaced when an operator imported a Ghost site whose
    `home_page_id` mapped to a `Home` page: locally the theme won, on CI
    the page plugin won.

    Hookwrapper sidesteps the ordering question entirely. We let the inner
    chain run (the page plugin's impl resolves its home page, anything
    else returns None), then `force_result` overrides with the pause-menu
    response so the theme wins deterministically. When the theme is not
    active we yield without forcing, so the chain's natural firstresult
    (page plugin's home page, then theme_default's welcome fallback)
    plays out as before.
    """
    if getattr(site, "theme", None) != "zelda":
        yield
        return

    tiles = _home_tiles_for(site)
    body = render_template("delivery/home/pause_menu.html", site=site, tiles=tiles)
    # pluggy injects the _Result object into the generator via .send() on
    # the yield; mypy can't see through pluggy's hookwrapper protocol, so
    # type the outcome as Any to access force_result.
    outcome: Any = yield
    outcome.force_result(Response(body, mimetype="text/html"))


def _home_tiles_for(site: Any) -> list[dict[str, str]]:
    """Return the inventory-tile dict list rendered on the pause-menu home.

    Each tile carries: slug, title, url, sprite. Reads published children of
    site.home_page_id when that field is set; otherwise falls back to a
    hardcoded [LA, OoT, About] list so the page is never empty on a fresh
    site.

    The sprite value is the PNG filename stem under
    `static/sprites/items/`; the template appends `.png`.
    """
    # Deferred imports: this module loads at app boot when the bragi DB may
    # not yet be connectable. Deferring keeps register_theme cheap and
    # mirrors the pattern used in _section_helper above.
    from bragi.core.db import SessionLocal
    from bragi.core.models.page import Page as _Page
    from bragi.core.models.page import PageStatus

    fallback: list[dict[str, str]] = [
        {
            "slug": "links-awakening",
            "title": "Link's Awakening",
            "url": "/links-awakening/",
            "sprite": "la_pearl",
        },
        {
            "slug": "ocarina-of-time",
            "title": "Ocarina of Time",
            "url": "/ocarina-of-time/",
            "sprite": "kokiri_emerald",
        },
        {
            "slug": "about",
            "title": "About",
            "url": "/about/",
            "sprite": "owl_statue",
        },
    ]

    home_id = getattr(site, "home_page_id", None)
    if home_id is None:
        return fallback

    with SessionLocal() as session:
        children = (
            session.query(_Page)
            .filter_by(site_id=site.id, parent_id=home_id, status=PageStatus.PUBLISHED)
            .order_by(_Page.menu_order, _Page.title)
            .all()
        )
        if not children:
            return fallback
        return [
            {
                "slug": p.slug,
                "title": p.title,
                # bragi's url_for_page is not available here; cheap path
                # build is fine for top-level children of the home page.
                "url": f"/{p.slug}/",
                # PNG name convention: slug hyphens become underscores.
                "sprite": p.slug.replace("-", "_"),
            }
            for p in children
        ]


@hookimpl
def on_app_init(app: Flask, registry: Any) -> None:
    """Install themed 404/500 error pages on the delivery app.

    Fires after bragi's core middleware (including `register_redirect_handler`)
    has already installed its own `@app.errorhandler(404)` that emits a plain
    "Not Found" text response as the redirect-miss fallback. Flask resolves
    multiple `errorhandler` registrations for the same code by using the last
    one registered; this hookimpl fires after core middleware, so our handler
    wins.

    For zelda-themed sites our handler replicates the redirect-chain logic
    (it has to, because we replaced the handler that ran it) using
    `pm.hook.resolve_redirect` from the plugin manager already stored on
    `app.extensions`. For unresolved paths on zelda sites, we render the
    ZZZZZ 404 template. For non-zelda sites or no-site-resolved requests, we
    fall back to the plain-text "Not Found" so other sites sharing the
    same delivery process are unaffected.

    The 500 handler is unconditional: a server error on any site deserves a
    page rather than a Werkzeug plaintext traceback, and the zelda 500
    template (`GAME OVER / CONTINUE?`) is readable without zelda-specific
    branding.

    TODO: replace this entire workaround once bragi exposes a
    `register_error_handlers(app)` hookspec. The redirect-chain replication
    below is a copy of bragi's canonical handler and will drift if bragi's
    upstream changes; the workaround exists only because there is no clean
    way to install a themed errorhandler without it today.
    """
    # Maximum hops mirrors bragi's own constant in core/middleware/redirects.py.
    # Kept local to avoid importing from bragi.core (plugin boundary).
    max_hops = 3

    @app.errorhandler(404)
    def _themed_404(_exc: object) -> Response:
        from flask import current_app

        site = g.get("site")
        if site is None:
            # No site resolved: plain fallback, same as bragi's core handler.
            return make_response("Not Found", 404)

        pm = current_app.extensions.get("plugin_manager")
        if pm is not None:
            # Run the redirect chain before deciding this is a real 404.
            # Mirrors the logic in bragi's register_redirect_handler but
            # stays within the plugin boundary (no bragi.core imports).
            initial_path = request.path
            current_path = initial_path
            seen: set[str] = {initial_path}
            first_status: int | None = None
            final_target: str | None = None

            for _ in range(max_hops):
                result = pm.hook.resolve_redirect(site=site, path=current_path)
                if result is None:
                    break
                if first_status is None:
                    first_status = result.status_code
                if result.status_code == 410:
                    return make_response("Gone", 410)
                final_target = result.target
                if final_target in seen:
                    current_app.logger.warning(
                        "Redirect loop detected on %r (chain: %s)",
                        initial_path,
                        [*list(seen), final_target],
                    )
                    return make_response("Internal Server Error: redirect loop", 500)
                seen.add(final_target)
                if not final_target.startswith("/"):
                    break
                current_path = final_target

            if final_target is not None:
                assert first_status is not None
                return redirect(final_target, code=first_status)

        # No redirect matched. Render the themed 404 for zelda sites;
        # fall back to plain text for any other theme.
        if getattr(site, "theme", None) == "zelda":
            body = render_template("delivery/errors/404.html", site=site)
            return make_response(body, 404)

        return make_response("Not Found", 404)

    @app.errorhandler(500)
    def _themed_500(_exc: object) -> Response:
        site = g.get("site")
        try:
            body = render_template(
                "delivery/errors/500.html",
                site=site,
            )
        except Exception:
            # If template rendering itself fails, fall back to plain text so
            # the error page can't recursively 500.
            return make_response("Internal Server Error", 500)
        return make_response(body, 500)


@hookimpl
def register_admin_blueprint() -> Any:
    """Register the Zelda theme's admin Blueprint for ROM upload management.

    Wires bragi's site-resolution and role-gate callables into the
    blueprint factory so access control matches every other bragi admin
    surface.

    Note: `bragi.api` does not expose `current_site_by_slug` or
    `require_role` as of the current bragi version. We reach into
    `bragi.core.permissions` directly as a temporary boundary crossing.
    `resolve_site_or_abort` takes ``(db, site_slug)``; we wrap it in a
    closure that opens a SessionLocal so the blueprint sees the simple
    ``(site_slug: str) -> Site`` contract it expects. This should be
    replaced with a clean `bragi.api` surface once bragi exposes one.

    TODO: migrate to `bragi.api.current_site_by_slug` and
    `bragi.api.require_role` once bragi grows that hookspec surface.
    """
    # Temporary bragi.core imports: no clean bragi.api equivalent yet.
    from bragi.core.db import SessionLocal
    from bragi.core.permissions import require_role as _require_role
    from bragi.core.permissions import resolve_site_or_abort

    from bragi_theme_zelda.admin import build_admin_blueprint

    def _current_site(site_slug: str) -> Any:
        with SessionLocal() as db:
            return resolve_site_or_abort(db, site_slug)

    return build_admin_blueprint(
        current_site=_current_site,
        require_role=_require_role,
    )


@hookimpl
def register_delivery_blueprint() -> Any:
    """Register the ROM-extraction Blueprint on the delivery app.

    The route surface ``/zelda/rom/<game>/<palette>/<sprite>.png`` is
    delivery-only; this hook fires only on the delivery app so the
    admin app does not mirror the route.
    """
    from bragi_theme_zelda.delivery.rom_routes import build_rom_blueprint

    return build_rom_blueprint()


__all__ = [
    "on_app_init",
    "register_admin_blueprint",
    "register_delivery_blueprint",
    "register_theme",
    "register_template_globals",
    "resolve_home",
]
