from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.deps.db import get_session
from backend.repo.admin import AdminRepo
from backend.repo.telegram import TelegramRepo, stamp

router = APIRouter(tags=["telegram"])

# How many failing syncs one message lists before it stops.
FAILURE_LIMIT = 5


def format_stats(repo: AdminRepo) -> str:
    """The numbers worth reading on a phone."""
    totals = repo.totals()
    syncs = repo.sync_totals()
    events = repo.event_totals()

    return (
        f"Users {totals.users}  (+{totals.signed_up_7d} in 7d)\n"
        f"Notion {totals.notion_connected}   iCloud {totals.icloud_connected}\n"
        f"Set up {totals.with_sync}   Syncing {totals.syncing}\n"
        f"Two-way {totals.two_way}\n\n"
        f"Syncs {syncs.mappings}  on {syncs.enabled}  failing "
        f"{syncs.error + syncs.auth_error}\n"
        f"Events {events.linked_events} across {events.calendars} calendars"
    )


def format_funnel(repo: AdminRepo) -> str:
    """Setup as a sequence, so the step that loses people is obvious."""
    totals = repo.totals()
    lines = [
        f"{step.name}: {step.count}  ({step.share}%)"
        for step in repo.funnel(totals)
    ]
    return "Funnel\n" + "\n".join(lines)


def format_failures(repo: AdminRepo) -> str:
    """Every sync whose last run did not work."""
    failures = repo.failures()
    if not failures:
        return "No failing syncs."

    lines = []
    for failure in failures[:FAILURE_LIMIT]:
        error = failure.error or "no detail"
        lines.append(
            f"user {failure.user_id} {failure.email}\n"
            f"  {failure.database or 'unnamed'}: {failure.status}\n"
            f"  {error[:120]}\n"
            f"  run={failure.run_id or 'none'}"
        )

    answer = f"Failing syncs: {len(failures)}\n\n" + "\n\n".join(lines)
    if len(failures) > FAILURE_LIMIT:
        answer += f"\n\nand {len(failures) - FAILURE_LIMIT} more"
    return answer


def format_health(db: Session) -> str:
    """Whether the database answers, asked the same way the probe asks."""
    from sqlalchemy import text

    try:
        db.execute(text("select 1"))
        return "Database ok"
    except Exception as exc:
        logger.opt(exception=exc).error("telegram health check failed")
        return "Database unreachable"


def build_report(action: str, db: Session) -> str:
    """Turn a button's callback data into the text it asks for."""
    repo = AdminRepo(db)

    if action == "stats":
        return format_stats(repo)
    if action == "funnel":
        return format_funnel(repo)
    if action == "failures":
        return format_failures(repo)
    if action == "health":
        return format_health(db)
    return "Unknown command. Use the buttons."


@router.post("/api/v1/telegram/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def telegram_webhook(
    request: Request,
    secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_session),
):
    """Answer a button tap or a command from the operator's chat.

    This URL is public, so an update is acted on only when it carries the
    secret Telegram was given at setWebhook time and comes from the one chat
    the notifications go to. Anything else is dropped without a word, since
    telling a stranger why they failed is telling them what to fix.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if not settings.telegram_webhook_secret or secret != settings.telegram_webhook_secret:
        logger.warning("telegram webhook: bad or missing secret token")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    update = await request.json()
    callback = update.get("callback_query")
    message = update.get("message")

    if callback:
        action = callback.get("data", "")
        chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))
        callback_id = callback.get("id", "")
    elif message:
        # A typed command, so /stats works as well as the button does.
        action = message.get("text", "").lstrip("/").strip().lower()
        chat_id = str(message.get("chat", {}).get("id", ""))
        callback_id = ""
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if chat_id != settings.telegram_chat_id:
        logger.warning("telegram webhook: update from unexpected chat")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    repo = TelegramRepo(settings.telegram_bot_token, settings.telegram_chat_id)

    # Answered first: Telegram leaves the button spinning for a minute if the
    # report is slow, which reads as a broken bot.
    if callback_id:
        try:
            repo.answer_callback(callback_id)
        except Exception as exc:
            logger.opt(exception=exc).warning("telegram: answering the tap failed")

    if action in ("start", "help", ""):
        body = "Calnio bot. Use the buttons, or /stats /funnel /failures /health"
    else:
        body = build_report(action, db)

    try:
        repo.send(f"{body}\n{stamp()}", buttons=True)
    except Exception as exc:
        logger.opt(exception=exc).warning("telegram: sending the report failed")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
