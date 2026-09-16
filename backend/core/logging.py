import logging
import sys
from pathlib import Path

from loguru import logger

# Where the rotating log file lives, relative to the working directory. In the
# container that is /app/logs, which docker-compose maps to ./logs on the host,
# so the file survives a restart and can be grepped from a shell.
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "calnio.log"

# Every line carries these, whether or not anything bound them, so a grep for
# "user=4" never misses a line just because it was written outside a sync.
CONTEXT = {"run": "-", "user": "-", "sync": "-"}

# One format for both sinks. The context block sits before the module, so the
# identifiers are in a fixed column and read the same in a terminal and in grep.
FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | "
    "run={extra[run]} user={extra[user]} sync={extra[sync]} | "
    "{name}:{function}:{line} | {message}"
)

COLOR_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | "
    "<yellow>run={extra[run]} user={extra[user]} sync={extra[sync]}</yellow> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru.

    httpx (Notion) and urllib3 (CalDAV) log through stdlib logging, so without
    this bridge their lines never reach our sinks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Re-emit one stdlib record through loguru at the matching level."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """Install the console and file sinks, and bridge stdlib logging into loguru."""
    logger.remove()
    logger.configure(extra=CONTEXT)

    logger.add(sys.stdout, level="INFO", colorize=True, format=COLOR_FORMAT)

    # enqueue=True because the scheduler thread writes here too, and a rotating
    # file wants one writer. diagnose=False because loguru's variable dump would
    # print the values in scope, and some of those are access tokens.
    LOG_DIR.mkdir(exist_ok=True)
    logger.add(
        LOG_FILE,
        level="INFO",
        format=FORMAT,
        rotation="20 MB",
        retention="14 days",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG, force=True)

    # These three narrate every HTTP request and every scheduler tick, which
    # buries the lines a person is actually looking for. Warnings still come
    # through, including APScheduler refusing to start an overlapping run.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    logger.info("logging initialized, writing to {}", LOG_FILE)
