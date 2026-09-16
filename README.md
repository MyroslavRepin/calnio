# Calnio

Syncs Notion with Apple Calendar. Notion holds tasks; Apple Calendar is where
people look. Calnio pushes Notion due dates into Apple Calendar via CalDAV on
a schedule.

Notion → Apple Calendar runs by default. Two-way is opt-in, one sync at a
time: switch it on and a moved, renamed or deleted event changes its Notion
page, and an event you add to that calendar becomes a new page. Notion wins
when both sides changed since the last run.

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

Serves on :8082, one uvicorn worker (the scheduler doubles every user's sync
with a second worker).
