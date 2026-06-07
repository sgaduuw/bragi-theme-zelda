# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.5] - 2026-06-07

### Fixed

- Delivery `/zelda/rom/<game>/<palette>/<sprite>.png` route now reads
  the attachments root from `bragi.settings.settings.attachments_root`
  instead of `current_app.config["BRAGI_ATTACHMENTS_ROOT"]`. Same fix
  as the admin handler got in v0.4.1 — the delivery half of the
  codebase was missed during that cycle, so post-deploy the previews
  hit the right host but the handler 404'd on `_attachments_root()`.
  Closes #59.

## [0.4.4] - 2026-06-07

### Fixed

- Admin ROM upload page's sprite preview grid now emits absolute,
  cross-host URLs (`//{{ site.hostname }}/zelda/rom/la/dmg/<name>.png`)
  instead of relative paths. The ROM delivery blueprint is
  registered via `register_delivery_blueprint` and only exists on
  the delivery app at the site's public hostname; the admin host
  has no such route, so the relative URLs 404'd. Closes #56.

## [0.4.3] - 2026-06-07

### Fixed

- Sprite rendering now actually consults the ROM extraction
  pipeline. The pause-menu home tiles and the callout-textbox
  portrait both used to hardcode `/theme/zelda/static/sprites/...`
  placeholder paths regardless of whether a ROM was uploaded; the
  `rom_sprite_url` Jinja global was dead code. Templates now call
  the helper, which returns the live `/zelda/rom/la/<palette>/<name>.png?v=<sha>`
  extraction URL for manifest-known sprites when a ROM is uploaded
  and falls back to the static placeholder otherwise.
- `make_rom_sprite_helpers` default `static_prefix` corrected from
  `/static/sprites` to `/theme/zelda/static/sprites`. Bragi mounts
  the theme's static dir at the latter; the former 404'd.
- `rom_sprite_url` and `rom_sprite` no longer raise `KeyError` for
  decorative-only sprite names (e.g. `la_pearl`, `kokiri_emerald`,
  `triforce_piece`) that aren't in `SPRITES_LA`. Those names
  resolve to their static placeholder path instead. The ROM
  extraction pipeline cannot produce them regardless of upload
  state, so the helper now matches that reality.
- `_get_current_site` in the `register_template_globals` hookimpl
  guards on `flask.has_app_context()` before reading `g.site`,
  falling back to the null-site helpers when called outside a
  request (e.g. when the callout-textbox macro is rendered from a
  unit test).

## [0.4.2] - 2026-06-07

### Fixed

- ROM upload and delete handlers no longer call a `site.save()`
  method that bragi's SQLAlchemy `Site` model doesn't have.
  Replaced with a `_persist_site_extra_setting(site, key, value)`
  helper that opens a fresh `bragi.core.db.SessionLocal`,
  re-attaches the (detached) site via `session.get(Site, site.id)`,
  mutates the `MutableDict.as_mutable(JSON)`-wrapped
  `extra_settings`, and commits. Same root-cause family as #48
  (Flask config key bragi never populates) and #43 (tests don't
  use the real admin app fixture). Closes #51.

## [0.4.1] - 2026-06-07

### Fixed

- ROM upload and delete handlers in `admin/routes.py` now read the
  attachments root from `bragi.settings.settings.attachments_root`
  instead of `current_app.config["BRAGI_ATTACHMENTS_ROOT"]`. The
  Flask config key was never populated by bragi, so the prior code
  500'd with `KeyError: 'BRAGI_ATTACHMENTS_ROOT'` on every upload
  and delete attempt. Surfaced on first v0.4.0 deploy. The
  canonical bragi pattern (used by `bragi.contrib.attachments`) is
  to import from `bragi.settings`. Closes #48.

## [0.4.0] - 2026-06-07

### Added

- `claims_root_route` hookimpl on the theme plugin. Returns True
  for zelda-themed sites so bragi's welcome-fallback detector (in
  bragi.contrib.admin_notices, available since bragi 1.29.0) does
  not fire a false-positive "Visitors are seeing the default
  welcome page" notice on sites where the theme's pause-menu
  inventory page owns `/`.
- Bumped dev dep on `bragi-cms` to `^1.29` to pick up the new
  hookspec.

## [0.3.1] - 2026-06-07

### Fixed

- ROM upload page (`/admin/sites/<slug>/zelda/rom/upload`) now extends
  bragi's `admin/base.html` so it renders inside the admin chrome instead
  of as a standalone page. Surfaced on first v0.3.0 deploy: the page
  visually looked like leaving the admin area. Closes #38.
- The upload, replace, and delete forms on the ROM management page
  now include the `_csrf_token` hidden field required by bragi's
  global CSRF middleware. Without it the operator could not upload a
  ROM (`CSRF token missing or invalid.`). Closes #39.
- Test fixture for the admin route tests now provides a minimal
  `admin/base.html` and a stub `csrf_token()` Jinja global so the
  templates render under the stub Flask app. (The real bragi admin app
  provides both natively; the stub didn't, which is why the two issues
  above slipped through CI.)

## [0.3.0] - 2026-06-07

### Added

- `admin_notices` hookimpl on the theme plugin: surfaces a
  `zelda.rom_required` action-required notice on the per-site
  admin dashboard, sticky rail, and global admin index when a
  zelda-themed site has no ROM uploaded. Disappears immediately
  after upload (the ROM upload/delete handlers call
  `bragi.api.invalidate_admin_notices(site)`).
- Bumped dev dep on `bragi-cms` to `^1.28` to pick up the new
  hookspec.

### Removed

- Delivery-side ROM upload nudge banner (`_rom_banner.html` + `.rom-banner*` CSS).
  It was gated on a `current_user_is_editor` Jinja variable that bragi does not
  expose to delivery templates: bragi's admin and delivery apps run on separate
  hostnames with separately-scoped session cookies (per bragi `_claude/CONTEXT.md`
  "Admin on its own host"), so the delivery render has no auth context and the
  banner could never render. The intended admin-side nudge will land via a new
  bragi hookspec; see brainstorming notes in `_claude/specs/`.

## [0.2.1] - 2026-06-07

### Fixed

- ROM extraction cache key now includes the file's `mtime_ns`, so an
  atomic ROM swap at the same path (`store_rom`'s `os.replace`) is
  visible to every worker process on the next request -- not just the
  worker that handled the admin POST. Closes #25.
- Admin ROM upload now enforces a 4 MiB + 64 KiB envelope cap via
  `request.content_length` before any multipart parsing, so a
  misbehaving editor cannot OOM the admin worker with an oversize
  body. Returns 413. Closes #26.
- New contrib test exercising the real bragi admin and delivery apps
  to catch signature drift in `bragi.core.permissions` and the
  `register_admin_blueprint` / `register_delivery_blueprint` hookspec
  surface that the stub-based tests in `tests/integration/` would
  miss. Closes #27.

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
