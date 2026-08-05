# Stage 1 — build the Vue app. Node only lives here; the final image has no npm.
# VITE_API_URL is deliberately unset: the app falls back to an empty base and
# issues relative requests, which is what same-origin serving needs.
FROM node:22-slim AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — the API, which also serves the built app.
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY . .
RUN uv sync --frozen
COPY --from=frontend /app/dist ./frontend/dist

# --workers 1 is load-bearing: the lifespan in main.py starts an APScheduler, so a
# second worker would run a second scheduler and sync every user twice.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
