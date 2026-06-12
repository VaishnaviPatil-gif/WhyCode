"""Tests for the ExplanationCache."""

from __future__ import annotations


import pytest

from whycode.cache import ExplanationCache
from whycode.models import AIExplanation


@pytest.fixture()
def tmp_cache(tmp_path):
    cache = ExplanationCache(cache_dir=tmp_path)
    yield cache
    cache.close()


def test_miss_returns_none(tmp_cache):
    assert tmp_cache.get("deadbeef") is None


def test_set_and_get(tmp_cache, sample_explanation):
    tmp_cache.set("abc123", sample_explanation)
    result = tmp_cache.get("abc123")
    assert result is not None
    assert result.summary == sample_explanation.summary
    assert result.confidence == sample_explanation.confidence


def test_different_hashes_independent(tmp_cache, sample_explanation):
    exp2 = AIExplanation(summary="other", rationale="other rationale", confidence=10)
    tmp_cache.set("hash1", sample_explanation)
    tmp_cache.set("hash2", exp2)
    assert tmp_cache.get("hash1").summary == sample_explanation.summary
    assert tmp_cache.get("hash2").summary == "other"


def test_provider_and_prompt_version_are_part_of_key(tmp_cache, sample_explanation):
    exp2 = AIExplanation(summary="other", rationale="other rationale", confidence=10)
    tmp_cache.set("hash1", "ollama", "prompt-v1", sample_explanation)
    tmp_cache.set("hash1", "openai", "prompt-v1", exp2)
    ollama_result = tmp_cache.get("hash1", "ollama", "prompt-v1")
    assert ollama_result is not None
    assert ollama_result.summary == sample_explanation.summary
    assert tmp_cache.get("hash1", "openai", "prompt-v1").summary == "other"
    assert tmp_cache.get("hash1", "ollama", "prompt-v2") is None


def test_invalidate_removes_entry(tmp_cache, sample_explanation):
    tmp_cache.set("xyz789", sample_explanation)
    tmp_cache.invalidate("xyz789")
    assert tmp_cache.get("xyz789") is None


def test_clear_wipes_all(tmp_cache, sample_explanation):
    tmp_cache.set("h1", sample_explanation)
    tmp_cache.set("h2", sample_explanation)
    tmp_cache.clear()
    assert tmp_cache.get("h1") is None
    assert tmp_cache.get("h2") is None


def test_len(tmp_cache, sample_explanation):
    assert len(tmp_cache) == 0
    tmp_cache.set("a", sample_explanation)
    tmp_cache.set("b", sample_explanation)
    assert len(tmp_cache) == 2
