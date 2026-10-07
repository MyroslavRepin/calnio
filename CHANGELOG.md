# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.8.2] - 2026-10-07

### Changed

- Notion is queried for dated pages only, and only for the title and date columns
- Changed calendar events load with calendar-multiget, and an update or a delete sends one request fewer
- iCloud requests send Basic auth up front instead of learning it from a 401
- A run makes at most 500 calendar writes per sync, and the rest follows on the next run
- A rate limit or a Notion outage puts a plain sentence on the sync card

### Fixed

- Notion reads that time out, fail with a 5xx or drop the connection are tried twice more before a sync fails
- An iCloud or Notion rate limit stops that user's run for the tick and leaves the master switch on
- A failed sync report no longer falls back to listing the whole calendar, and a stored `fake-` token no longer keeps it doing so
- An expired sync token recovers in the same run instead of reading as a refused password
- Pages are no longer trashed because a full calendar listing left their events out
- A renamed or retyped date column, or a page that arrives without it, stops the sync instead of deleting its events
- Deleting a sync whose events were already removed in Apple Calendar no longer fails
- Notion client log handlers no longer pile up for the life of the process

## [0.8.1] - 2026-10-06

### Fixed

- The 0.7.1 CalDAV fixes, merged into 0.8: events addressed by path, failed events counted
- A run with failed events lands in the run history as failed, with the count in its error

## [0.8.0] - 2026-10-06

### Added

- Admin split into Overview, Accounts, Syncs, Runs and Errors pages, plus a page per account and per sync
- Every id on the admin pages links to its record, and run ids come with the grep command for the log
- Sync run history, kept 90 days, charting runs, success rate, run time and work done per day
- Admin analytics: time to first sync, signup weeks, syncs per account, stale syncs, commonest failure reasons
- Errors page over a new loguru JSON sink: every warning and error in the app, with its traceback
- Product Hunt gallery GIF and stills, rendered from the video's scenes

### Changed

- A sync's result is committed as soon as it is recorded, so a later sync failing in the same pass cannot undo it

### Fixed

- Crashed requests reach the log file with their traceback instead of only uvicorn's stderr
- Admin account list read a row method instead of the event count

### Removed

- GET /api/v1/admin/stats, replaced by one endpoint per admin page

## [0.7.1] - 2026-10-05

### Changed

- A sync whose events fail one by one is marked as failed, with a count, on its card and the admin page

### Fixed

- Updates and deletes failing with "can't be joined" when iCloud named events on a different host than the calendar

## [0.7.0] - 2026-10-03

### Added

- Guide pages at /notion-apple-calendar-sync, /notion-icloud-calendar and /faq
- Public pages are prerendered, so crawlers read their full text without JavaScript
- robots.txt and a sitemap.xml generated from the router
- Per-page title, description, canonical and JSON-LD; app pages carry noindex
- A 404 page for addresses that do not exist
- Security and privacy section on the landing page
- Setup walkthrough video on the landing page, rendered with Remotion
- Self-hosted Umami analytics: page views, heatmaps, Web Vitals, signup and connect events
- Footer links to every public page and to the author

### Changed

- Landing headline and copy rewritten around Notion Apple Calendar sync
- System font replaces Inter across the landing page and the app
- A trailing slash redirects to the same address without it

### Fixed

- Unknown paths, robots.txt and sitemap.xml no longer answer with the landing page and a 200
- HEAD requests to pages are answered instead of refused with 405

### Removed

- The dashboard screenshot on the landing page, replaced by the setup video

## [0.6.0] - 2026-09-29

### Added

- Landing page rebuilt on its own design system, with alternating dark and light sections
- Hero task table is interactive: ticking a task greys out its calendar event
- Telegram alerts for signup, login, Notion connected, iCloud connected, setup complete and account deleted
- Telegram buttons for stats, funnel, failures and health, answered by a webhook
- Health endpoint at /api/v1/health, reporting whether the database answers
- Greppable run, user and sync ids on every log line, plus a rotating log file
- A failed sync records why it failed and which run said so

### Changed

- Dashboard rebranded onto the landing palette: ink, grey page ground, white cards
- Inter replaces the system font stack across the whole app
- Setup is three steps with one open at a time, rather than three open at once
- The Apple walkthrough states the two-factor requirement before the fields, not after a failure
- The SPA catch-all serves a real file when the build holds one, so images stop answering with index.html

### Fixed

- og:image is an absolute URL, so link previews render when the page is shared
- Sidebar active row is visible again against the grey page ground
- Welcome page no longer claims syncing switches on later in beta
- Em dashes removed from the frontend, per the style guide

### Removed

- The pricing card, replaced by the free stat card on the landing page
- GoogleButton, HowItWorks and GetStarted, folded into the rebuilt landing page

## [0.5.0] - 2026-09-16

### Added
- Admin dashboard at /dashboard/admin: signups, how many people connected each service, a setup funnel showing where people stop, sync and event totals, and one row per account.
- An is_admin flag on users, granted by hand in the database. The admin API answers 404 to everybody else.
- Logs carry run, user and sync ids in a fixed column, so one grep follows one sync from its first query to its last write.
- A failed sync records why it failed and which run said so, shown on the user's sync card and in an admin panel that hands over the grep command for that run.
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
