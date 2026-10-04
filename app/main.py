"""Application entrypoint kept for backwards-compatible uvicorn commands."""

from app.api.main import app

__all__ = ["app"]
