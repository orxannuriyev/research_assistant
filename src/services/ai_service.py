"""AI Service module with resilience, retry mechanisms, and error handling."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


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
    retry=retry_if_exception_type((AIRetryableError, AITimeoutError)),
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

    def __init__(self, ai_client: Any = None) -> None:
        if ai_client is None:
            try:
                from ai.providers import get_llm_provider
                self.ai_client = get_llm_provider()
            except Exception as e:
                logger.warning(f"Could not initialize default LLM provider: {e}")
                self.ai_client = None
        else:
            self.ai_client = ai_client

    def summarize_and_answer(self, question: str, context: str) -> str:
        """Summarizes research context and provides a structured answer to the question."""
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
                res = None
                if hasattr(self.ai_client, "generate"):
                    res = self.ai_client.generate(prompt)
                elif hasattr(self.ai_client, "complete"):
                    res = self.ai_client.complete(prompt)
                elif hasattr(self.ai_client, "chat"):
                    res = self.ai_client.chat(prompt)

                # Async cavabları idarə etmək
                if inspect.iscoroutine(res):
                    try:
                        res = asyncio.run(res)
                    except RuntimeError:
                        loop = asyncio.get_event_loop()
                        res = loop.run_until_complete(res)

                if res:
                    if hasattr(res, "text"):
                        return res.text
                    if hasattr(res, "content"):
                        return res.content
                    return str(res)

                raise AIRetryableError("AI client returned empty response.")
            except Exception as e:
                # Xətanı retry mexanizminin tutması üçün yuxarı fırladırıq
                if "timeout" in str(e).lower():
                    raise AITimeoutError(f"Timeout: {e}") from e
                raise AIRetryableError(f"LLM call error: {e}") from e

        return _execute_with_retry(_call_llm)