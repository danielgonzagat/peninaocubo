"""Tests for provider pricing utilities."""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable when package is not installed
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from penin.providers.pricing import estimate_cost, get_pricing, usage_value


def test_get_pricing_known_model():
    pricing = get_pricing("openai", "gpt-4o")
    assert pricing.prompt > 0
    assert pricing.completion > 0


def test_estimate_cost_uses_tokens():
    cost = estimate_cost("openai", "gpt-4o", prompt_tokens=1000, completion_tokens=500)
    # 1000 prompt tokens * 0.005 + 500 completion * 0.015 = 0.0125
    assert cost == pytest.approx(0.0125, rel=1e-6)


def test_usage_value_handles_various_structures():
    class UsageObj:
        prompt_tokens = 123

    assert usage_value({"prompt_tokens": 10}, "prompt_tokens") == 10
    assert usage_value(UsageObj(), "prompt_tokens") == 123
    assert usage_value(None, "prompt_tokens") == 0


def test_unknown_model_has_zero_cost():
    cost = estimate_cost("unknown", "model", 1000, 1000)
    assert cost == 0.0
