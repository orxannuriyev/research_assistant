from __future__ import annotations

import asyncio
import time

import pytest

from ai.schemas import AnswerWithCitations, Source
from src.config import Settings
from src.engine import ResearchEngine
from src.models import ResearchSession


class FakeOrchestrator:
    async def fetch(self, question: str, *, sources: list[str]) -> ResearchSession:
        return ResearchSession(
            question=question,
            sources_used=sources,
            raw_sources=[
                Source(
                    title="Offline source",
                    url="https://example.test/offline",
                    snippet="Offline context.",
                    origin="web",
                )
            ],
        )


class FakeAIService:
    def synthesize(self, question: str, sources: list[Source]) -> AnswerWithCitations:
        return AnswerWithCitations(question=question, answer="Offline answer [1].")


@pytest.mark.asyncio
async def test_engine_runs_full_offline_pipeline() -> None:
    engine = ResearchEngine(
        orchestrator=FakeOrchestrator(),
        ai_service=FakeAIService(),
        settings=Settings(cache_backend="memory"),
    )

    session = await engine.research_async(
        "What is photosynthesis?",
        sources="wiki,web",
        use_cache=False,
    )

    assert session.question == "What is photosynthesis?"
    assert session.sources_used == ["wikipedia", "web"]
    assert session.answer is not None
    assert session.answer.answer == "Offline answer [1]."


@pytest.mark.asyncio
async def test_engine_times_out_slow_ai_synthesis() -> None:
    class SlowAIService:
        def synthesize(self, question: str, sources: list[Source]) -> AnswerWithCitations:
            time.sleep(0.1)
            return AnswerWithCitations(question=question, answer="too late")

    engine = ResearchEngine(
        orchestrator=FakeOrchestrator(),
        ai_service=SlowAIService(),
        settings=Settings(cache_backend="memory", ai_timeout_seconds=0.01),
    )

    with pytest.raises(asyncio.TimeoutError):
        await engine.research_async("Q", use_cache=False)
