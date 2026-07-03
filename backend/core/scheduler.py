from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def init_scheduler():
    scheduler.start()
    return scheduler
