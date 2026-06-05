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

## Status: v0.1.0

v0.1.0 ships the full visual system, MAP sidebar, chrome, pause-menu home, ZZZZZ 404, all
four cosplay JS motifs, and subsetted woff2 fonts (Press Start 2P, Inter Regular + SemiBold,
JetBrains Mono). **Character portraits, item tiles, the heart-container, and the 404 scene art
are placeholder PNGs** (Pillow-generated text-on-coloured-square). The CSS / JS / templates
reference the correct sprite filenames, so v0.1.1 swaps in real art via per-file PNG
replacement with no code changes.

## Asset provenance

Fonts and sprites are documented row-by-row in [ASSETS.md](ASSETS.md). No ROM-ripped
Nintendo assets; see ASSETS.md for the full sourcing and licence detail.

## Installing

The theme is installed into a downstream bragi deployment via a thin `Dockerfile` that
builds on the published bragi images and `pip install`s this package from git.

### Delivery container

```dockerfile
FROM ghcr.io/sgaduuw/bragi-delivery:v1.26.0

RUN pip install --no-cache-dir \
    "git+https://github.com/sgaduuw/bragi-theme-zelda.git@v0.1.0"
```

### Admin container

```dockerfile
FROM ghcr.io/sgaduuw/bragi-admin:v1.26.0

RUN pip install --no-cache-dir \
    "git+https://github.com/sgaduuw/bragi-theme-zelda.git@v0.1.0"
```

Both containers need the package so template lookups work from the admin preview path and
from the public delivery path. Restart both after installation to pick up the plugin.

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
