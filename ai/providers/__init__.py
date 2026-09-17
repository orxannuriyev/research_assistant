"""Groq LLM Provider Integration with Clean Auto Discovery."""

from __future__ import annotations

import os
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GroqLLMCaller:
    """Direct LLM caller using Groq API with auto-detected active models."""

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment or .env file.")

        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
        except ImportError:
            raise RuntimeError("Please install groq package: pip install groq")

    def _get_active_models(self) -> list[str]:
        """Fetch all available active models from Groq account."""
        try:
            models_page = self.client.models.list()
            return [m.id for m in models_page.data if getattr(m, "active", True)]
        except Exception:
            return []

    def generate(self, prompt: str) -> str:
        available_models = self._get_active_models()
        
        if not available_models:
            raise RuntimeError("No active models found in Groq account.")

        last_error = None
        # Groq-un hesabınızda təqdim etdiyi HƏR BİR modeli sırayla sınayırıq
        for model in available_models:
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                return completion.choices[0].message.content
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All available Groq models ({available_models}) failed. Error: {last_error}")


def get_llm_provider() -> Any:
    """Returns Groq LLM provider."""
    return GroqLLMCaller()


__all__ = ["get_llm_provider"]