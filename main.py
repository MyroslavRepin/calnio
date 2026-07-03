import time

from backend.core.scheduler import init_scheduler
from backend.services.sync import sync_notion_to_caldav

if __name__ == "__main__":
    scheduler = init_scheduler()
    scheduler.add_job(
        sync_notion_to_caldav,
        "interval",
        seconds=30,
        max_instances=1,  # never overlap two syncs
    )
    # Keep main thread alive so the background scheduler keeps running.
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
