"""Tests for ai_engine module — provider abstraction and prompt building."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from whycode.ai_engine import (
    AIEngine,
    OllamaProvider,
    _parse_explanation,
    _parse_timeline,
)
from whycode.models import AIExplanation


# ── _parse_explanation ────────────────────────────────────────────────────────

class TestParseExplanation:
    def test_valid_json(self):
        raw = json.dumps({
            "summary": "Added retry logic.",
            "rationale": "External APIs fail transiently.",
            "confidence": 80,
        })
        result = _parse_explanation(raw, "Add retry logic")
        assert isinstance(result, AIExplanation)
        assert result.confidence == 80
        assert result.context_quality in {"Low", "Medium", "High"}
        assert result.summary == "Added retry logic."

    def test_markdown_fences_stripped(self):
        raw = "```json\n{\"summary\":\"s\",\"rationale\":\"r\",\"confidence\":70}\n```"
        result = _parse_explanation(raw, "some message")
        assert result.confidence == 70

    def test_vague_commit_lowers_confidence(self):
        raw = json.dumps({"summary": "s", "rationale": "r", "confidence": 90})
        result = _parse_explanation(raw, "fix")
        assert result.confidence <= 40

    def test_invalid_json_returns_zero_confidence(self):
        result = _parse_explanation("not json at all", "fix something")
        assert result.confidence == 0

    def test_confidence_capped_at_100(self):
        raw = json.dumps({"summary": "s", "rationale": "r", "confidence": 999})
        result = _parse_explanation(raw, "Descriptive message")
        assert result.confidence == 100


# ── _parse_timeline ───────────────────────────────────────────────────────────

class TestParseTimeline:
    def test_valid_list(self):
        raw = json.dumps([
            {"date": "2024-01", "summary": "Added auth"},
            {"date": "2024-06", "summary": "Refactored billing"},
        ])
        result = _parse_timeline(raw)
        assert len(result) == 2
        assert result[0]["date"] == "2024-01"

    def test_invalid_json_returns_empty(self):
        assert _parse_timeline("garbage") == []

    def test_non_list_returns_empty(self):
        raw = json.dumps({"date": "2024-01", "summary": "something"})
        assert _parse_timeline(raw) == []


# ── AIEngine factory ──────────────────────────────────────────────────────────

class TestAIEngineFactory:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            AIEngine(provider="unknownxyz")

    def test_ollama_provider_selected(self, monkeypatch):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = {
            "message": {"content": '{"summary":"s","rationale":"r","confidence":50}'}
        }
        monkeypatch.setattr("whycode.ai_engine.OllamaProvider.__init__",
                            lambda self, model=None: None)
        monkeypatch.setattr("whycode.ai_engine.OllamaProvider.complete",
                            lambda self, s, u: '{"summary":"s","rationale":"r","confidence":50}')
        engine = AIEngine(provider="ollama")
        assert isinstance(engine._provider, OllamaProvider)


# ── OllamaProvider ────────────────────────────────────────────────────────────

class TestOllamaProvider:
    def test_explain_calls_complete(self, sample_chunk, monkeypatch):
        good_response = json.dumps({
            "summary": "Test summary",
            "rationale": "Test rationale",
            "confidence": 75,
        })

        provider = OllamaProvider.__new__(OllamaProvider)
        provider._model = "llama3"
        provider._ollama = MagicMock()
        provider._ollama.chat.return_value = {"message": {"content": good_response}}

        result = provider.explain(sample_chunk, "app.py")
        assert result.confidence == 75
        assert result.summary == "Test summary"
