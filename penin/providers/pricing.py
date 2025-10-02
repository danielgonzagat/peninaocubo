"""Pricing helpers for provider cost estimation.

This module centralises model pricing references so that individual
providers can translate token usage metadata into USD cost estimates.
The prices here are intentionally conservative and should be reviewed
periodically against vendor documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "Pricing",
    "PROVIDER_PRICING",
    "get_pricing",
    "estimate_cost",
    "usage_value",
    "calculate_cost",
    "get_first_available",
]


@dataclass(frozen=True)
class Pricing:
    """Represents pricing information per 1K tokens."""

    prompt: float
    completion: float


PROVIDER_PRICING: dict[str, dict[str, Pricing]] = {
    "openai": {
        "gpt-4o": Pricing(prompt=0.005, completion=0.015),
        "gpt-4o-mini": Pricing(prompt=0.0006, completion=0.0024),
        "default": Pricing(prompt=0.005, completion=0.015),
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": Pricing(prompt=0.003, completion=0.015),
        "claude-3-5-sonnet": Pricing(prompt=0.003, completion=0.015),
        "default": Pricing(prompt=0.003, completion=0.015),
    },
    "deepseek": {
        "deepseek-chat": Pricing(prompt=0.00014, completion=0.00028),
        "default": Pricing(prompt=0.00014, completion=0.00028),
    },
    "mistral": {
        "mistral-large-latest": Pricing(prompt=0.008, completion=0.024),
        "default": Pricing(prompt=0.008, completion=0.024),
    },
    "gemini": {
        "gemini-1.5-pro": Pricing(prompt=0.0035, completion=0.0105),
        "default": Pricing(prompt=0.0035, completion=0.0105),
    },
    "grok": {
        "grok-beta": Pricing(prompt=0.01, completion=0.03),
        "default": Pricing(prompt=0.01, completion=0.03),
    },
}


def _normalise_key(value: str | None) -> str:
    return (value or "").lower()


def get_pricing(provider: str, model: str) -> Pricing:
    """Fetch pricing for the given provider/model pair."""

    provider_key = _normalise_key(provider)
    model_key = _normalise_key(model)
    provider_prices = PROVIDER_PRICING.get(provider_key, {})
    if model_key in provider_prices:
        return provider_prices[model_key]
    if "default" in provider_prices:
        return provider_prices["default"]
    return Pricing(prompt=0.0, completion=0.0)


def usage_value(usage: Any, key: str) -> int:
    """Extract integer usage data from SDK-specific structures."""

    if usage is None:
        return 0
    if isinstance(usage, dict):
        value = usage.get(key, 0)
    else:
        value = getattr(usage, key, 0)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def estimate_cost(
    provider: str, model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Estimate USD cost from token counts using provider pricing."""

    pricing = get_pricing(provider, model)
    prompt_cost = (prompt_tokens / 1000.0) * pricing.prompt
    completion_cost = (completion_tokens / 1000.0) * pricing.completion
    total = prompt_cost + completion_cost
    # Guard against negative or NaN inputs
    return max(total, 0.0)


def calculate_cost(
    provider: str, model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Alias for estimate_cost for backwards compatibility."""
    return estimate_cost(provider, model, prompt_tokens, completion_tokens)


def get_first_available(usage: Any, *keys: str) -> int:
    """Extract the first available integer value from usage metadata.

    This function tries multiple key names to handle different SDK response formats.
    """
    if not usage:
        return 0

    # Try dict-like access
    if isinstance(usage, dict):
        for key in keys:
            if key in usage:
                try:
                    return int(usage[key] or 0)
                except (TypeError, ValueError):
                    continue
        return 0

    # Try attribute access
    for key in keys:
        if hasattr(usage, key):
            value = getattr(usage, key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return 0
