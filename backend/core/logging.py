import logging
import sys

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Route stdlib `logging` records into loguru.

    Third-party libs (httpx for Notion, urllib3/requests for CalDAV) log via
    stdlib logging, not loguru. Without this bridge their HTTP lines never
    reach our sinks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    logger.add(
        "logs/calnio.log",
        rotation="10 MB",
        retention="30 days",
        level="DEBUG",
        compression="zip",
        enqueue=True,
    )

    # Bridge stdlib logging -> loguru so HTTP logs show up.
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.DEBUG, force=True)

    # httpx (Notion) logs each request at INFO -> visible on console.
    logging.getLogger("httpx").setLevel(logging.INFO)
    # urllib3 (CalDAV) request detail is DEBUG-only and noisy -> file only.
    logging.getLogger("urllib3").setLevel(logging.INFO)

    logger.info("Logging initialized")
