"""Base provider, prompts, parsers, and AIEngine facade."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from whycode.config import get_config
from whycode.models import AIExplanation, BlameChunk, CommitInfo

PROMPT_VERSION = "2026-06-08.context-quality.v1"

_SYSTEM_PROMPT = """\
You are an expert software engineer and code historian.
Given Git commit context, produce a structured JSON explanation with exactly
four fields:
  "summary" - one-sentence description of what changed (max 20 words)
  "rationale" - 2-4 sentence explanation of why the change was likely made
  "confidence" - integer 0-100 reflecting certainty from the available context
  "context_quality" - one of "High", "Medium", or "Low"

Respond ONLY with the raw JSON object. No markdown fences, no preamble.
"""


def _build_prompt(chunk: BlameChunk, file_path: str) -> str:
    c: CommitInfo = chunk.commit
    nearby = ", ".join(c.nearby_commits) if c.nearby_commits else "none"
    diff_section = f"```diff\n{c.diff}\n```" if c.diff else "(diff not available)"

    return f"""File: {file_path}
Lines: {chunk.start_line}-{chunk.end_line}
Commit: {c.short_hash}  ({c.hash})
Author: {c.author} <{c.email}>
Date: {c.date.strftime("%Y-%m-%d")}
Message: {c.message}

Nearby commits touching the same file: {nearby}

Diff:
{diff_section}

Code snippet:
```
{"".join(chunk.lines[:60])}
```

Return the JSON explanation now."""


def _build_timeline_prompt(file_path: str, commits: list[CommitInfo]) -> str:
    entries = "\n".join(
        f"- [{c.short_hash}] {c.date.strftime('%Y-%m-%d')} by {c.author}: {c.message}"
        for c in commits
    )
    return f"""File: {file_path}

Git history (newest first):
{entries}

Summarise the evolution of this file over time.
Return a JSON array where each element has:
  "date" - YYYY-MM string
  "summary" - one short sentence describing what changed that month

Group closely related commits into one entry when they form a logical unit.
Return ONLY the raw JSON array. No markdown fences, no preamble."""


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's text response."""

    def explain(self, chunk: BlameChunk, file_path: str) -> AIExplanation:
        user_prompt = _build_prompt(chunk, file_path)
        raw = self.complete(_SYSTEM_PROMPT, user_prompt)
        return _parse_explanation(raw, chunk.commit)

    def timeline_summaries(
        self, file_path: str, commits: list[CommitInfo]
    ) -> list[dict]:
        user_prompt = _build_timeline_prompt(file_path, commits)
        raw = self.complete(
            "You are a concise technical writer. Return only valid JSON.", user_prompt
        )
        return _parse_timeline(raw)


def _clean_json(raw: str) -> str:
    """Strip markdown fences if the model added them anyway."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _context_quality(commit: CommitInfo | str, diff_size: int | None = None) -> str:
    if isinstance(commit, CommitInfo):
        message = commit.message
        diff_size = len(commit.diff)
        related = len(commit.nearby_commits)
    else:
        message = commit
        related = 0
        diff_size = 0 if diff_size is None else diff_size

    words = [w for w in re.split(r"\W+", message.strip()) if w]
    vague = {"fix", "wip", "update", "changes", "misc", "cleanup", "refactor"}

    score = 0
    if len(words) >= 4 and message.strip().lower() not in vague:
        score += 2
    elif len(words) >= 2:
        score += 1

    if 20 <= diff_size <= 4000:
        score += 2
    elif diff_size > 0:
        score += 1

    if related:
        score += 1

    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


def _parse_explanation(raw: str, commit: CommitInfo | str) -> AIExplanation:
    commit_message = commit.message if isinstance(commit, CommitInfo) else commit
    fallback_quality = _context_quality(commit)
    try:
        data = json.loads(_clean_json(raw))
        confidence = int(data.get("confidence", 50))
        vague = {"fix", "wip", "update", "changes", "misc", "cleanup", "refactor"}
        if commit_message.strip().lower() in vague:
            confidence = min(confidence, 40)
        context_quality = str(data.get("context_quality") or fallback_quality).title()
        if context_quality not in {"High", "Medium", "Low"}:
            context_quality = fallback_quality
        return AIExplanation(
            summary=str(data.get("summary", "")),
            rationale=str(data.get("rationale", "")),
            confidence=max(0, min(100, confidence)),
            context_quality=context_quality,
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return AIExplanation(
            summary="Could not parse AI response.",
            rationale=raw[:500],
            confidence=0,
            context_quality="Low",
        )


def _parse_timeline(raw: str) -> list[dict]:
    try:
        data = json.loads(_clean_json(raw))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, ValueError):
        return []


class AIEngine:
    """Public facade; the rest of the app talks only to this class."""

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        from whycode.ai.claude_provider import ClaudeProvider
        from whycode.ai.ollama_provider import OllamaProvider
        from whycode.ai.openai_provider import OpenAIProvider

        providers: dict[str, type[BaseProvider]] = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "ollama": OllamaProvider,
        }
        config = get_config()
        resolved = (provider or config.default_provider).lower()

        if resolved not in providers:
            raise ValueError(
                f"Unknown provider '{resolved}'. Choose from: {', '.join(providers)}"
            )

        self.provider_name = resolved
        self.prompt_version = PROMPT_VERSION
        self._provider: BaseProvider = providers[resolved](model=model)

    def explain(self, chunk: BlameChunk, file_path: str) -> AIExplanation:
        return self._provider.explain(chunk, file_path)

    def timeline_summaries(
        self, file_path: str, commits: list[CommitInfo]
    ) -> list[dict]:
        return self._provider.timeline_summaries(file_path, commits)
