import tomllib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from sqlalchemy import text

from backend.core.config import settings
from backend.core.db import SessionLocal
from backend.core.logging import logger
from backend.models.sync_settings import STATUS_OK
from backend.repo.admin import AdminRepo
from backend.repo.database import DatabaseRepo
from backend.repo.healthcheck import HealthcheckRepo
from backend.repo.system_settings import SystemSettingsRepo
from backend.repo.telegram import notify
from backend.services.sync import run_all_users

VERSION = tomllib.loads(
    (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text()
)["project"]["version"]

# Alerts currently raised. Only the tick thread touches it, and ticks never
# overlap, so each alert is sent once and resolved once without a lock.
active_alerts: set[str] = set()


def raise_alert(key: str, text: str) -> None:
    """Send an alert, unless it is already active."""
    if key in active_alerts:
        return
    active_alerts.add(key)
    logger.warning("alert {}: {}", key, text.splitlines()[0])
    notify(f"ALERT  {text}", buttons=True)


def clear_alert(key: str, text: str) -> None:
    """Say once that an active alert is over."""
    if key not in active_alerts:
        return
    active_alerts.discard(key)
    logger.info("alert {} resolved", key)
    notify(f"RESOLVED  {text}", silent=True)


def mark_started() -> bool | None:
    """Flag this process as running. Whether the last one stopped cleanly, None if unknown."""
    try:
        with SessionLocal() as db:
            previous = SystemSettingsRepo(db).mark_started()
            db.commit()
            return previous
    except Exception as exc:
        logger.opt(exception=exc).error("could not record startup")
        return None


def mark_stopped() -> None:
    """Flag a graceful shutdown, so the next start does not report a crash."""
    try:
        with SessionLocal() as db:
            SystemSettingsRepo(db).mark_stopped()
            db.commit()
    except Exception as exc:
        logger.opt(exception=exc).error("could not record shutdown")


def report_startup(previous_clean: bool | None) -> None:
    """The startup message: how the last run ended, the database, its migrations."""
    problems: list[str] = []
    lines: list[str] = []

    if previous_clean is None:
        lines.append("previous run: unknown")
    elif previous_clean:
        lines.append("previous run: stopped cleanly")
    else:
        problems.append("crash")
        lines.append("previous run: CRASHED, no clean shutdown (OOM, power, kill)")

    # The container never runs migrations, so a deploy can ship code ahead of
    # its schema. This is where that shows up, before the first failing query.
    try:
        with SessionLocal() as db:
            db.execute(text("select 1"))
            database = DatabaseRepo(db)
            current = database.current_revision()
            head = database.head_revision()
        lines.append("database ok")
        if current == head:
            lines.append(f"migrations at head ({head})")
        else:
            problems.append("migrations")
            lines.append(
                f"migrations BEHIND: db {current}, code {head}\n"
                "run: uv run alembic upgrade head"
            )
    except Exception as exc:
        logger.opt(exception=exc).error("startup database check failed")
        problems.append("database")
        lines.append("database UNREACHABLE")

    if not settings.scheduler_enabled:
        lines.append("scheduler off (SCHEDULER_ENABLED=false)")

    title = f"Calnio {VERSION} started"
    if problems:
        title = f"ALERT  {title}"
    notify(title + "\n" + "\n".join(lines), buttons=True)


def ping_healthcheck(failed: bool) -> None:
    """Ping the dead man's switch, when one is configured. Never raises."""
    if not settings.healthcheck_url:
        return
    try:
        HealthcheckRepo(settings.healthcheck_url).ping(failed)
    except Exception as exc:
        logger.opt(exception=exc).warning("healthcheck ping failed")


def run_tick() -> None:
    """The scheduled job: the sync tick unless the global switch is off, then its alerts."""
    started_at = datetime.now(timezone.utc)
    started = perf_counter()
    try:
        with SessionLocal() as db:
            if not SystemSettingsRepo(db).sync_enabled():
                ping_healthcheck(failed=False)
                return
        run_all_users()
        with SessionLocal() as db:
            runs = AdminRepo(db).runs_since(started_at)
    except Exception as exc:
        logger.opt(exception=exc).error("sync tick crashed")
        raise_alert("tick-crash", f"Sync tick crashed\n{type(exc).__name__}: {exc}")
        ping_healthcheck(failed=True)
        return

    clear_alert("tick-crash", "Sync tick runs again")
    check_failures(runs)
    check_duration(perf_counter() - started)
    ping_healthcheck(failed=False)


def check_failures(runs: list[tuple[str | None, str | None]]) -> None:
    """Alert when half a tick failed: that is Notion or iCloud, not one user."""
    errors = [error for status, error in runs if status != STATUS_OK]
    if len(errors) >= 2 and len(errors) * 2 >= len(runs):
        reasons = Counter((error or "no detail")[:100] for error in errors)
        top = "\n".join(f"{count}x {reason}" for reason, count in reasons.most_common(3))
        raise_alert(
            "mass-failure", f"{len(errors)} of {len(runs)} syncs failed in one tick\n{top}"
        )
    else:
        clear_alert(
            "mass-failure", f"Syncs recovered, {len(runs) - len(errors)} of {len(runs)} ok"
        )


def check_duration(seconds: float) -> None:
    """Alert when a tick outlasts its interval, so the next one gets skipped."""
    interval = int(settings.syncing_interval_minutes)
    if seconds > interval * 60:
        raise_alert(
            "slow-tick",
            f"Sync tick took {seconds / 60:.0f} min, longer than its {interval} min "
            "interval\nusers now sync less often than every tick",
        )
    elif seconds < interval * 60 * 0.8:
        clear_alert("slow-tick", f"Sync tick back to {seconds / 60:.0f} min")
