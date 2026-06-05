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

## Status: v0.1.3

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

Fonts and sprites are documented row-by-row in [ASSETS.md](ASSETS.md). No ROM-ripped
Nintendo assets; see ASSETS.md for the full sourcing and licence detail.

## Installing

### Recommended: pre-built variant images (v0.1.3+)

From v0.1.3, pre-built images are published on every GitHub Release. Pull the variant
directly instead of writing a downstream Dockerfile:

```dockerfile
# Delivery container — bragi-delivery + bragi-theme-zelda preinstalled.
FROM ghcr.io/sgaduuw/bragi-delivery-zelda:v0.1.3
# That's it. No further pip install step needed.
```

```dockerfile
# Admin container — bragi-admin + bragi-theme-zelda preinstalled.
FROM ghcr.io/sgaduuw/bragi-admin-zelda:v0.1.3
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
FROM ghcr.io/sgaduuw/bragi-delivery:v1.27.3

# Install from PyPI (pin to a specific version).
RUN pip install --no-cache-dir bragi-theme-zelda==0.1.3

# For development against an unreleased commit, use the git+https form instead:
# RUN pip install --no-cache-dir \
#     "git+https://github.com/sgaduuw/bragi-theme-zelda.git@<sha-or-branch>"
```

#### Admin container

```dockerfile
FROM ghcr.io/sgaduuw/bragi-admin:v1.27.3

# Install from PyPI (pin to a specific version).
RUN pip install --no-cache-dir bragi-theme-zelda==0.1.3

# For development against an unreleased commit, use the git+https form instead:
# RUN pip install --no-cache-dir \
#     "git+https://github.com/sgaduuw/bragi-theme-zelda.git@<sha-or-branch>"
```

Replace the version pin with the version to deploy. v0.1.1 is the first PyPI-published
release; v0.1.0 is git-tag-only. v0.1.3 is the current release.

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
