"""Typed application settings loaded from environment variables.

Usage
-----
    from src.config import Settings, get_settings

    s = Settings()               # reads from os.environ / .env
    s = get_settings()           # cached singleton (same process)

All fields have defaults so the app starts even without a .env file —
useful for offline tests and CI runs that don't need a real LLM.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Research Assistant.

    Pydantic-settings reads values from (in priority order):
      1. Environment variables
      2. A .env file in the working directory
      3. The defaults defined below
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",       # silently ignore unknown env vars
        case_sensitive=False,
    )

    # ── LLM provider ──────────────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="Which LLM backend to use.",
    )
    openai_api_key: str = Field(default="", description="OpenAI API key.")
    anthropic_api_key: str = Field(default="", description="Anthropic API key.")
    gemini_api_key: str = Field(default="", description="Google Gemini API key.")

    # ── Web search provider ────────────────────────────────────────────────────
    web_search_provider: Literal["tavily", "serper", "duckduckgo"] = Field(
        default="tavily",
        description="Which web search backend to use.",
    )
    tavily_api_key: str = Field(default="", description="Tavily API key.")
    serper_api_key: str = Field(default="", description="Serper API key.")

    # ── Cache ──────────────────────────────────────────────────────────────────
    cache_backend: Literal["filesystem", "memory"] = Field(
        default="filesystem",
        description="Cache storage backend.",
    )
    cache_dir: str = Field(
        default=".cache",
        description="Directory for filesystem cache (relative to project root).",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=0,
        description="Time-to-live for cache entries in seconds. 0 = never expire.",
    )

    # ── Concurrency ────────────────────────────────────────────────────────────
    max_concurrent_sources: int = Field(
        default=5,
        ge=1,
        le=20,
        description="asyncio.Semaphore limit for parallel source fetches.",
    )
    source_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Per-source HTTP timeout in seconds.",
    )
    ai_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="Maximum time allowed for one AI synthesis call.",
    )
    arxiv_min_interval_seconds: float = Field(
        default=1.0,
        ge=0,
        description="Minimum interval between arXiv requests in one orchestrator.",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Python logging level.",
    )

    @field_validator("cache_ttl_seconds", mode="before")
    @classmethod
    def _ttl_non_negative(cls, v: int) -> int:
        if int(v) < 0:
            raise ValueError("cache_ttl_seconds must be >= 0")
        return int(v)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton.

    Call ``get_settings.cache_clear()`` in tests to reset.
    """
    return Settings()
