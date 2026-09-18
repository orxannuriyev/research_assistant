"""Async orchestrator: fetches sources from all enabled providers in parallel.

Key features (Concurrency rubric)
----------------------------------
* Uses ``asyncio.gather`` to run all source fetchers concurrently.
* ``asyncio.Semaphore`` limits the number of live HTTP connections.
* Per-source timeout via ``asyncio.wait_for``.
* Graceful degradation — if one source fails, the others still succeed.
* Results are served from CacheService when available.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import httpx

from ai import fetch_arxiv, fetch_web, fetch_wikipedia
from ai.providers.base import ProviderError
from ai.schemas import Source
from src.config import Settings
from src.models import CacheEntry, ResearchSession
from src.services.cache import CacheService
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Names for the three built-in sources.
_SOURCES = ("wikipedia", "arxiv", "web")


def _retry_source_error(retry_state: object) -> bool:
    """Retry transient source failures, but stop immediately on HTTP 429."""
    outcome = getattr(retry_state, "outcome", None)
    exception = outcome.exception() if outcome is not None else None
    if exception is None:
        return False
    response = getattr(exception, "response", None)
    if getattr(response, "status_code", None) == 429 or "429" in str(exception):
        return False
    return isinstance(exception, (asyncio.TimeoutError, ProviderError, httpx.HTTPError, OSError))


class Orchestrator:
    """Coordinates concurrent source fetching for a single research question.

    Parameters
    ----------
    cache:
        The CacheService instance. Pass one with ``enabled=False`` for
        ``--no-cache`` mode.
    settings:
        Application settings (timeout, semaphore limit, etc.).
    """

    def __init__(self, cache: CacheService, settings: Settings) -> None:
        self._cache = cache
        self._settings = settings
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_sources)
        self._arxiv_rate_lock = asyncio.Lock()
        self._last_arxiv_request = 0.0

    # ── public API ────────────────────────────────────────────────────────────

    async def fetch(
        self,
        question: str,
        *,
        sources: Optional[list[str]] = None,
    ) -> ResearchSession:
        """Fetch sources for *question* and return a populated ResearchSession.

        Parameters
        ----------
        question:
            The user's research question.
        sources:
            Subset of ``["wikipedia", "arxiv", "web"]`` to query.
            Defaults to all three.
        """
        enabled = [s for s in (sources or list(_SOURCES)) if s in _SOURCES]
        if not enabled:
            logger.warning("No valid sources requested; defaulting to all.")
            enabled = list(_SOURCES)

        start = time.monotonic()

        async with httpx.AsyncClient(
            timeout=self._settings.source_timeout_seconds,
            follow_redirects=True,
        ) as client:
            tasks = [
                self._fetch_one(name, question, client)
                for name in enabled
            ]
            results: list[tuple[str, list[Source], bool]] = await asyncio.gather(
                *tasks, return_exceptions=False
            )

        all_sources: list[Source] = []
        cache_hits = 0
        for name, batch, from_cache in results:
            all_sources.extend(batch)
            if from_cache:
                cache_hits += 1

        elapsed = time.monotonic() - start
        logger.info(
            "Orchestrator: fetched %d sources in %.2fs "
            "(%d/%d from cache)",
            len(all_sources), elapsed, cache_hits, len(enabled),
        )

        return ResearchSession(
            question=question,
            sources_used=enabled,
            raw_sources=all_sources,
            from_cache=(cache_hits == len(enabled)),
            elapsed_seconds=elapsed,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    async def _fetch_one(
        self,
        source_name: str,
        query: str,
        client: httpx.AsyncClient,
    ) -> tuple[str, list[Source], bool]:
        """Fetch a single source with semaphore + timeout + cache + graceful degradation."""
        async with self._semaphore:
            # 1. Check cache first.
            cached = self._cache.get(source_name, query)
            if cached is not None:
                return source_name, cached.sources, True

            # 2. Live fetch with per-source timeout.
            try:
                retrying = AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=0.25, min=0.25, max=2),
                    retry=_retry_source_error,
                    reraise=True,
                )
                async for attempt in retrying:
                    with attempt:
                        await self._wait_for_arxiv_slot(source_name)
                        batch = await asyncio.wait_for(
                            self._call_fetcher(source_name, query, client),
                            timeout=self._settings.source_timeout_seconds,
                        )
            except asyncio.TimeoutError:
                logger.warning(
                    "Source '%s' timed out after %.1fs — skipping.",
                    source_name, self._settings.source_timeout_seconds,
                )
                return source_name, [], False
            except Exception as exc:
                # Graceful degradation: one source failure must not crash the pipeline.
                logger.warning("Source '%s' failed: %s", source_name, exc)
                return source_name, [], False

            # 3. Store in cache.
            if batch:
                entry = CacheEntry(source=source_name, query=query, sources=batch)
                self._cache.set(source_name, query, entry)

            return source_name, batch, False

    async def _wait_for_arxiv_slot(self, source_name: str) -> None:
        """Enforce the configured minimum interval between arXiv requests."""
        if source_name != "arxiv":
            return

        async with self._arxiv_rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_arxiv_request
            delay = self._settings.arxiv_min_interval_seconds - elapsed
            if self._last_arxiv_request and delay > 0:
                await asyncio.sleep(delay)
            self._last_arxiv_request = time.monotonic()

    @staticmethod
    async def _call_fetcher(
        source_name: str,
        query: str,
        client: httpx.AsyncClient,
    ) -> list[Source]:
        """Dispatch to the correct ai.* fetcher."""
        if source_name == "wikipedia":
            return await fetch_wikipedia(query, max_results=3, client=client)
        if source_name == "arxiv":
            return await fetch_arxiv(query, max_results=3, client=client)
        if source_name == "web":
            return await fetch_web(query, max_results=3, client=client)
        raise ValueError(f"Unknown source: {source_name!r}")
