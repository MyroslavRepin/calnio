# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.5.0] - 2026-09-16

### Added
- Admin dashboard at /dashboard/admin: signups, how many people connected each service, a setup funnel showing where people stop, sync and event totals, and one row per account.
- An is_admin flag on users, granted by hand in the database. The admin API answers 404 to everybody else.
- Logs carry run, user and sync ids in a fixed column, so one grep follows one sync from its first query to its last write.
- A rotating log file at logs/calnio.log, mapped to the host in production, so logs survive a restart.

### Changed
- Sync failures log a traceback instead of one line of exception text, and messages no longer repeat the ids the context already carries.
- httpx, httpcore, urllib3 and apscheduler log at WARNING, since their per-request lines buried everything else.

## [0.4.0] - 2026-09-15

### Added
- A user can sync several Notion databases at once, each into its own Apple calendar, with its own switch and its own status.
- Setup is one action: ticking databases infers each date column, reuses or creates the calendar, and turns syncing on.
- Two-way sync, per sync and off by default: moving, renaming or deleting an event in Apple Calendar changes its Notion page, and an event made in that calendar becomes a new page.
- Every sync card states its direction, and the Notion connection states whether Calnio may write.

### Changed
- Link rows hold the state both sides last agreed on, and change detection compares content rather than timestamps, so neither direction echoes the other.
- Calendar reads use an RFC 6578 sync token, so a run fetches only what changed and hears about deletions.
- A calendar event is edited in place instead of replaced, keeping alarms, notes and location the user set.
- Notion wins a conflict on a tie, since its edit timestamps are rounded to the minute.
- A grant that may only read keeps its one-way sync running and asks the user to reconnect.
- Landing page and dashboard copy describe what two-way does instead of promising Notion is never written to.

### Fixed
- All-day dates no longer shift by a day when Postgres returns timestamps in the server's zone.
- Calendars served from iCloud's sharded host work, instead of failing on every run.
- A uid iCloud refuses to reuse is replaced with a fresh one rather than failing forever.

### Removed
- synced_events.etag and synced_events.notion_last_edited, which nothing read.

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
