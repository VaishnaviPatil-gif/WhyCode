"""Disk-backed explanation cache using diskcache."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import diskcache  # type: ignore

from whycode.config import get_config
from whycode.models import AIExplanation


class ExplanationCache:
    """Persist AI explanations keyed by commit, provider, and prompt version.

    Usage
    -----
    cache = ExplanationCache()
    result = cache.get(commit_hash, provider, prompt_version)
    cache.set(commit_hash, provider, prompt_version, explanation)
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        ttl: int | None = None,
    ) -> None:
        config = get_config()
        resolved_dir = (
            Path(cache_dir)
            if cache_dir
            else config.cache_dir
        )
        resolved_dir.mkdir(parents=True, exist_ok=True)
        self._cache: diskcache.Cache = diskcache.Cache(str(resolved_dir))
        self._ttl: int = ttl or config.cache_ttl

    # ── public ────────────────────────────────────────────────────────────────

    def get(
        self,
        commit_hash: str,
        provider: str = "default",
        prompt_version: str = "legacy",
    ) -> AIExplanation | None:
        """Return a cached explanation or *None* on a cache miss."""
        raw: Any = self._cache.get(self._key(commit_hash, provider, prompt_version))
        if raw is None:
            return None
        try:
            return AIExplanation(**raw)
        except (TypeError, KeyError):
            return None

    def set(
        self,
        commit_hash: str,
        provider: str | AIExplanation,
        prompt_version: str | None = None,
        explanation: AIExplanation | None = None,
    ) -> None:
        """Store *explanation* keyed by commit, provider, and prompt version."""
        if isinstance(provider, AIExplanation):
            explanation = provider
            provider = "default"
            prompt_version = "legacy"
        if explanation is None:
            raise ValueError("explanation is required")
        self._cache.set(
            self._key(commit_hash, str(provider), prompt_version or "legacy"),
            explanation.to_dict(),
            expire=self._ttl,
        )

    def invalidate(
        self,
        commit_hash: str,
        provider: str = "default",
        prompt_version: str = "legacy",
    ) -> None:
        """Remove a single entry from the cache."""
        self._cache.delete(self._key(commit_hash, provider, prompt_version))

    def clear(self) -> None:
        """Wipe the entire cache."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def close(self) -> None:
        self._cache.close()

    # ── internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _key(commit_hash: str, provider: str, prompt_version: str) -> str:
        raw = f"{commit_hash}:{provider}:{prompt_version}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"whycode:explanation:{digest}"
