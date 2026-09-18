from __future__ import annotations

import asyncio

import pytest

from ai.providers.base import ProviderError
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

@pytest.mark.asyncio
async def test_source_fetch_retries_then_succeeds(monkeypatch) -> None:
    settings = Settings(cache_backend="memory", source_timeout_seconds=0.2)
    orchestrator = Orchestrator(CacheService(InMemoryCache(), settings), settings)
    attempts = 0

    async def flaky_fetch(query, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderError("temporary source failure")
        return [_source("wikipedia")]

    monkeypatch.setattr(orchestrator_module, "fetch_wikipedia", flaky_fetch)
    session = await orchestrator.fetch("photosynthesis", sources=["wikipedia"])

    assert attempts == 2
    assert len(session.raw_sources) == 1


@pytest.mark.asyncio
async def test_rate_limited_source_is_not_retried(monkeypatch) -> None:
    settings = Settings(cache_backend="memory", source_timeout_seconds=0.2)
    orchestrator = Orchestrator(CacheService(InMemoryCache(), settings), settings)
    attempts = 0

    async def rate_limited_fetch(query, **kwargs):
        nonlocal attempts
        attempts += 1
        raise ProviderError("HTTP 429 Too Many Requests")

    monkeypatch.setattr(orchestrator_module, "fetch_wikipedia", rate_limited_fetch)
    session = await orchestrator.fetch("photosynthesis", sources=["wikipedia"])

    assert attempts == 1
    assert session.raw_sources == []


@pytest.mark.asyncio
async def test_arxiv_requests_are_rate_limited(monkeypatch) -> None:
    settings = Settings(cache_backend="memory", arxiv_min_interval_seconds=1.0)
    orchestrator = Orchestrator(CacheService(InMemoryCache(), settings), settings)
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(orchestrator_module.asyncio, "sleep", fake_sleep)
    await orchestrator._wait_for_arxiv_slot("arxiv")
    await orchestrator._wait_for_arxiv_slot("arxiv")

    assert len(sleeps) == 1
    assert sleeps[0] > 0
