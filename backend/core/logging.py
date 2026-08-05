import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru.

    httpx (Notion) and urllib3 (CalDAV) log through stdlib logging, so without
    this bridge their HTTP lines never reach our sinks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Re-emit one stdlib record through loguru at the matching level."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """Install the console sink and bridge stdlib logging into loguru."""
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

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG, force=True)

    # Both libraries log every request at DEBUG, which drowns a sync run.
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)

    logger.info("logging initialized")
