from __future__ import annotations

import pytest

from ai.schemas import AnswerWithCitations
from src.services.ai_service import (
    AIService,
    AIServiceError,
    AITimeoutError,
    _execute_with_retry,
)


def test_ai_service_returns_cited_answer(fake_llm, sample_sources) -> None:
    result = AIService(ai_client=fake_llm).synthesize(
        "What is photosynthesis?", sample_sources
    )

    assert isinstance(result, AnswerWithCitations)
    assert {citation.index for citation in result.citations} == {1, 2}
    assert len(fake_llm.calls) == 1


def test_ai_service_retries_transient_synthesis_failure(sample_sources) -> None:
    class FlakyLLM:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, prompt: str, **kwargs: object) -> str:
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("temporary failure")
            return "Recovered answer [1]."

    client = FlakyLLM()
    result = AIService(ai_client=client).synthesize("Q", sample_sources)

    assert result.answer == "Recovered answer [1]."
    assert client.calls == 2

def test_ai_service_rejects_empty_inputs(sample_sources) -> None:
    service = AIService(ai_client=object())

    with pytest.raises(AIServiceError, match="Question cannot be empty"):
        service.synthesize("   ", sample_sources)

    with pytest.raises(AIServiceError, match="At least one source"):
        service.synthesize("Q", [])


def test_legacy_text_api_uses_context_without_client() -> None:
    result = AIService().summarize_and_answer("Q", "context")

    assert result == "Gathered Research Context:\n\ncontext"


def test_legacy_text_api_supports_complete_client() -> None:
    class CompleteClient:
        def complete(self, prompt: str) -> str:
            assert "Question: Q" in prompt
            return "completed"

    assert AIService(CompleteClient()).summarize_and_answer("Q", "context") == "completed"


def test_legacy_text_api_supports_generate_client() -> None:
    class GenerateClient:
        def generate(self, prompt: str) -> str:
            return "generated"

    assert AIService(GenerateClient()).summarize_and_answer("Q", "context") == "generated"


def test_legacy_text_api_rejects_unsupported_client() -> None:
    with pytest.raises(AIServiceError, match="LLM call error"):
        AIService(object()).summarize_and_answer("Q", "context")


def test_retry_helper_preserves_timeout_errors() -> None:
    def fail() -> None:
        raise AITimeoutError("timed out")

    with pytest.raises(AITimeoutError, match="timed out"):
        _execute_with_retry(fail)


def test_retry_helper_wraps_unexpected_errors() -> None:
    def fail() -> None:
        raise ValueError("bad response")

    with pytest.raises(AIServiceError, match="AI service failed"):
        _execute_with_retry(fail)
