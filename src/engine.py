"""Core research engine integrating concurrency, caching, validation, and AI service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from src.config import Settings
from src.concurrency.orchestrator import Orchestrator
from src.models import ResearchSession
from src.services.ai_service import AIService
from src.services.cache import CacheService
from src.storage.cache_store import CacheBackend, FilesystemCache, InMemoryCache
from src.validation import normalize_search_query, normalize_sources, validate_question

logger = logging.getLogger(__name__)


def _build_cache_backend(settings: Settings) -> CacheBackend:
    """Create the configured cache backend."""
    if settings.cache_backend == "memory":
        return InMemoryCache()
    return FilesystemCache(settings.cache_dir)


class ResearchEngine:
    """Orchestrates research workflow across multiple sources and synthesizes answers."""

    def __init__(
        self,
        orchestrator: Orchestrator | None = None,
        cache_store: CacheBackend | CacheService | None = None,
        ai_service: AIService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.ai_service = ai_service or AIService(provider=self.settings.llm_provider)

        if isinstance(cache_store, CacheService):
            cache = cache_store
        else:
            backend = cache_store or _build_cache_backend(self.settings)
            cache = CacheService(backend, self.settings)

        self.cache = cache
        self.orchestrator = orchestrator or Orchestrator(
            cache=cache,
            settings=self.settings,
        )

    async def research_async(
        self,
        question: str,
        sources: str | Sequence[str] | None = None,
        use_cache: bool = True,
    ) -> ResearchSession:
        """Executes full research pipeline asynchronously."""
        clean_question = validate_question(question)
        search_query = normalize_search_query(clean_question)
        target_sources = list(normalize_sources(sources))
        self.cache.enabled = use_cache

        session = await self.orchestrator.fetch(
            search_query,
            sources=target_sources,
        )
        session.question = clean_question
        if session.raw_sources:
            try:
                session.answer = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.ai_service.synthesize,
                        clean_question,
                        session.raw_sources,
                    ),
                    timeout=self.settings.ai_timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.error(
                    "AI synthesis timed out after %.1fs",
                    self.settings.ai_timeout_seconds,
                )
                raise
        else:
            logger.warning("No sources retrieved for question=%r", clean_question)
        return session

    def research(
        self,
        question: str,
        sources: str | Sequence[str] | None = None,
        use_cache: bool = True,
    ) -> ResearchSession:
        """Synchronous wrapper for research_async."""
        return asyncio.run(self.research_async(question, sources, use_cache))