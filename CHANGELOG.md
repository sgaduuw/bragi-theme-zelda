# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Distribution: PyPI publication via Trusted Publishers (OIDC) is now
  the canonical install path. The GitHub Release workflow at
  `.github/workflows/release.yml` publishes sdist + wheel on every
  `release: published` event. v0.1.0 remains git-tag-only; v0.1.1
  is the first PyPI-published version. CONTEXT.md "Distribution"
  section added; CLAUDE.md "Distribution" section updated.

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
