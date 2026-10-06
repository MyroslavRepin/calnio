import json
from datetime import datetime, timezone

from backend.schemas.admin import AdminLogEntry


class LogParser:
    """Loguru's serialized records into log entries."""

    def parse_entry(self, line: str) -> AdminLogEntry | None:
        """One line of problems.json, or None for a line cut in half."""
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None

        record = payload["record"]
        extra = record["extra"]
        exception = record["exception"]
        message = record["message"]

        # The sink's format is the bare message, so whatever follows it in the
        # rendered text is the traceback.
        error_type = None
        traceback = None
        if exception is not None:
            error_type = exception["type"]
            traceback = payload["text"][len(message) :].strip() or None

        return AdminLogEntry(
            time=datetime.fromtimestamp(record["time"]["timestamp"], tz=timezone.utc),
            level=record["level"]["name"],
            run_id=self.parse_text(extra.get("run")),
            user_id=self.parse_id(extra.get("user")),
            mapping_id=self.parse_id(extra.get("sync")),
            location=f"{record['name']}:{record['function']}:{record['line']}",
            message=message,
            error_type=error_type,
            traceback=traceback,
        )

    def parse_text(self, value: object) -> str | None:
        """A context value, with the "-" placeholder read as missing."""
        if value is None or value == "-":
            return None
        return str(value)

    def parse_id(self, value: object) -> int | None:
        """A context id, or None for the placeholder."""
        text = self.parse_text(value)
        if text is None or not text.isdigit():
            return None
        return int(text)
