from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api.oauth import router as oauth_router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.scheduler import init_scheduler
from backend.services.sync import sync_notion_to_caldav

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = init_scheduler()
    scheduler.add_job(
        sync_notion_to_caldav,
        "interval",
        minutes=int(settings.syncing_interval_minutes),
        max_instances=1,  # never overlap two syncs
        next_run_time=datetime.now(),  # run once immediately on startup
    )
    yield
    scheduler.shutdown(wait=False)  # don't block Ctrl+C on an in-flight sync


app = FastAPI(lifespan=lifespan)

# CORS: the Vue dev app (frontend_url) calls the API cross-origin and must send
# the refresh cookie, so credentials must be allowed and the origin explicit
# (a wildcard origin is rejected by browsers when credentials are included).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SessionMiddleware: stores the OAuth `state` in a signed cookie (CSRF protection).
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

app.include_router(oauth_router)
