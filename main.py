from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.api.account import router as account_router
from backend.api.apple_calendar import router as apple_calendar_router
from backend.api.notion import router as notion_router
from backend.api.oauth import router as oauth_router
from backend.api.sync import router as sync_router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.scheduler import init_scheduler
from backend.services.sync import run_all_users

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the scheduler, schedule the sync tick, stop it on shutdown."""
    # The scheduler starts either way, because turning a user's sync on queues
    # a one-off job through it and that path is gated separately.
    scheduler = init_scheduler()
    if settings.scheduler_enabled:
        scheduler.add_job(
            run_all_users,
            "interval",
            minutes=int(settings.syncing_interval_minutes),
            max_instances=1,  # never overlap two ticks
            next_run_time=datetime.now(),  # run once immediately on startup
        )
    yield
    scheduler.shutdown(wait=False)  # do not block Ctrl+C on an in-flight sync


app = FastAPI(lifespan=lifespan)

# The Vue dev app calls the API cross-origin and must send the refresh cookie,
# so credentials are allowed and the origin is explicit. Browsers reject a
# wildcard origin once credentials are included.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Holds the OAuth state in a signed cookie. Its policy has to match the auth
# cookies rather than Starlette's lax default: Notion's connect flow asks for
# its authorize URL over a cross-origin XHR, and a session cookie set on that
# response is only usable cross-site as SameSite=None and Secure.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site=settings.cookie_samesite,
    https_only=settings.cookie_secure,
)

app.include_router(oauth_router)
app.include_router(apple_calendar_router)
app.include_router(notion_router)
app.include_router(sync_router)
app.include_router(account_router)

# The built Vue app, served same-origin in prod. Resolved from this file rather
# than the working directory, and present only inside the Docker image. In dev
# the directory is absent and the app stays a bare API.
DIST = Path(__file__).parent / "frontend" / "dist"

if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    # Declared after every router so real endpoints win. The Vue router runs in
    # history mode, so a hard refresh of /dashboard/connections asks the server
    # for a path that is not a file and has to be answered with index.html.
    @app.get("/{spa_path:path}", include_in_schema=False)
    async def spa(spa_path: str) -> FileResponse:
        """Serve index.html for any path the routers did not claim."""
        # An unmatched API path stays JSON: HTML with a 200 would make a typo'd
        # endpoint look like a successful request.
        if spa_path.startswith(("api/", "auth/")):
            raise HTTPException(status_code=404, detail="Not Found")
        # index.html must not be cached: it references hashed bundle names that
        # a redeploy replaces, and a stale copy points at files that are gone.
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
