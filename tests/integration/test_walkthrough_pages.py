"""Integration tests against a live bragi delivery app with this theme set."""

from __future__ import annotations

import pytest


@pytest.fixture
def client(bragi_app_with_theme, db_session):
    """Seed a minimal site + LA section + one dungeon child page."""
    from bragi.core.models.page import Page, PageStatus
    from bragi.core.models.site import Site
    from bragi.core.models.user import User

    # Site.owner_user_id is NOT NULL; create a minimal owner first.
    owner = User(email="test@zelda.test", display_name="Tester", is_active=True)
    db_session.add(owner)
    db_session.flush()

    site = Site(
        hostname="zelda.test",
        slug="zelda-test",
        title="Zelda Test",
        locale="en",
        theme="zelda",
        owner_user_id=owner.id,
    )
    db_session.add(site)
    db_session.flush()

    la = Page(
        site_id=site.id,
        slug="links-awakening",
        title="Link's Awakening",
        status=PageStatus.PUBLISHED,
        show_in_nav=True,
        menu_order=0,
        author_id=owner.id,
    )
    db_session.add(la)
    db_session.flush()

    # show_in_nav=True so tail-cave appears in la's nav children list
    # (bragi.contrib.nav.tree.build_nav_tree only includes show_in_nav=True
    # pages, even as children).
    tail_cave = Page(
        site_id=site.id,
        slug="tail-cave",
        title="Tail Cave",
        parent_id=la.id,
        status=PageStatus.PUBLISHED,
        show_in_nav=True,
        menu_order=0,
        author_id=owner.id,
    )
    db_session.add(tail_cave)
    db_session.commit()

    return bragi_app_with_theme.test_client()


def test_top_level_la_page_has_data_section_la(client) -> None:
    resp = client.get("/links-awakening/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'data-section="la"' in resp.data


def test_map_sidebar_renders_section_tree(client) -> None:
    # Hitting the child page; the parent node (links-awakening) is marked
    # current because request.path starts with its URL, expanding children.
    resp = client.get("/links-awakening/tail-cave/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'class="map-label"' in resp.data
    assert b"MAP" in resp.data
    # The ► cursor (U+25BA, UTF-8: 0xe2 0x96 0xba) renders on the current item.
    assert b"\xe2\x96\xba" in resp.data


def test_breadcrumbs_render_with_pixel_arrow_separator(client) -> None:
    """Multi-level page: breadcrumb shows section -> current, no site title."""
    resp = client.get("/links-awakening/tail-cave/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'class="breadcrumbs"' in resp.data
    # Crumbs include the section root and the current page (Jinja HTML-escapes
    # the apostrophe to &#39;).
    assert b"Link&#39;s Awakening" in resp.data
    assert b"Tail Cave" in resp.data
    # Site title is NOT in the breadcrumb (the top bar's brand link already
    # serves that role; including it here repeats the wordmark visually for
    # no navigational gain).
    assert b'class="breadcrumbs"' in resp.data
    breadcrumbs_html = resp.data.split(b'class="breadcrumbs"', 1)[1].split(
        b"</nav>", 1
    )[0]
    assert b"Zelda Test" not in breadcrumbs_html


def test_breadcrumbs_hidden_on_section_root_page(client) -> None:
    """Top-level page (own breadcrumb chain has length 1): suppress the
    breadcrumb entirely. The page H1 already conveys 'you are here'; a
    single-item breadcrumb is just visual noise above it."""
    resp = client.get("/links-awakening/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'class="breadcrumbs"' not in resp.data


def test_pause_menu_home_renders(client) -> None:
    resp = client.get("/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'class="pause-menu"' in resp.data
    assert b"- PAUSE -" in resp.data
    # Fallback list contains links-awakening (LA pearl tile).
    assert b"links-awakening" in resp.data


def test_pause_menu_home_wins_when_site_has_home_page_id(client, db_session) -> None:
    """`resolve_home` is `tryfirst=True` so the pause-menu beats bragi's page
    plugin even when an operator has set `site.home_page_id` (the common
    state after a Ghost import — Ghost ships a `Home` page that the importer
    maps to the bragi home_page_id). Regression test for the issue surfaced
    during the first zelda.eelcowesemann.nl cutover."""
    from bragi.core.models.page import Page, PageStatus
    from bragi.core.models.site import Site

    # Seed an extra page and point the site's home_page_id at it.
    site = db_session.query(Site).filter_by(hostname="zelda.test").one()
    owner_id = site.owner_user_id
    home_page = Page(
        site_id=site.id,
        slug="home",
        title="Home",
        body_markdown="This Ghost-imported Home page must NOT render at /.",
        status=PageStatus.PUBLISHED,
        show_in_nav=False,
        menu_order=0,
        author_id=owner_id,
    )
    db_session.add(home_page)
    db_session.flush()
    site.home_page_id = home_page.id
    db_session.commit()

    resp = client.get("/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b'class="pause-menu"' in resp.data
    assert b"- PAUSE -" in resp.data
    assert b"This Ghost-imported Home page must NOT render at /." not in resp.data


def test_hr_renders_in_page_body(client) -> None:
    """The theme styles <hr> via CSS; markdown's <hr/> survives to the rendered page."""
    # Seed: set a body with a horizontal rule on the existing tail_cave page.
    from bragi.core.db import SessionLocal
    from bragi.core.models.page import Page
    from bragi.core.render.markdown import render_markdown

    with SessionLocal() as session:
        page = session.query(Page).filter_by(slug="tail-cave").first()
        assert page is not None
        page.body_markdown = "Intro paragraph.\n\n---\n\nNext section."
        # Force re-render of body_html (bragi typically does this on save).
        page.body_html = render_markdown(page.body_markdown)
        session.commit()

    resp = client.get("/links-awakening/tail-cave/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    assert b"<hr" in resp.data


def test_404_page_renders_zzz_scene(client) -> None:
    resp = client.get("/no-such-page/", headers={"Host": "zelda.test"})
    assert resp.status_code == 404
    assert b'class="error-page error-404"' in resp.data
    assert b"It's a bad omen." in resp.data or b"It&#39;s a bad omen." in resp.data
    assert b"WAKE UP" in resp.data
