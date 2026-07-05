FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY . .
RUN uv sync --frozen
CMD ["uv", "run", "main.py"]
