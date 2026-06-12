"""Compatibility imports for the split AI provider package."""

from whycode.ai import (
    AIEngine,
    BaseProvider,
    ClaudeProvider,
    OllamaProvider,
    OpenAIProvider,
    PROMPT_VERSION,
    _parse_explanation,
    _parse_timeline,
)

__all__ = [
    "AIEngine",
    "BaseProvider",
    "ClaudeProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "PROMPT_VERSION",
    "_parse_explanation",
    "_parse_timeline",
]
