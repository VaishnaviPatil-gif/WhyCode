"""OpenAI provider."""

from __future__ import annotations

from whycode.ai.base import BaseProvider
from whycode.config import get_config


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, model: str | None = None) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ImportError("Run: pip install openai") from exc

        config = get_config()
        self._client = OpenAI(api_key=config.openai_api_key)
        self._model = model or config.openai_model

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
