# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- ROM extraction cache key now includes the file's `mtime_ns`, so an
  atomic ROM swap at the same path (`store_rom`'s `os.replace`) is
  visible to every worker process on the next request -- not just the
  worker that handled the admin POST. Closes #25.
- Admin ROM upload now enforces a 4 MiB + 64 KiB envelope cap via
  `request.content_length` before any multipart parsing, so a
  misbehaving editor cannot OOM the admin worker with an oversize
  body. Returns 413. Closes #26.

## [0.2.0] - 2026-06-07

### Added

- Runtime ROM-driven sprite extraction. Site operators can upload their
  Link's Awakening (1993, Game Boy) ROM via the admin UI; the theme
  decodes 2bpp GB tile data from it live on every page render.
- Admin upload page at `/admin/sites/<slug>/zelda/rom/upload` with
  upload, replace, delete, and a live sprite-preview grid.
- Public-site banner shown to logged-in editors prompting ROM upload
  while none is configured.
- `rom_sprite` and `rom_sprite_url` Jinja template globals for
  rendering ROM-extracted sprites with `<picture>`-based light/dark
  palette switching.
- New `register_admin_blueprint` and `register_delivery_blueprint`
  hookimpls on the theme plugin.
- Pillow (`pillow ^12.2`) as a runtime dependency.

### Changed

- `register_template_globals` now also exposes `rom_sprite` and
  `rom_sprite_url` alongside the existing `section_helper` and
  `page_ancestors`.
- The `/zelda/rom/...` delivery Blueprint is now registered via
  `register_delivery_blueprint` (delivery-only) rather than from
  `on_app_init` (which also fires on the admin app).
- Existing placeholder PNGs under `static/sprites/` reorganized to
  match manifest sprite names; the placeholder invariant test now
  enforces parity.

## [0.1.6] - 2026-06-06

### Changed

- Pause-menu inventory grid (`pause_menu.html` + `theme.css`): drop the
  2px border on `.pause-menu__sprite`. It matched the tile frame's own
  2px border in colour and width, reading as a double-walled nested
  frame around an empty sprite area. The sprite's lighter `gb-3` fill
  against the tile's `gb-2` background carries enough contrast on its
  own.
- `.pause-menu__label` font-size bumped from `0.55rem` to `0.625rem`
  (10px exact at the default 16px root). Press Start 2P renders crisply
  at integer pixel sizes; `0.55rem` (~8.8px) subpixel-blurred against
  the tile background.
- `pause_menu.html` title decoration swapped from `- PAUSE -` to
  `<< PAUSE >>`. ASCII hyphens read as a dev placeholder; chevrons echo
  selection arrows from SNES-era menus and stay inside Press Start 2P's
  basic-Latin subset.

Sprite finalisation (replacing the placeholder `LA PEA` / `KOKIRI` /
`OWL ST` PNGs with real pixel-art) is unchanged in this release; it
remains the bigger deferred surface tracked in
`_claude/MEMORY.md` 2026-06-05.

## [0.1.5] - 2026-06-06

### Changed

- Bragi base image bumped from v1.27.3 to v1.27.6 in
  `docker/admin.Dockerfile` and `docker/delivery.Dockerfile`. Brings
  the Ghost-importer `__GHOST_URL__` placeholder substitution fix
  (bragi#376), which restores internal body links on Ghost-imported
  posts and pages on the zelda site. Also picks up bragi's PyPI
  propagation gating fix in `release.yml` (probe with `pip download`
  instead of curl against the JSON endpoint), which only affects
  bragi's own release pipeline but moves the theme onto a base with a
  more reliable release cycle.

### Added

- `.github/workflows/bragi-released.yml`: receiver listening for
  `repository_dispatch` of type `bragi-released`, fired by bragi's
  `release.yml` `notify-themes` matrix job. On dispatch, the workflow
  reads the current `ARG BRAGI_VERSION=` from
  `docker/admin.Dockerfile`, short-circuits if the new version equals
  the current pin, otherwise `sed`s both Dockerfiles to the new
  version and opens a PR via `peter-evans/create-pull-request@v7` on
  branch `bump-bragi-v<new>`. Major-version crossings gain the
  `breaking-base-bump` label. Detection latency drops from ~24h
  (Dependabot's daily poll) to seconds. Dependabot stays in place as
  the backstop in case the dispatch silently fails.

## [0.1.4] - 2026-06-05

### Added

- `.github/dependabot.yml` watching the `docker/` Dockerfiles for
  `ghcr.io/sgaduuw/bragi-admin` / `bragi-delivery` tag updates. When a
  new bragi release publishes container images to GHCR, Dependabot
  opens a PR bumping `ARG BRAGI_VERSION` in both Dockerfiles. Operator
  reviews + merges + cuts a theme PATCH; the new base then bakes into
  the next theme image. Major-version bumps are ignored (template-
  contract changes need deliberate operator review). Lighter-touch
  alternative to wiring `repository_dispatch` from bragi → theme; the
  bragi → theme dependency stays visible as a reviewable PR rather
  than firing as a background workflow.

### Changed

- Breadcrumb partial (`_breadcrumbs.html`) no longer prepends the site
  title as the first crumb. The top bar already shows the brand
  linking to `/`; repeating it in the breadcrumb produced visual
  doubling (especially when the site title overlaps a section name —
  e.g. site "Link's Awakening & Ocarina of Time" → section "Link's
  Awakening" read as a stutter). Breadcrumbs now start at the section
  root. Single-item trails (current page IS the section root) are
  suppressed entirely; the page H1 already conveys "you are here".

### Fixed

- Body link contrast: `--accent-link` darkened from `#1a6b1a` (rupee-green,
  ~3.2:1 against `#9bbc0f` GB-3 body — failed WCAG AA 4.5:1) to
  `#08400a` (~5.8:1, passes AA). Same rupee-green family, just deeper.
  Surfaced during the first zelda.eelcowesemann.nl cutover; body link
  runs were barely distinguishable from surrounding text.
- `resolve_home` rewritten as a pluggy hookwrapper so the pause-menu
  inventory grid always wins at `/` when `site.theme == "zelda"`,
  regardless of whether the operator (or an importer) set
  `site.home_page_id`. Surfaced during the first
  zelda.eelcowesemann.nl cutover from Ghost: the Ghost importer set
  `home_page_id` to an imported `Home` page, and bragi's
  `bragi.contrib.page` plugin's own `@hookimpl(tryfirst=True)`
  `resolve_home` was serving it at `/` with the Zelda chrome but
  without the inventory grid. Two `tryfirst=True` impls compete on
  plugin-discovery order (non-deterministic), so `tryfirst` on our
  side wasn't enough; a hookwrapper that `force_result`s the
  pause-menu response sidesteps the ordering question entirely.
  Regression test added to the integration suite.

## [0.1.3] - 2026-06-05

### Added

- Pre-built container images `ghcr.io/sgaduuw/bragi-admin-zelda` and
  `ghcr.io/sgaduuw/bragi-delivery-zelda`, published on every GitHub
  Release via the new `publish-docker` job in `release.yml`. Each
  image is the corresponding bragi base image (pinned to v1.27.3
  in v0.1.3) with the theme PyPI wheel preinstalled. Operators can
  now `FROM ghcr.io/sgaduuw/bragi-admin-zelda:vX.Y.Z` directly
  instead of writing a downstream Dockerfile to layer the theme on
  top of the bragi base.

## [0.1.2] - 2026-06-05

### Changed

- Dev dep: `bragi @ git+https://...@v1.26.0` replaced with `bragi-cms ^1.27`
  from PyPI. The theme's runtime contract is unchanged (still imports from
  `bragi`); only the install path for the dev/CI venv moves. Faster CI
  install (PyPI CDN vs git clone), no GitHub-side rate-limit risk.

## [0.1.1] - 2026-06-05

First PyPI-published version. No runtime behaviour change from v0.1.0.

### Changed

- Distribution: PyPI publication via Trusted Publishers (OIDC) is now
  the canonical install path. The GitHub Release workflow at
  `.github/workflows/release.yml` publishes sdist + wheel on every
  `release: published` event. v0.1.0 remains git-tag-only; v0.1.1
  is the first PyPI-published version. CONTEXT.md "Distribution"
  section added; CLAUDE.md "Distribution" section updated.
- Move `bragi` git dep from runtime to dev dependencies. PyPI rejects
  packages with direct-URL (git/VCS) dependencies in their published
  metadata; moving it to dev avoids the rejection while preserving the
  dep for local development and the test suite. At runtime the theme is
  always installed inside bragi's own environment where bragi is already
  present as the host app.

## [0.1.0] - 2026-06-05

Initial release. Ships the full LA-game-UI-cosplay theme designed in the
2026-06-04 brainstorming session. See README.md for the highlight list and
`_claude/specs/2026-06-04-bragi-theme-zelda-design.md` for the full design.

### Added

- GB-LCD 4-shade green light mode and GB Pocket greyscale dark mode, switching
  via `prefers-color-scheme`.
- Press Start 2P pixel headings, Inter body, JetBrains Mono code; all fonts
  subsetted to the theme's used glyph range and self-hosted as woff2.
- MAP-styled left sidebar tree (current-section siblings + expanded children).
- OoT section chrome flip: royal-blue + gold accent on `[data-section="oot"]`
  pages via `register_template_globals` hookimpl.
- Seven cosplay motifs: text-box callouts (Owl / Marin / Tarin / Ulrira
  portraits), rupee counter, PUSH START splash, item-acquired flourish,
  pause-menu inventory homepage, ZZZZZ 404, heart-container `<hr>`,
  inventory-row pinned posts.
- `prefers-reduced-motion` static fallbacks for all animated motifs.
- `print.css`: strip chrome for printed walkthroughs.
- `on_app_init` 404 errorhandler replicating bragi's redirect chain then
  serving the ZZZZZ template (workaround until bragi grows
  `register_error_handlers`).
- 23-test suite covering unit, contrib-contract, and integration layers.

### Notes

Real woff2 fonts ship in this release. Character portraits, item tiles, the
heart-container, and the 404 scene art are **placeholder PNGs** (Pillow-
generated text-on-coloured-square). v0.1.1 will swap in real original pixel-art
via per-file PNG replacement with no code changes required.
