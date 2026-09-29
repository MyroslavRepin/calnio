import httpx

from backend.core.config import settings
from backend.core.logging import logger


class TelegramRepo:
    """Sends operator notifications to one Telegram chat."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.chat_id = chat_id
        self.client = httpx.Client(
            base_url=f"https://api.telegram.org/bot{bot_token}",
            # A notification is never worth holding a request open for.
            timeout=10.0,
        )

    def send(self, text: str) -> None:
        """Post one message to the configured chat."""
        response = self.client.post(
            "/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
                # A workspace or a display name can contain the characters
                # Telegram's markup would choke on, so the text stays plain.
                "disable_web_page_preview": True,
            },
        )
        response.raise_for_status()


def notify(text: str) -> None:
    """Send a notification, swallowing every failure.

    Notifying the operator must never break the thing that triggered it, so a
    missing bot token is a silent no-op and a Telegram outage is a warning.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    try:
        TelegramRepo(settings.telegram_bot_token, settings.telegram_chat_id).send(text)
    except Exception as exc:
        logger.opt(exception=exc).warning("telegram notification failed")
