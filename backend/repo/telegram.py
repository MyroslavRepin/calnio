from datetime import datetime

import httpx

from backend.core.config import settings
from backend.core.logging import logger

# The buttons under an alert. Kept here so a notification and the bot's own
# menu offer the same things, and so the callback data has one definition.
MENU = [
    [
        {"text": "Stats", "callback_data": "stats"},
        {"text": "Funnel", "callback_data": "funnel"},
    ],
    [
        {"text": "Failures", "callback_data": "failures"},
        {"text": "Health", "callback_data": "health"},
    ],
]


class TelegramRepo:
    """Sends operator notifications to one Telegram chat."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.chat_id = chat_id
        self.client = httpx.Client(
            base_url=f"https://api.telegram.org/bot{bot_token}",
            # A notification is never worth holding a request open for.
            timeout=10.0,
        )

    def send(self, text: str, *, buttons: bool = False, silent: bool = False) -> None:
        """Post one message to the configured chat."""
        payload: dict = {
            "chat_id": self.chat_id,
            "text": text,
            # A workspace or a display name can contain the characters
            # Telegram's markup would choke on, so the text stays plain.
            "disable_web_page_preview": True,
            # Arrives without a sound. For news, so it never buries an alert.
            "disable_notification": silent,
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": MENU}

        response = self.client.post("/sendMessage", json=payload)
        response.raise_for_status()

    def answer_callback(self, callback_id: str) -> None:
        """Stop the spinner on a tapped button.

        Telegram keeps the button in a loading state for a minute if nothing
        answers, which reads as a broken bot.
        """
        response = self.client.post(
            "/answerCallbackQuery", json={"callback_query_id": callback_id}
        )
        response.raise_for_status()


def stamp() -> str:
    """The server's local time, on its own line under every message."""
    return datetime.now().strftime("%d %b %H:%M")


def notify(text: str, *, buttons: bool = False, silent: bool = False) -> None:
    """Send a notification, swallowing every failure.

    Notifying the operator must never break the thing that triggered it, so a
    missing bot token is a silent no-op and a Telegram outage is a warning.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    try:
        repo = TelegramRepo(settings.telegram_bot_token, settings.telegram_chat_id)
        repo.send(f"{text}\n{stamp()}", buttons=buttons, silent=silent)
    except Exception as exc:
        logger.opt(exception=exc).warning("telegram notification failed")
