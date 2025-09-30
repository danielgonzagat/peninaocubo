from __future__ import annotations
from typing import Dict

# USD por 1k tokens (exemplos; ajuste depois se quiser)
_PRICING: Dict[str, Dict[str, float]] = {
    "default": {"input": 0.0, "output": 0.0},
    "openai:gpt-4o": {"input": 0.005, "output": 0.015},
    "openai:gpt-4o-mini": {"input": 0.001, "output": 0.003},
    "anthropic:claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "mistral:large": {"input": 0.002, "output": 0.006},
}

def get_pricing(model: str) -> Dict[str, float]:
    """Retorna as taxas do modelo ou 'default' se desconhecido."""
    return _PRICING.get(model, _PRICING["default"]).copy()

def usage_value(tokens: int, rate_usd_per_1k: float) -> float:
    """Converte tokens em custo em USD dado preço por 1k tokens."""
    return (tokens / 1000.0) * float(rate_usd_per_1k)

def estimate_cost(model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> float:
    """Custo total = input + output, com base nas taxas do modelo."""
    p = get_pricing(model)
    return usage_value(prompt_tokens, p["input"]) + usage_value(completion_tokens, p["output"])
