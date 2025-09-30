"""Pricing utilities for estimating LLM usage costs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ModelPricing:
    """Per-token pricing for a specific provider/model combination."""

    input_usd_per_token: float
    output_usd_per_token: float


DEFAULT_PRICING = ModelPricing(input_usd_per_token=0.0, output_usd_per_token=0.0)

# Pricing values are based on publicly available rate cards as of Q1 2025.
# They intentionally err on the conservative (higher) side to avoid
# under-reporting spend if providers update prices in the future.
PRICING_TABLE: dict[str, dict[str, ModelPricing]] = {
    "openai": {
        # gpt-4o (Apr 2024): $5 input / $15 output per 1M tokens
        "gpt-4o": ModelPricing(0.000005, 0.000015),
        "default": ModelPricing(0.000005, 0.000015),
    },
    "deepseek": {
        # DeepSeek V3 Chat pricing (approx.): $0.14 input / $0.28 output per 1M tokens
        "deepseek-chat": ModelPricing(0.00000014, 0.00000028),
        "default": ModelPricing(0.00000014, 0.00000028),
    },
    "anthropic": {
        # Claude 3.5 Sonnet: $3 input / $15 output per 1M tokens
        "claude-3-5-sonnet-20241022": ModelPricing(0.000003, 0.000015),
        "default": ModelPricing(0.000003, 0.000015),
    },
    "gemini": {
        # Gemini 1.5 Pro: $3.50 input / $10.50 output per 1M tokens
        "gemini-1.5-pro": ModelPricing(0.0000035, 0.0000105),
        "default": ModelPricing(0.0000035, 0.0000105),
    },
    "mistral": {
        # Mistral Large: $4 input / $12 output per 1M tokens
        "mistral-large-latest": ModelPricing(0.000004, 0.000012),
        "default": ModelPricing(0.000004, 0.000012),
    },
    "grok": {
        # Grok Beta (xAI): assume $5 input / $15 output per 1M tokens
        "grok-beta": ModelPricing(0.000005, 0.000015),
        "default": ModelPricing(0.000005, 0.000015),
    },
}


def _normalize_model(model: str | None) -> str | None:
    if not model:
        return None
    return model.lower()


def get_model_pricing(provider: str, model: str | None) -> ModelPricing:
    """Return pricing information for the given provider/model."""

    provider_key = provider.lower()
    provider_pricing = PRICING_TABLE.get(provider_key)
    if not provider_pricing:
        return DEFAULT_PRICING

    model_key = _normalize_model(model)
    if model_key and model_key in provider_pricing:
        return provider_pricing[model_key]

    return provider_pricing.get("default", DEFAULT_PRICING)


def estimate_cost_usd(provider: str, model: str | None, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost using the configured pricing table."""

    pricing = get_model_pricing(provider, model)
    tokens_in = max(0, int(tokens_in or 0))
    tokens_out = max(0, int(tokens_out or 0))
    return (tokens_in * pricing.input_usd_per_token) + (tokens_out * pricing.output_usd_per_token)


def _get_mapping_value(mapping: Mapping[str, Any], key: str) -> Any | None:
    value = mapping.get(key)
    if value is None:
        camel = key.replace("_", "")
        for candidate in mapping:
            if candidate.lower() == key.lower() or candidate.lower() == camel.lower():
                return mapping[candidate]
    return value


def get_first_available(usage: Any, *keys: str) -> int:
    """Extract the first available integer value from usage metadata."""

    if not usage:
        return 0

    if isinstance(usage, Mapping):
        for key in keys:
            value = _get_mapping_value(usage, key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
        return 0

    for key in keys:
        if hasattr(usage, key):
            value = getattr(usage, key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return 0
