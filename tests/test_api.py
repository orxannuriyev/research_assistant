from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

import api
from ai.schemas import AnswerWithCitations, Citation, Source
from src.models import ResearchSession
from src.validation import ValidationError


class FakeEngine:
    def __init__(self, settings=None) -> None:
        self.received_question: str | None = None
        self.received_sources: object = None
        self.received_cache: bool | None = None

    def research(self, question, sources, use_cache):
        self.received_question = question
        self.received_sources = sources
        self.received_cache = use_cache
        source = Source(
            title="Offline source",
            url="https://example.test/source",
            snippet="Context",
            origin="web",
        )
        return ResearchSession(
            question=question,
            sources_used=["wikipedia", "web"],
            raw_sources=[source],
            answer=AnswerWithCitations(
                question=question,
                answer="Answer [1].",
                citations=[Citation(index=1, source=source)],
            ),
            created_at=datetime.now(timezone.utc),
            elapsed_seconds=0.1,
        )


def test_api_returns_typed_citations_and_normalized_sources(monkeypatch) -> None:
    fake_engine = FakeEngine()
    monkeypatch.setattr(api, "ResearchEngine", lambda settings: fake_engine)
    client = TestClient(api.app)

    response = client.post(
        "/research",
        json={
            "question": "  What   is AI? ",
            "sources": "wiki,web",
            "no_cache": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "  What   is AI? "
    assert body["llm_provider"] == "openai"
    assert body["sources_used"] == ["wikipedia", "web"]
    assert body["citations"][0]["url"] == "https://example.test/source"
    assert fake_engine.received_question == "  What   is AI? "
    assert fake_engine.received_sources == "wiki,web"
    assert fake_engine.received_cache is False


def test_api_forwards_selected_llm_provider(monkeypatch) -> None:
    fake_engine = FakeEngine()
    captured_settings: dict[str, str] = {}

    def build_engine(settings):
        captured_settings["provider"] = settings.llm_provider
        return fake_engine

    monkeypatch.setattr(api, "ResearchEngine", build_engine)
    response = TestClient(api.app).post(
        "/research",
        json={"question": "Q", "llm_provider": "gemini"},
    )

    assert response.status_code == 200
    assert captured_settings["provider"] == "gemini"


def test_api_uses_default_sources(monkeypatch) -> None:
    fake_engine = FakeEngine()
    monkeypatch.setattr(api, "ResearchEngine", lambda settings: fake_engine)
    client = TestClient(api.app)

    response = client.post("/research", json={"question": "Q"})

    assert response.status_code == 200
    assert fake_engine.received_sources == "web, wikipedia, arxiv"


def test_api_translates_validation_failures(monkeypatch) -> None:
    class RejectingEngine:
        def __init__(self, settings=None) -> None:
            pass

        def research(self, question, sources, use_cache):
            raise ValidationError("Unknown source 'reddit'.")

    monkeypatch.setattr(api, "ResearchEngine", RejectingEngine)
    client = TestClient(api.app)

    response = client.post(
        "/research",
        json={"question": "Q", "sources": "reddit"},
    )

    assert response.status_code == 422
    assert "Unknown source" in response.json()["detail"]


def test_api_translates_provider_failures(monkeypatch) -> None:
    class FailingEngine:
        def __init__(self, settings=None) -> None:
            pass

        def research(self, question, sources, use_cache):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(api, "ResearchEngine", FailingEngine)
    response = TestClient(api.app).post("/research", json={"question": "Q"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Research provider failed."


def test_api_returns_fallback_when_no_answer(monkeypatch) -> None:
    fake_engine = FakeEngine()
    original_research = fake_engine.research

    def no_answer_research(question, sources, use_cache):
        result = original_research(question, sources, use_cache)
        result.answer = None
        result.raw_sources = []
        return result

    fake_engine.research = no_answer_research
    monkeypatch.setattr(api, "ResearchEngine", lambda settings: fake_engine)
    response = TestClient(api.app).post("/research", json={"question": "Q"})

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "No answer could be produced because no sources were retrieved."
    )
    assert response.json()["citations"] == []
