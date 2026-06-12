"""Tests for data models."""

from whycode.models import ExplainResult, TimelineEntry


def test_ai_explanation_to_dict(sample_explanation):
    d = sample_explanation.to_dict()
    assert d["confidence"] == 82
    assert d["context_quality"] == "High"
    assert "summary" in d
    assert "rationale" in d


def test_explain_result_to_dict(sample_chunk, sample_explanation):
    result = ExplainResult(
        file_path="app.py",
        chunk=sample_chunk,
        explanation=sample_explanation,
    )
    d = result.to_dict()
    assert d["file"] == "app.py"
    assert d["lines"]["start"] == 120
    assert d["lines"]["end"] == 145
    assert d["commit"] == "a7b3f2c"
    assert d["explanation"]["confidence"] == 82
    assert d["explanation"]["context_quality"] == "High"


def test_timeline_entry_to_dict(sample_commit):
    from datetime import datetime, timezone

    entry = TimelineEntry(
        date=datetime(2024, 3, 1, tzinfo=timezone.utc),
        commit=sample_commit,
        summary="Introduced retry logic for external API calls.",
    )
    d = entry.to_dict()
    assert d["date"] == "2024-03"
    assert d["summary"] == "Introduced retry logic for external API calls."
