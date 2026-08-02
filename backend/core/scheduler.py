from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def init_scheduler() -> BackgroundScheduler:
    """Start the background scheduler and hand it back."""
    scheduler.start()
    return scheduler
