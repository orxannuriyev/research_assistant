from __future__ import annotations

import pytest

from ai.schemas import AnswerWithCitations, Citation, Source
from src.cli import parse_args, render_answer
from src.validation import ValidationError, normalize_search_query


def test_cli_parses_sources_and_no_cache() -> None:
    args = parse_args(["ask", "  What   is AI? ", "--sources", "wiki,arxiv", "--no-cache"])

    assert args.question == "What is AI?"
    assert args.sources == ("wikipedia", "arxiv")
    assert args.no_cache is True


def test_cli_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        parse_args(["ask", "   "])


def test_cli_renders_numbered_references() -> None:
    source = Source(
        title="A source",
        url="https://example.test/source",
        snippet="Context",
        origin="web",
    )
    answer = AnswerWithCitations(
        question="Q",
        answer="An answer [1].",
        citations=[Citation(index=1, source=source)],
    )

    rendered = render_answer(answer)
    assert "An answer [1]." in rendered
    assert "[1] (web) A source" in rendered
    assert "https://example.test/source" in rendered

def test_cli_renders_missing_answer() -> None:
    assert render_answer(None) == (
        "No answer could be produced because no sources were retrieved."
    )

def test_cli_rejects_unknown_source() -> None:
    with pytest.raises(ValidationError, match="Unknown source"):
        parse_args(["ask", "Q", "--sources", "reddit"])


def test_search_query_removes_trailing_punctuation() -> None:
    assert normalize_search_query("  What   is photosynthesis?! ") == (
        "What is photosynthesis"
    )
