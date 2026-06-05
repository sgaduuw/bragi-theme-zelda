# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

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
