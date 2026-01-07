# Changelog

All notable changes to this project will be documented here.

## [1.3.0] - 2026-01-06

### Added
- Support for custom stream provider display names via environment variables:
  - `STREAM_PROVIDER_NAME_INTERNAL`
  - `STREAM_PROVIDER_NAME_EXTERNAL`

### Changed
- Improved file size display in stream titles:
  - Files under 1 GB now display in MB
  - Files 1 GB and larger display in GB
- Refactored stream construction logic to use a shared helper for movies and series (no behavior change)
- Automatic library refresh via scheduled background scans:
  - New cron-based scan sidecar container
  - Configurable scan schedule using `SCAN_CRON`
  - Uses existing admin scan endpoint and `ADMIN_SCAN_TOKEN`
- Support for configurable media folder names:
  - Movie and series subfolder names under `/media` can now be customized
  - Controlled via `MOVIES_DIR_NAME` and `SERIES_DIR_NAME`
  - Defaults remain `movies` and `series` for backward compatibility

### Notes
- No breaking changes
- Existing configurations continue to work without modification

## 1.2.0
- Default prevention of duplicate catalogs when using internal + external access
- Clarified and enforced token-based security model
- Improved admin scanning behavior and documentation
- Hardened proxy / API responsibility boundaries

## 1.1.2
- Minor fixes and documentation updates
