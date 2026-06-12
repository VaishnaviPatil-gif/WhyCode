"""Anthropic Claude provider."""

from __future__ import annotations

from whycode.ai.base import BaseProvider
from whycode.config import get_config


class ClaudeProvider(BaseProvider):
    name = "claude"

    def __init__(self, model: str | None = None) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ImportError("Run: pip install anthropic") from exc

        config = get_config()
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._model = model or config.claude_model

    def complete(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text if message.content else ""
