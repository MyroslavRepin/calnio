# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.3.0] - 2026-08-11

### Changed
- Production database moved from managed Neon to self-hosted Postgres on the same host as the app.
- Docker prod container uses network_mode: host to reach the local Postgres, and now serves on :8082 internally.

## [0.2.0] - 2026-08-11

### Added
- Global sync switch (`system_settings`), scheduler tick skips every user when it's off.

## [0.1.1] - 2026-08-10

### Added
- Block selecting a Reminders calendar during Apple Calendar setup.

## [0.1.0] - 2026-08-09

### Added
- One-way Notion → Apple Calendar sync via CalDAV, on a schedule (APScheduler).
- Per-user sync: own Notion connection, iCloud credential, and sync settings row per user.
- Google OAuth login, cookie-based JWT access and refresh tokens.
- Per-user iCloud app-specific-password setup wizard.
- Per-user Notion OAuth connection with database picker.
- Account deletion, cascades user data, revokes the Notion grant, cancels queued sync jobs.
- Dashboard shell with Overview, Connections and Settings.
- Onboarding welcome flow with setup progress and due-date column picker.
- Production Docker image serving the built Vue app from FastAPI.
- Landing page and app frontend design system.

### Changed
- Rewrote `api/`, `repo/`, `services/` and `core/` layers to follow the conventions in CLAUDE.md.

### Fixed
- Sync loop indentation bug that skipped event updates.
- Docker port mapping.

### Removed
- `caldav_events` full-mirror table, replaced by the `synced_events` link index.
