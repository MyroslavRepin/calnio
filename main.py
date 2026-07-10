import time

from backend.core.config import settings
from backend.core.scheduler import init_scheduler
from backend.services.sync import reset_all, sync_notion_to_caldav


def sync_workflow():
    scheduler = init_scheduler()
    sync_notion_to_caldav()  # Start sync func manually
    scheduler.add_job(
        sync_notion_to_caldav,
        "interval",
        minutes=int(settings.syncing_interval_minutes),
        max_instances=1,  # never overlap two syncs
    )
    # Keep main thread alive so the background scheduler keeps running.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt, SystemExit:
        scheduler.shutdown()


if __name__ == "__main__":
    sync_workflow()
    # reset_all()
