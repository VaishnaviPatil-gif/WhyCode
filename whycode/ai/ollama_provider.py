"""Ollama provider."""

from __future__ import annotations

from whycode.ai.base import BaseProvider
from whycode.config import get_config


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, model: str | None = None) -> None:
        try:
            import ollama  # type: ignore
        except ImportError as exc:
            raise ImportError("Run: pip install ollama") from exc

        config = get_config()
        self._ollama = ollama
        self._model = model or config.ollama_model
        self._host = config.ollama_url

    def complete(self, system: str, user: str) -> str:
        response = self._ollama.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": 0.2},
        )
        return response["message"]["content"]
