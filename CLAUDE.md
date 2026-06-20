# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calnio is a FastAPI-based Python application using Python 3.14+. The project uses `uv` as the package manager.

## Development Setup

### Package Management
- **Package manager**: `uv` (not pip)
- **Install dependencies**: `uv sync`
- **Add dependency**: `uv add <package>`
- **Add dev dependency**: `uv add --dev <package>`

### Running the Application
- **Start development server**: `uv run uvicorn main:app --reload`
- **Run with specific host/port**: `uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`

## Project Structure

```
.
├── backend/          # Backend application code
│   ├── api/         # API endpoints/routes
│   ├── core/        # Core configuration and settings
│   ├── deps/        # Dependencies and dependency injection
│   └── services/    # Business logic and services
├── main.py          # Application entry point
├── pyproject.toml   # Project dependencies and metadata
└── .env             # Environment variables (not committed)
```

## Key Technologies

- **Framework**: FastAPI
- **Validation**: Pydantic v2
- **Settings Management**: pydantic-settings
- **Python**: 3.14+