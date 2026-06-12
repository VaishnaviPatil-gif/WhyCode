"""Shared data models for whycode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CommitInfo:
    """Metadata for a single Git commit."""

    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str
    diff: str = ""
    nearby_commits: list[str] = field(default_factory=list)


@dataclass
class BlameChunk:
    """A contiguous block of lines attributed to one commit."""

    start_line: int
    end_line: int
    commit: CommitInfo
    lines: list[str] = field(default_factory=list)


@dataclass
class AIExplanation:
    """Structured AI response for a commit."""

    summary: str
    rationale: str
    confidence: int  # 0-100
    context_quality: str = "Unknown"

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "context_quality": self.context_quality,
        }


@dataclass
class ExplainResult:
    """Full result for a single blame chunk."""

    file_path: str
    chunk: BlameChunk
    explanation: AIExplanation

    def to_dict(self) -> dict:
        c = self.chunk.commit
        return {
            "file": self.file_path,
            "lines": {"start": self.chunk.start_line, "end": self.chunk.end_line},
            "author": c.author,
            "email": c.email,
            "date": c.date.isoformat(),
            "commit": c.short_hash,
            "message": c.message,
            "explanation": self.explanation.to_dict(),
        }


@dataclass
class TimelineEvent:
    """One entry in the timeline view."""

    date: datetime
    commit: CommitInfo
    summary: str

    def to_dict(self) -> dict:
        return {
            "date": self.date.strftime("%Y-%m"),
            "commit": self.commit.short_hash,
            "author": self.commit.author,
            "summary": self.summary,
        }


TimelineEntry = TimelineEvent
