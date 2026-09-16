"""Core Pydantic models for the Research Assistant SE layer.

These models cross module boundaries — every public function that
returns structured data must use one of these, never a naked dict.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ai.schemas import AnswerWithCitations, Source


class CacheEntry(BaseModel):
    """A single cached research result.

    `expires_at` is a UTC timestamp (epoch seconds).
    A value of 0 means the entry never expires.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(description="Source identifier, e.g. 'wikipedia'.")
    query: str = Field(description="The canonical (normalised) query string.")
    sources: list[Source] = Field(
        default_factory=list,
        description="Raw sources retrieved from this (source, query) pair.",
    )
    created_at: float = Field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp(),
        description="Unix timestamp (UTC) when this entry was created.",
    )
    expires_at: float = Field(
        default=0.0,
        description="Unix timestamp (UTC) after which the entry is stale. 0 = never.",
    )

    def is_expired(self) -> bool:
        """Return True if the entry has passed its TTL."""
        if self.expires_at == 0.0:
            return False
        return datetime.now(timezone.utc).timestamp() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (JSON-safe)."""
        return {
            "source": self.source,
            "query": self.query,
            "sources": [s.model_dump() for s in self.sources],
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Deserialise from a plain dict (e.g. loaded from JSON)."""
        return cls.model_validate(data)


class ResearchSession(BaseModel):
    """A complete research session: question → sources → answer.

    Created by the Orchestrator and returned to the CLI / Web UI.
    """

    model_config = ConfigDict(extra="forbid")

    question: str = Field(description="The original user question.")
    sources_used: list[str] = Field(
        default_factory=list,
        description="Source names that were queried, e.g. ['wikipedia', 'arxiv', 'web'].",
    )
    raw_sources: list[Source] = Field(
        default_factory=list,
        description="All Source objects retrieved (may come from cache).",
    )
    answer: AnswerWithCitations | None = Field(
        default=None,
        description="The synthesised answer. None if synthesis failed.",
    )
    from_cache: bool = Field(
        default=False,
        description="True if every source batch was served from cache.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this session was created (UTC).",
    )
    elapsed_seconds: float = Field(
        default=0.0,
        ge=0,
        description="Wall-clock time for the full pipeline in seconds.",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe dict for artefacts/ output."""
        return {
            "question": self.question,
            "sources_used": self.sources_used,
            "from_cache": self.from_cache,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "created_at": self.created_at.isoformat(),
            "answer": self.answer.to_dict() if self.answer else None,
        }
