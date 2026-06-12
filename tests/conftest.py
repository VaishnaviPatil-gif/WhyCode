"""Shared pytest fixtures for whycode tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from whycode.models import AIExplanation, BlameChunk, CommitInfo


@pytest.fixture()
def sample_commit() -> CommitInfo:
    return CommitInfo(
        hash="a7b3f2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
        short_hash="a7b3f2c",
        author="Jane Doe",
        email="jane@example.com",
        date=datetime(2024, 3, 15, tzinfo=timezone.utc),
        message="Add retry mechanism for API failures",
        diff="@@ -120,10 +120,30 @@\n+    for attempt in range(max_retries):",
        nearby_commits=["b1c2d3e", "c2d3e4f"],
    )


@pytest.fixture()
def sample_chunk(sample_commit: CommitInfo) -> BlameChunk:
    return BlameChunk(
        start_line=120,
        end_line=145,
        commit=sample_commit,
        lines=[f"    line {i}\n" for i in range(26)],
    )


@pytest.fixture()
def sample_explanation() -> AIExplanation:
    return AIExplanation(
        summary="Added retry logic for resilient API calls.",
        rationale=(
            "External APIs can fail transiently due to network issues. "
            "Retry logic with exponential back-off reduces user-visible errors."
        ),
        confidence=82,
        context_quality="High",
    )
