from __future__ import annotations

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings — loaded from environment / .env file."""

    app_name: str = "modular-monolith-example"
    debug: bool = True
