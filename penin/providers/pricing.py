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
    "MODEL_PRICING",
    "get_pricing",
    "estimate_cost",
    "usage_value",
    # compatibility aliases
    "ModelPricing",
    "DEFAULT_PRICING",
    "PRICING_TABLE",
    "get_model_pricing",
    "estimate_cost_usd",
    "get_first_available",
]


@dataclass(frozen=True)
class Pricing:
    """Represents pricing information per 1K tokens."""

    prompt: float
    completion: float


MODEL_PRICING: dict[str, dict[str, Pricing]] = {
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
    provider_prices = MODEL_PRICING.get(provider_key, {})
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


def estimate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost from token counts using provider pricing."""

    pricing = get_pricing(provider, model)
    prompt_cost = (prompt_tokens / 1000.0) * pricing.prompt
    completion_cost = (completion_tokens / 1000.0) * pricing.completion
    total = prompt_cost + completion_cost
    # Guard against negative or NaN inputs
    return max(total, 0.0)


# ---------- Compatibility layer (new API used by providers) ----------
from typing import Mapping


class ModelPricing(Pricing):
    @property
    def input_usd_per_token(self) -> float:
        return self.prompt / 1000.0

    @property
    def output_usd_per_token(self) -> float:
        return self.completion / 1000.0


DEFAULT_PRICING = ModelPricing(prompt=0.0, completion=0.0)

PRICING_TABLE: dict[str, dict[str, ModelPricing]] = {
    provider: {model: ModelPricing(p.prompt, p.completion) for model, p in models.items()}
    for provider, models in MODEL_PRICING.items()
}


def get_model_pricing(provider: str, model: str | None) -> ModelPricing:
    provider_key = (provider or "").lower()
    model_key = (model or "").lower()
    table = PRICING_TABLE.get(provider_key)
    if not table:
        return DEFAULT_PRICING
    return table.get(model_key, table.get("default", DEFAULT_PRICING))


def estimate_cost_usd(provider: str, model: str | None, tokens_in: int, tokens_out: int) -> float:
    pr = get_model_pricing(provider, model)
    ti = max(0, int(tokens_in or 0))
    to = max(0, int(tokens_out or 0))
    return ti * pr.input_usd_per_token + to * pr.output_usd_per_token


def get_first_available(usage: Any, *keys: str) -> int:
    if not usage:
        return 0
    if isinstance(usage, Mapping):
        for k in keys:
            v = usage.get(k)
            if v is not None:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    continue
        return 0
    for k in keys:
        if hasattr(usage, k):
            v = getattr(usage, k)
            if v is not None:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    continue
    return 0

