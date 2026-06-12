"""Central configuration for whycode."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    openai_api_key: str | None
    anthropic_api_key: str | None
    ollama_url: str
    default_provider: str
    openai_model: str
    claude_model: str
    ollama_model: str
    cache_dir: Path
    cache_ttl: int


def get_config() -> Config:
    """Read environment-backed settings once at component boundaries."""
    return Config(
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        ollama_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        default_provider=os.environ.get("WHYCODE_DEFAULT_PROVIDER", "ollama"),
        openai_model=os.environ.get("WHYCODE_OPENAI_MODEL", "gpt-4o"),
        claude_model=os.environ.get("WHYCODE_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        ollama_model=os.environ.get("WHYCODE_OLLAMA_MODEL", "llama3"),
        cache_dir=Path(os.environ.get("WHYCODE_CACHE_DIR", Path.home() / ".cache" / "whycode")),
        cache_ttl=int(os.environ.get("WHYCODE_CACHE_TTL", 60 * 60 * 24 * 7)),
    )
