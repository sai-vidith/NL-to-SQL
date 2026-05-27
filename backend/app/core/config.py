"""
Nexus — NL-to-SQL Analytics Platform
Core Configuration using Pydantic Settings
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "Nexus"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./nexus.db"
    database_readonly_url: str | None = None
    enable_in_memory_db: bool = False  # Load complete business schema into RAM for 100x query speeds

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str | None = None
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None

    # ── Gemini AI ────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # ── Hugging Face AI ──────────────────────────────────────────
    huggingface_api_key: str = ""
    huggingface_embedding_model: str = "sentence-transformers/all-mpnet-base-v2"


    # ── JWT Authentication ───────────────────────────────────────
    jwt_secret: str = "change-this-in-production-use-a-strong-random-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── Telegram Bot ─────────────────────────────────────────────
    telegram_bot_token: str | None = None
    telegram_webhook_url: str | None = None
    telegram_webhook_secret: str | None = None

    # ── Rate Limiting ────────────────────────────────────────────
    rate_limit_per_minute: int = 50

    # ── Query Safety ─────────────────────────────────────────────
    query_timeout_seconds: int = 10
    max_result_rows: int = 1000

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000", "*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def readonly_db_url(self) -> str:
        """Returns read-only DB URL, falling back to main DB URL."""
        return self.database_readonly_url or self.database_url

    @property
    def redis_available(self) -> bool:
        """Check if Redis configuration is available."""
        return bool(self.redis_url or self.upstash_redis_rest_url)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
