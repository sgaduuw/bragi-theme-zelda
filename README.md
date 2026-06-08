# bragi-theme-zelda

A Link's-Awakening-flavoured theme for the [bragi CMS](https://github.com/sgaduuw/bragi),
deployed at [zelda.eelcowesemann.nl](https://zelda.eelcowesemann.nl).

This is a site-specific theme. The visual choices are opinionated for one Zelda fan site
(primarily Link's Awakening walkthroughs with secondary Ocarina of Time coverage) and are
not intended as a general-purpose Zelda theme.

## Theme highlights

- **Game Boy LCD palette:** 4-shade GB green light mode, 4-shade GB Pocket greyscale dark
  mode. Two real handheld LCDs under one roof; `prefers-color-scheme` determines which.
- **Pixel headings over readable body:** Press Start 2P for short strings (headings, labels,
  UI chrome), Inter for body text, JetBrains Mono for code.
- **MAP-styled sidebar tree:** Current section's siblings and children visible at a glance,
  styled as a pause-menu MAP panel. Walkthrough hierarchy (game, dungeon, room) navigable
  without hunting through a top-level nav.
- **OoT section chrome flip:** Royal-blue + gold accent shift in the Ocarina of Time section
  via `data-section="oot"`. Body stays GB-green for cohesion; chrome (top bar, image frames,
  links) signals the switch.
- **GB Pocket greyscale dark mode:** A real GB Pocket palette (light grey on near-black),
  not a colour inversion. Different hardware era, coherent aesthetic family.
- **Seven cosplay motifs:** text-box callouts (Owl / Marin / Tarin / Ulrira portraits),
  rupee counter, PUSH START splash, item-acquired flourish between sections, pause-menu
  inventory homepage, ZZZZZ 404, heart-container `<hr>`, inventory-row pinned posts.
- **`prefers-reduced-motion` respected:** Any animation that moves (ZZZZZ float, item-
  acquired scroll, PUSH START blink) switches to a static render.

## Status: v0.4.9

v0.4.9 is a small follow-up to v0.4.8 with two additions: the
LA-section pause-menu tile now extracts a `link_sleeping` sprite
(`$38D00`, Npc1Tiles row 13 position 0 — the iconic LA cold-open
frame) from the operator's ROM instead of falling back to a static
`la_pearl` placeholder; and the cache-buster on every ROM-extracted
PNG URL now mixes the installed theme version (`?v=<sha[:12]>-<theme_version>`)
so manifest changes between theme upgrades auto-invalidate cached
browser/CDN copies. The latter scratches an itch that bit operator
verification across the v0.4.6 → v0.4.7 → v0.4.8 cycle — incognito
windows are no longer required to see fresh PNGs after a theme bump.
Eighth sprite in the manifest; no new `SpriteRef` flags.

v0.4.8 closes the v0.4.6 sprite-rendering arc: all seven sprites in
`manifest_la.py` now render recognisably against a real LA-1993 ROM dump.
v0.4.6's shipped addresses were correct for some sprites and
wrong-but-plausibly-close for others; v0.4.7 fixed the decoder's tile
ordering for 8x16 OAM sprites but didn't move the addresses; v0.4.8
does direct visual verification against the operator's ROM via a new
local iteration tool (`_claude/scripts/sprite_explore.py`) and locks
in addresses + geometries + render flags for each. `SpriteRef` gains
three flags (`mirror_right`, `palette_invert`, `vstack_groups`)
capturing the patterns we found in the ROM data: Nintendo's
mirror-storage trick for symmetric sprites, LA's OBP1 palette path
for character portraits and stone statues, and tall NPCs that occupy
two stacked OAM groups. Tarin's offset moved from Npc2Tiles row 42
(where the agent's slot-table research had pointed -- and where the
sleep-Z icon actually lives) to Npc1Tiles row 14, the canonical
forward-facing portrait. Ulrira, owl, and owl-statue all re-addressed
to match what the game actually draws.

v0.4.7 is a hotfix bundle that makes the v0.4.6 sprite extractions actually
look like the in-game sprites. Two bugs surfaced on first deploy:
multi-column NPC sprites rendered with their top-right and bottom-left
tiles swapped, because LA stores 16x16 character portraits in 8x16
OAM-mode column-major order (`[TL, BL, TR, BR]`) but our decoder read
them row-major; and the item icons (heart container, rupee, owl statue)
shipped with wrong tile-dimensions that captured only a corner or a
column of the actual sprite. `SpriteRef` grows an `oam_8x16` flag that
swaps to column-major iteration when set; the four character portraits
plus `heart_container` and `owl_statue` set the flag. `heart_container`
geometry corrected from 1x1 to 2x2, `rupee_green` from 1x1 to 1x2,
`owl_statue` from 1x4 to 2x4. The decoder default stays row-major so
existing tests and any future single-tile or single-column extractions
are unaffected.

v0.4.6 finishes the v0.2.0 deferral: ROM offsets in `manifest_la.py` now
point at the actual tile data for the seven supported sprites, sourced
from [zladx/LADX-Disassembly](https://github.com/zladx/LADX-Disassembly)
with cross-verification against
[jverkoey/windfish](https://github.com/jverkoey/windfish)'s original-LA
disassembly (commit `7437552`). Until v0.4.6 the offsets shipped as
plausible-looking placeholders that decoded to noise from any LA ROM:
the seven sprites were structurally extractable end-to-end but visually
unrecognisable. `owl_statue`'s geometry also flipped from 2x2 to 1x4 to
match the in-game art (8x16 OAM column rendering). Task 5b — the
longstanding gap since v0.2.0 — is complete.

v0.4.5 finishes off what v0.4.1 missed: the delivery `/zelda/rom/...` route
also reads from `bragi.settings.settings.attachments_root` now (it was still
on the dead `current_app.config["BRAGI_ATTACHMENTS_ROOT"]` path). After
v0.4.4 fixed the URL host, the requests landed at the right host but the
handler 404'd because it couldn't find the ROM file. Closes #59.

v0.4.4 fixes the admin ROM upload page's sprite preview grid: the previews
were emitting relative URLs that resolved against the admin host, but the
`/zelda/rom/<game>/<palette>/<sprite>.png` extraction route only exists on
the delivery app. Previews now use cross-host
(`//{{ site.hostname }}/zelda/rom/...`) URLs so the browser fetches them
from the right host. Closes #56.

v0.4.3 finally wires the ROM extraction pipeline through to rendered sprites.
Until now the pause-menu home tiles and callout-textbox portraits hardcoded
the static placeholder paths regardless of whether a ROM was uploaded; the
`rom_sprite_url` Jinja global was dead code. v0.4.3 has the templates call
the helper, fixes its default static-prefix to match bragi's theme-static
mount, and makes it fall back gracefully for decorative-only sprite names
that aren't in `SPRITES_LA`. Closes the loop on the v0.2.0+ ROM upload
feature actually doing something visible.

v0.4.2 is a second hotfix on the v0.4.0 ROM upload path: the handlers were
calling a `site.save()` method that bragi's SQLAlchemy `Site` model doesn't
have (`AttributeError` on every POST). Persistence now goes through a small
helper that opens a fresh `bragi.core.db.SessionLocal`, re-attaches the
(detached) site row via `session.get(Site, site.id)`, mutates the
`MutableDict`-wrapped `extra_settings`, and commits. Closes #51.

v0.4.1 is a hotfix for a v0.4.0 deploy-time bug: the ROM upload and delete
handlers in `admin/routes.py` were reading the attachments root from
`current_app.config["BRAGI_ATTACHMENTS_ROOT"]` (a Flask config key bragi
never populates), so every upload and delete attempt 500'd with a `KeyError`
on first deploy. v0.4.1 switches to `bragi.settings.settings.attachments_root`,
matching the pattern used by bragi's in-tree contrib plugins. Closes #48.

v0.4.0 consumes bragi 1.29.0's new `claims_root_route` hookspec. The theme now
declares ownership of `/` for zelda-themed sites declaratively so bragi's
welcome-fallback detector doesn't fire a false-positive notice on sites where
the pause-menu inventory page owns `/`. Closes out the full #389 cycle:
bragi v1.28.0 introduced the false positive, v1.28.1 shipped a heuristic
band-aid that the theme could rely on transiently, v1.29.0 introduced the
principled API; theme v0.4.0 picks up the consumer. Eighth theme hookimpl.
Bumps bragi base to v1.29.0.

v0.3.1 is a hotfix bundle for two v0.3.0 deploy-time bugs: the ROM upload
admin page now extends bragi's `admin/base.html` so it renders inside the
admin chrome instead of as a standalone page (#38), and the upload / replace
/ delete forms now include the `_csrf_token` hidden field required by
bragi's CSRF middleware (without it, the operator could not upload a ROM at
all — #39). No template or schema changes beyond the rom-management page.

v0.3.0 closes the loop on the v0.2.0 delivery-side ROM-upload banner that
couldn't render because bragi keeps admin and delivery session state on
separately-scoped hostnames. The replacement is admin-side via bragi 1.28.0's
new `admin_notices` hookspec: a `zelda.rom_required` action_required notice
surfaces on the per-site dashboard, the sticky rail on every per-site admin
page, and the global admin index dots whenever a zelda-themed site has no
ROM uploaded. Disappears immediately on upload (the upload + delete handlers
call `bragi.api.invalidate_admin_notices(site)`). Adds one new hookimpl
(`admin_notices`); the dead delivery banner partial + CSS are removed. Bumps
the bragi base to v1.28.0.

v0.2.1 is a PATCH bundle of post-v0.2.0 hardening: ROM extraction cache key now
includes `mtime_ns` so atomic swaps self-invalidate across worker processes (#25),
admin upload enforces a 4 MiB + 64 KiB envelope cap via `request.content_length`
before any multipart parsing to prevent admin-worker OOM (#26), and new contrib
tests exercise the real bragi admin + delivery apps to catch hookspec signature
drift the prior stub-based tests would miss (#27). No template or schema changes.

v0.2.0 introduces runtime ROM-driven sprite extraction. Site operators upload
their Link's Awakening (1993, Game Boy) ROM via the admin
(`/admin/sites/<slug>/zelda/rom/upload`); the theme decodes 2bpp GB tile data on
every page render to serve pixel-perfect LA-authentic character and item sprites.
The theme package itself ships zero Nintendo IP. New hookimpls:
`register_admin_blueprint` and `register_delivery_blueprint`. New Jinja globals:
`rom_sprite` and `rom_sprite_url`. Falls back to v0.1.6 placeholder PNGs when no
ROM is uploaded.

v0.1.6 is a PATCH bundle of pause-menu visual polish: drop the inner `.pause-menu__sprite`
border (it duplicated the tile-frame border and read as a nested double-wall), bump
`.pause-menu__label` font-size to 10px exact for crisp Press Start 2P rendering, and
swap the `- PAUSE -` title decoration to JRPG-style chevrons (`<< PAUSE >>`). Placeholder
sprites (`LA PEA` / `KOKIRI` / `OWL ST`) are unchanged; sprite finalisation remains the
bigger deferred surface.

v0.1.5 is a PATCH bundle: bragi base bumped from v1.27.3 to v1.27.6 (carries bragi's
`__GHOST_URL__` placeholder substitution fix for Ghost-imported content, and the PyPI
propagation gating fix in the release pipeline), and a `bragi-released`
`repository_dispatch` receiver workflow that opens the bragi base-bump PR within seconds
of a bragi release. Dependabot stays in place as the 24h backstop.

v0.1.4 is a PATCH bundle: pause-menu hookwrapper (deterministic win at `/`), darkened
`--accent-link` for WCAG AA body-link contrast, breadcrumb simplification (drop site-title
prefix, suppress single-item trails), and Dependabot watching Dockerfile FROM lines. No
bragi base bump.

v0.1.3 adds pre-built container images `ghcr.io/sgaduuw/bragi-admin-zelda` and
`ghcr.io/sgaduuw/bragi-delivery-zelda`. Each image is the corresponding bragi base (pinned
to v1.27.3) with the theme wheel preinstalled. Operators can now pull a single image instead
of writing a downstream Dockerfile to layer the theme on top of the bragi base.

v0.1.2 switched the dev dep from `bragi @ git+https://...@v1.26.0` to `bragi-cms ^1.27`
from PyPI. No runtime behaviour change for sites running with `theme='zelda'`.

v0.1.1 is the first PyPI-published release. **Character portraits, item tiles, the
heart-container, and the 404 scene art are still placeholder PNGs** (Pillow-generated
text-on-coloured-square). The CSS / JS / templates reference the correct sprite filenames,
so a future release swaps in real art via per-file PNG replacement with no code changes.

## Asset provenance

Fonts and sprites are documented row-by-row in [ASSETS.md](ASSETS.md). For ROM-extracted
sprites (v0.2.0+), each operator supplies their own ROM; the theme itself ships zero Nintendo IP.
See ASSETS.md for the full sourcing and licence detail.

## ROM-extracted sprites (v0.2.0+)

Character portraits and iconic item sprites can be extracted live from an operator-uploaded
Link's Awakening (1993, Game Boy) ROM. The theme package itself ships zero Nintendo IP; each
operator brings their own legally-dumped cartridge data.

After installing the theme, visit:

```
/admin/sites/<your-site-slug>/zelda/rom/upload
```

...and upload your `.gb` dump. Sprites then extract live on every page render. Until a ROM is
uploaded, the theme falls back to the v0.1.6 placeholder PNGs; logged-in site editors see a
nudge banner pointing at the upload page.

The delivery URL `/zelda/rom/la/<palette>/<sprite>.png?v=<sha[:12]>-<theme_version>` exposes
the provenance directly: the `rom` segment makes clear the PNG is live-extracted, the palette
segment selects DMG (4-greens) or GB Pocket greyscale, and the `?v=` cache-buster automatically
invalidates browser/CDN caches whenever the ROM is swapped OR the theme is upgraded (theme
upgrades can change the manifest's addresses, geometries, and render flags, so URLs need to
auto-invalidate even when the operator's ROM stays the same).

### Template helpers

Two Jinja globals are exposed for use in custom templates:

~~~jinja
{{ rom_sprite('marin', alt='Marin says') }}
{# Becomes a <picture> with dmg + pocket variants when ROM uploaded,
   or <img> to /static/sprites/portraits/marin.png otherwise. #}

{{ rom_sprite_url('marin', palette='dmg') }}
{# Returns just the URL string; use for inline CSS or JS. #}
~~~

Sprite names available since v0.2.0: `marin`, `tarin`, `owl`, `ulrira`,
`heart_container`, `rupee_green`, `owl_statue`. v0.4.9 adds
`link_sleeping`.

## Installing

### Recommended: pre-built variant images (v0.1.3+)

From v0.1.3, pre-built images are published on every GitHub Release. Pull the variant
directly instead of writing a downstream Dockerfile:

```dockerfile
# Delivery container — bragi-delivery + bragi-theme-zelda preinstalled.
FROM ghcr.io/sgaduuw/bragi-delivery-zelda:v0.4.9
# That's it. No further pip install step needed.
```

```dockerfile
# Admin container — bragi-admin + bragi-theme-zelda preinstalled.
FROM ghcr.io/sgaduuw/bragi-admin-zelda:v0.4.9
# That's it. No further pip install step needed.
```

Both containers need the package so template lookups work from the admin preview path and
from the public delivery path. Restart both after installation to pick up the plugin.

### Fallback: downstream Dockerfile from PyPI

Use this form when you need a different bragi base version than the one pinned in the
variant image (see CONTEXT.md "Container deploy" for the `BRAGI_VERSION` bump policy), or
for development against an unreleased commit.

#### Delivery container

```dockerfile
FROM ghcr.io/sgaduuw/bragi-delivery:v1.29.0

# Install from PyPI (pin to a specific version).
RUN pip install --no-cache-dir bragi-theme-zelda==0.4.9

# For development against an unreleased commit, use the git+https form instead:
# RUN pip install --no-cache-dir \
#     "git+https://github.com/sgaduuw/bragi-theme-zelda.git@<sha-or-branch>"
```

#### Admin container

```dockerfile
FROM ghcr.io/sgaduuw/bragi-admin:v1.29.0

# Install from PyPI (pin to a specific version).
RUN pip install --no-cache-dir bragi-theme-zelda==0.4.9

# For development against an unreleased commit, use the git+https form instead:
# RUN pip install --no-cache-dir \
#     "git+https://github.com/sgaduuw/bragi-theme-zelda.git@<sha-or-branch>"
```

Replace the version pin with the version to deploy. v0.1.1 is the first PyPI-published
release; v0.1.0 is git-tag-only. v0.4.9 is the current release.

## Development

### Prerequisites

- Python 3.14+
- [Poetry](https://python-poetry.org/)

### Install

```sh
poetry install
```

### Run against a bragi dev checkout (editable install)

```sh
# From this project's directory, install into bragi's venv as an editable package:
cd ../bragi && poetry run pip install -e ../bragi-theme-zelda

# Then in bragi's working tree, point the Zelda site's theme to "zelda"
# via the admin UI or CLI, and reload the delivery process to pick up template changes.
```

### Commands

```sh
# Run the test suite
poetry run pytest

# Lint
poetry run ruff check src/ tests/

# Format-check
poetry run ruff format --check src/ tests/

# Type-check
poetry run mypy src/
```

## License

MIT. See [LICENSE](LICENSE). Theme code and original assets are MIT-licensed. Third-party
fonts are under their respective open-source licences; see [ASSETS.md](ASSETS.md).
