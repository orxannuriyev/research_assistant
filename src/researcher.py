"""Core research engine integrating concurrency, caching, validation, and AI service."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Sequence

from src.config import Settings
from src.concurrency.orchestrator import Orchestrator
from src.services.ai_service import AIService
from src.validation import normalize_sources, sanitize_output, validate_question

logger = logging.getLogger(__name__)


class FlexibleMockCache:
    """Fallback cache class accepting any combination of positional/keyword arguments."""

    def get(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def set(self, *args: Any, **kwargs: Any) -> None:
        pass


def _get_cache_instance() -> Any:
    """Tries to instantiate CacheStore, otherwise falls back to FlexibleMockCache."""
    try:
        import src.storage.cache_store as cache_module
        cache_cls = getattr(
            cache_module,
            "CacheStore",
            getattr(cache_module, "Cache", getattr(cache_module, "CacheManager", None)),
        )
        if cache_cls:
            return cache_cls()
    except Exception as e:
        logger.warning(f"Could not initialize CacheStore: {e}")
    return FlexibleMockCache()


class ResearchEngine:
    """Orchestrates research workflow across multiple sources and synthesizes answers."""

    def __init__(
        self,
        orchestrator: Orchestrator | None = None,
        cache_store: Any = None,
        ai_service: AIService | None = None,
    ) -> None:
        self.cache_store = cache_store or _get_cache_instance()
        self.settings = Settings()

        self.orchestrator = orchestrator or Orchestrator(
            cache=self.cache_store,
            settings=self.settings,
        )

        if not hasattr(self.orchestrator, "cache") or self.orchestrator.cache is None:
            self.orchestrator.cache = self.cache_store

        self.ai_service = ai_service or AIService()

    def _call_orchestrator(self, query: str, sources: list[str]) -> Any:
        """Finds and executes the fetch method on Orchestrator, handling sync and async results safely."""
        res = None
        for attr in ["fetch_all", "fetch", "run", "search", "fetch_sources"]:
            if hasattr(self.orchestrator, attr):
                method = getattr(self.orchestrator, attr)
                try:
                    res = method(query=query, sources=sources)
                except TypeError:
                    try:
                        res = method(query, sources)
                    except TypeError:
                        res = method(query)
                break

        if inspect.iscoroutine(res):
            try:
                res = asyncio.run(res)
            except RuntimeError:
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    pass
                loop = asyncio.get_event_loop()
                res = loop.run_until_complete(res)

        return res

    def research(
        self,
        question: str,
        sources: str | Sequence[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Executes full research pipeline for a given question and sources."""
        clean_question = validate_question(question)
        target_sources = normalize_sources(sources)

        logger.info(
            f"Researching question: '{clean_question}' on sources: {target_sources}"
        )

        cache_key = f"{clean_question}:{','.join(sorted(target_sources))}"

        if use_cache and self.cache_store is not None:
            try:
                cached_result = self.cache_store.get(cache_key)
                if cached_result:
                    logger.info("Found cached answer.")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")

        raw_results = self._call_orchestrator(clean_question, target_sources)

        context_blocks = []
        
        # Raw sources/results obyektini daxili mətnə çevirmək
        if isinstance(raw_results, dict):
            for src, content in raw_results.items():
                if content:
                    context_blocks.append(f"[{str(src).upper()}]: {content}")
        elif isinstance(raw_results, list):
            for item in raw_results:
                snippet = getattr(item, "snippet", getattr(item, "text", str(item)))
                title = getattr(item, "title", "")
                context_blocks.append(f"{title}: {snippet}" if title else str(snippet))
        elif raw_results:
            context_blocks.append(str(raw_results))

        combined_context = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "No information found from sources."
        )

        # AI Servisdən cavabı almaq
        res = self.ai_service.summarize_and_answer(
            question=clean_question, context=combined_context
        )

        # Əgər res obyekt, dict və ya None olarsa onun mətn sahəsini götürmək
        if isinstance(res, dict):
            raw_answer = res.get("answer") or res.get("summary") or str(res)
        elif hasattr(res, "answer"):
            raw_answer = getattr(res, "answer")
        elif hasattr(res, "summary"):
            raw_answer = getattr(res, "summary")
        else:
            raw_answer = str(res)

        # Əgər cavab `None` çıxarsa və mənbələrdə məlumat varsa, mənbələri göstəririk
        if not raw_answer or raw_answer == "None":
            raw_answer = f"Based on gathered research:\n\n" + combined_context

        clean_answer = sanitize_output(raw_answer)

        final_response = {
            "question": clean_question,
            "sources": target_sources,
            "answer": clean_answer,
            "raw_sources_count": len(context_blocks),
        }

        if use_cache and self.cache_store is not None:
            try:
                self.cache_store.set(cache_key, final_response)
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")

        return final_response