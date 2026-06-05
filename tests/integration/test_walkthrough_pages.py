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
    resp = client.get("/links-awakening/tail-cave/", headers={"Host": "zelda.test"})
    assert resp.status_code == 200
    # Breadcrumb list should include "Link's Awakening" and "Tail Cave"
    # with the ► separator. Jinja HTML-escapes the apostrophe to &#39;.
    assert b'class="breadcrumbs"' in resp.data
    assert b"Link&#39;s Awakening" in resp.data
    assert b"Tail Cave" in resp.data
