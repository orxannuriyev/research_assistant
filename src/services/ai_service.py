"""AI Service module with resilience, retry mechanisms, and error handling."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from ai.providers.base import ProviderError

logger = logging.getLogger(__name__)
_provider_lock = threading.Lock()


class AIServiceError(Exception):
    """Base exception for AI Service errors."""
    pass


class AITimeoutError(AIServiceError):
    """Raised when AI service call times out."""
    pass


class AIRetryableError(AIServiceError):
    """Raised when a temporary error occurs that can be retried."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((AIRetryableError, AITimeoutError, ProviderError)),
    reraise=True,
)
def _execute_with_retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Helper to execute an AI call function with retry logic."""
    try:
        return func(*args, **kwargs)
    except (TimeoutError, asyncio.TimeoutError) as exc:
        logger.warning(f"AI call timed out: {exc}. Retrying...")
        raise AITimeoutError("AI service request timed out.") from exc
    except (ConnectionError, OSError) as exc:
        logger.warning(f"Connection error during AI call: {exc}. Retrying...")
        raise AIRetryableError("Network connection error during AI call.") from exc
    except Exception as exc:
        if isinstance(exc, (AIServiceError, AIRetryableError, AITimeoutError)):
            raise exc
        logger.error(f"Unexpected error in AI call: {exc}")
        raise AIServiceError(f"AI service failed: {exc}") from exc


class AIService:
    """Wrapper service for AI operations with retry and robustness features."""

    def __init__(self, ai_client: Any = None, provider: str | None = None) -> None:
        self.ai_client = ai_client
        self.provider = provider

    def synthesize(self, question: str, sources: list[Any]) -> Any:
        """Synthesize a cited answer through the provided AI module."""
        if not question or not question.strip():
            raise AIServiceError("Question cannot be empty for AI generation.")
        if not sources:
            raise AIServiceError("At least one source is required for synthesis.")

        from ai import synthesize as ai_synthesize

        def _call() -> Any:
            llm = self.ai_client
            if llm is None:
                if self.provider is None:
                    return ai_synthesize(question, sources)
                from ai.providers.factory import get_llm

                with _provider_lock:
                    previous = os.environ.get("LLM_PROVIDER")
                    os.environ["LLM_PROVIDER"] = self.provider
                    try:
                        return ai_synthesize(question, sources, llm=get_llm())
                    finally:
                        if previous is None:
                            os.environ.pop("LLM_PROVIDER", None)
                        else:
                            os.environ["LLM_PROVIDER"] = previous
            return ai_synthesize(question, sources, llm=llm)

        try:
            return _execute_with_retry(_call)
        except AIServiceError:
            raise
        except Exception as exc:
            logger.error("AI synthesis failed: %s", exc)
            raise AIServiceError("AI synthesis failed.") from exc

    def summarize_and_answer(self, question: str, context: str) -> str:
        """Retain the legacy text API for callers outside the research engine."""
        if not question or not question.strip():
            raise AIServiceError("Question cannot be empty for AI generation.")

        prompt = (
            f"You are a helpful research assistant. Answer the user's question accurately "
            f"and thoroughly using only the provided context.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}\n\n"
            f"Detailed Answer:"
        )

        def _call_llm() -> str:
            if not self.ai_client:
                return f"Gathered Research Context:\n\n{context}"

            try:
                if hasattr(self.ai_client, "complete"):
                    res = self.ai_client.complete(prompt)
                elif hasattr(self.ai_client, "generate"):
                    res = self.ai_client.generate(prompt)
                else:
                    raise AIRetryableError("AI client has no completion method.")

                if res:
                    return str(res)

                raise AIRetryableError("AI client returned empty response.")
            except Exception as e:
                # Xətanı retry mexanizminin tutması üçün yuxarı fırladırıq
                if "timeout" in str(e).lower():
                    raise AITimeoutError(f"Timeout: {e}") from e
                raise AIRetryableError(f"LLM call error: {e}") from e

        return _execute_with_retry(_call_llm)