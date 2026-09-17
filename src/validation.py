"""Validation and output-sanitization helpers for the CLI."""

from __future__ import annotations

import re
from collections.abc import Sequence

MAX_QUESTION_LENGTH = 500
DEFAULT_SOURCES = ("wikipedia", "arxiv", "web")

_SOURCE_ALIASES = {
    "wiki": "wikipedia",
    "wikipedia": "wikipedia",
    "arxiv": "arxiv",
    "web": "web",
}

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ValidationError(ValueError):
    """Raised when a user-provided value is invalid."""


def validate_question(
    question: str,
    *,
    max_length: int = MAX_QUESTION_LENGTH,
) -> str:
    """Return a normalized, valid research question."""
    if not isinstance(question, str):
        raise ValidationError("Question must be text.")

    normalized = " ".join(question.split())

    if not normalized:
        raise ValidationError("Question cannot be empty.")

    if len(normalized) > max_length:
        raise ValidationError(
            f"Question must not exceed {max_length} characters."
        )

    return normalized


def normalize_sources(
    sources: str | Sequence[str] | None,
) -> tuple[str, ...]:
    """Validate and normalize source names from the CLI."""
    if sources is None:
        return DEFAULT_SOURCES

    raw_sources = sources.split(",") if isinstance(sources, str) else sources

    normalized: list[str] = []
    for source in raw_sources:
        name = source.strip().lower()

        if not name:
            raise ValidationError("Source names cannot be empty.")

        canonical_name = _SOURCE_ALIASES.get(name)
        if canonical_name is None:
            allowed = ", ".join(DEFAULT_SOURCES)
            raise ValidationError(
                f"Unknown source {source!r}. Allowed sources: {allowed}."
            )

        if canonical_name not in normalized:
            normalized.append(canonical_name)

    if not normalized:
        raise ValidationError("At least one source must be selected.")

    return tuple(normalized)


def sanitize_output(text: str) -> str:
    """Remove control characters from text before showing it to a user."""
    if not isinstance(text, str):
        raise ValidationError("Output must be text.")

    cleaned = _CONTROL_CHARS.sub("", text)
    return cleaned.strip()