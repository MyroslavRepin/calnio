# Calnio

Syncs Notion with Apple Calendar. Notion holds tasks; Apple Calendar is where
people look. Calnio pushes Notion due dates into Apple Calendar via CalDAV on
a schedule.

One-way sync only: Notion → Apple Calendar. Notion is read-only, nothing
writes back.

## Setup

```bash
uv sync                     # install backend deps
cp .env.example .env        # fill in the values
uv run alembic upgrade head # run migrations
```

## Run

```bash
uv run uvicorn main:app --reload --port 8080   # backend, :8080
cd frontend && npm run dev                      # frontend, :5173
```

## Production

```bash
cp .env.prod.example .env.prod
uv run alembic upgrade head
docker compose up --build
```

Serves on :8080, one uvicorn worker (the scheduler doubles every user's sync
with a second worker).
