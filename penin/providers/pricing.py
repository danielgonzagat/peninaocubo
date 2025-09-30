
from __future__ import annotations
from typing import Dict, Mapping, Any, Union

# USD por 1k tokens (exemplos; ajuste depois)
_PRICING: Dict[str, Dict[str, float]] = {
    "default": {"input": 0.0, "output": 0.0},
    "openai:gpt-4o": {"input": 0.005, "output": 0.015},
    "openai:gpt-4o-mini": {"input": 0.001, "output": 0.003},
    "anthropic:claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "mistral:large": {"input": 0.002, "output": 0.006},
    "google:gemini-1.5-pro": {"input": 0.002, "output": 0.006},
    "deepseek:chat": {"input": 0.0005, "output": 0.0015},
    "xai:grok-2": {"input": 0.003, "output": 0.009},
}

Number = Union[int, float]
Tokens = Union[Number, Mapping[str, Any], list, tuple, None]

def _table_for(pricing_or_none: Mapping[str, Dict[str, float]]|None) -> Mapping[str, Dict[str, float]]:
    return pricing_or_none if pricing_or_none is not None else _PRICING

def get_pricing(pricing_or_model: Union[str, Mapping[str, Dict[str, float]]],
                model: str|None = None) -> Dict[str, float]:
    """
    Compatível com:
      - get_pricing(model)
      - get_pricing(pricing_table, model)
    """
    if model is None:
        table = _PRICING
        model = str(pricing_or_model)
    else:
        table = _table_for(pricing_or_model)  # type: ignore
    return dict(table.get(model, table.get("default", {"input": 0.0, "output": 0.0})))

def usage_value(tokens: Tokens, rate_usd_per_1k: Number) -> float:
    """Suporta int/float, dicts {'input':..,'output':..}, listas/tuplas e None."""
    if tokens is None:
        return 0.0
    if isinstance(tokens, (list, tuple)):
        return sum(usage_value(t, rate_usd_per_1k) for t in tokens)
    if isinstance(tokens, Mapping):
        return sum(usage_value(v, rate_usd_per_1k) for v in tokens.values())
    # numérico
    return (float(tokens) / 1000.0) * float(rate_usd_per_1k)

def estimate_cost(model_or_pricing: Union[str, Mapping[str, Dict[str, float]]],
                  model: str|None = None,
                  prompt_tokens: Tokens = 0,
                  completion_tokens: Tokens = 0) -> float:
    """
    Compatível com:
      - estimate_cost(model, prompt_tokens=..., completion_tokens=...)
      - estimate_cost(pricing_table, model, prompt_tokens=..., completion_tokens=...)
    """
    prices = get_pricing(model_or_pricing, model)
    return usage_value(prompt_tokens, prices["input"]) + usage_value(completion_tokens, prices["output"])
