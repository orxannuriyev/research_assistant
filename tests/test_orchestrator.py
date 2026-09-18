from __future__ import annotations

import asyncio

import pytest

from ai.schemas import Source
from src.config import Settings
from src.concurrency import orchestrator as orchestrator_module
from src.concurrency.orchestrator import Orchestrator
from src.models import CacheEntry
from src.services.cache import CacheService
from src.storage.cache_store import InMemoryCache


def _source(origin: str) -> Source:
    return Source(
        title=f"{origin} result",
        url=f"https://example.test/{origin}",
        snippet="Useful research context.",
        origin=origin,
    )


@pytest.mark.asyncio
async def test_one_failed_source_does_not_cancel_other_sources(monkeypatch) -> None:
    settings = Settings(
        cache_backend="memory",
        source_timeout_seconds=0.2,
        max_concurrent_sources=3,
    )
    cache = CacheService(InMemoryCache(), settings)
    orchestrator = Orchestrator(cache, settings)

    async def wiki(query, **kwargs):
        await asyncio.sleep(0.01)
        return [_source("wikipedia")]

    async def arxiv(query, **kwargs):
        raise RuntimeError("arxiv unavailable")

    async def web(query, **kwargs):
        await asyncio.sleep(0.01)
        return [_source("web")]

    monkeypatch.setattr(orchestrator_module, "fetch_wikipedia", wiki)
    monkeypatch.setattr(orchestrator_module, "fetch_arxiv", arxiv)
    monkeypatch.setattr(orchestrator_module, "fetch_web", web)

    session = await orchestrator.fetch("photosynthesis")

    assert {source.origin for source in session.raw_sources} == {"wikipedia", "web"}
    assert session.sources_used == ["wikipedia", "arxiv", "web"]


@pytest.mark.asyncio
async def test_cached_source_avoids_fetch(monkeypatch) -> None:
    settings = Settings(cache_backend="memory")
    cache = CacheService(InMemoryCache(), settings)
    cache.set("wikipedia", "photosynthesis", CacheEntry(
        source="wikipedia",
        query="photosynthesis",
        sources=[_source("wikipedia")],
    ))
    orchestrator = Orchestrator(cache, settings)

    async def unexpected_fetch(*args, **kwargs):
        raise AssertionError("cache should have been used")

    monkeypatch.setattr(orchestrator_module, "fetch_wikipedia", unexpected_fetch)
    session = await orchestrator.fetch("photosynthesis", sources=["wikipedia"])

    assert session.from_cache is True
    assert len(session.raw_sources) == 1
