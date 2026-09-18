from __future__ import annotations

from ai.schemas import AnswerWithCitations
from src.services.ai_service import AIService


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
