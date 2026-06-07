"""Theme registration contract test.

Asserts the package exposes a ThemeSpec via the `bragi.plugins` entry point,
the loader resolves templates, and the static dir resolves to a real path.
"""

from __future__ import annotations

# bragi.api is the public import surface for hookimpl and spec dataclasses;
# the @hookspec-decorated functions that pluggy needs for add_hookspecs()
# live in bragi.hookspecs (the internal contract module).
import bragi.hookspecs as bragi_hookspecs
import pluggy
import pytest


@pytest.fixture
def pm() -> pluggy.PluginManager:
    """A plugin manager with only this theme registered."""
    from bragi_theme_zelda import plugin as theme_plugin

    pm = pluggy.PluginManager("bragi")
    pm.add_hookspecs(bragi_hookspecs)
    pm.register(theme_plugin)
    return pm


def test_register_theme_returns_zelda_spec(pm: pluggy.PluginManager) -> None:
    specs = pm.hook.register_theme()
    assert len(specs) == 1
    spec = specs[0]
    assert spec.slug == "zelda"
    assert spec.display_name == "Zelda (Link's Awakening)"


def test_theme_template_loader_finds_base_html(pm: pluggy.PluginManager) -> None:
    spec = pm.hook.register_theme()[0]
    source, filename, _ = spec.template_loader.get_source(None, "delivery/base.html")
    assert "<html" in source
    assert filename.endswith("base.html")


def test_theme_static_dir_exists(pm: pluggy.PluginManager) -> None:
    spec = pm.hook.register_theme()[0]
    assert spec.static_dir.exists(), f"expected {spec.static_dir!r} to exist"
    assert spec.static_dir.is_dir(), f"expected {spec.static_dir!r} to be a directory"


def test_section_helper_registered_as_template_global(
    pm: pluggy.PluginManager,
) -> None:
    # bragi's register_template_globals hookspec mutates env in place
    # (signature: (env: jinja2.Environment) -> None), so we pass a real
    # Jinja Environment and assert the global was injected.
    import jinja2

    env = jinja2.Environment()
    pm.hook.register_template_globals(env=env)
    assert "section_helper" in env.globals
    helper = env.globals["section_helper"]
    # Sanity: calling on None returns ('', '').
    assert helper(None) == ("", "")


def test_textbox_macro_renders(pm: pluggy.PluginManager) -> None:
    import jinja2

    spec = pm.hook.register_theme()[0]
    env = jinja2.Environment(loader=spec.template_loader, autoescape=True)
    # The textbox macro references the rom_sprite_url Jinja global for the
    # portrait background. Wire up the theme's template globals so the
    # helper is callable from the macro body.
    pm.hook.register_template_globals(env=env)
    tpl = env.from_string(
        "{% import 'delivery/_callout_textbox.html' as cb %}"
        "{% call cb.textbox('owl') %}<p>Hoot.</p>{% endcall %}"
    )
    out = tpl.render()
    assert 'class="textbox textbox--owl"' in out
    assert "OWL:" in out
    # The {% call %} block body is auto-escaped; assert on visible text only
    # so the test is agnostic to whether the caller wraps in autoescape or not.
    assert "Hoot." in out
