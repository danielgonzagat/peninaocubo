from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Union

Number = Union[int, float]

@dataclass(frozen=True)
class Pricing:
    prompt: float       # USD por 1k tokens de entrada
    completion: float   # USD por 1k tokens de saída

# Tabelas simples por provedor/modelo
_PRICING_BY_PROVIDER: Dict[str, Dict[str, Pricing]] = {
    "openai": {
        "gpt-4o": Pricing(prompt=0.005, completion=0.015),
        "gpt-4o-mini": Pricing(prompt=0.0005, completion=0.0015),
        "default": Pricing(prompt=0.003, completion=0.009),
    },
    "anthropic": {"default": Pricing(0.005, 0.015)},
    "gemini":    {"default": Pricing(0.002, 0.004)},
    "mistral":   {"default": Pricing(0.002, 0.006)},
    "grok":      {"default": Pricing(0.003, 0.010)},
    "deepseek":  {"default": Pricing(0.001, 0.002)},
}

def _table_for(provider_or_table: Union[str, Mapping[str, Pricing]]) -> Mapping[str, Pricing]:
    if isinstance(provider_or_table, Mapping):
        return provider_or_table
    return _PRICING_BY_PROVIDER.get(str(provider_or_table).lower(), {"default": Pricing(0.0, 0.0)})

def get_pricing(pricing_or_model: Union[str, Mapping[str, Pricing]], model: str | None = None) -> Pricing:
    """
    Compatível com:
      - get_pricing(model)
      - get_pricing(provider_or_table, model)
    """
    if model is None:
        # Interpretamos como "model" e vasculhamos as tabelas
        model_name = str(pricing_or_model)
        for table in _PRICING_BY_PROVIDER.values():
            if model_name in table:
                return table[model_name]
        return Pricing(0.0, 0.0)
    table = _table_for(pricing_or_model)
    return table.get(model, table.get("default", Pricing(0.0, 0.0)))

def estimate_cost(provider_or_table: Union[str, Mapping[str, Pricing]],
                  model: str | None = None,
                  prompt_tokens: Number = 0,
                  completion_tokens: Number = 0) -> float:
    p = get_pricing(provider_or_table, model)
    return (float(prompt_tokens) / 1000.0) * p.prompt + (float(completion_tokens) / 1000.0) * p.completion

def get_first_available(usage: Any, *names: str) -> int:
    if usage is None:
        return 0
    for n in names:
        if isinstance(usage, Mapping) and n in usage and isinstance(usage[n], (int, float)):
            return int(usage[n])
        if hasattr(usage, n):
            v = getattr(usage, n)
            if isinstance(v, (int, float)):
                return int(v)
    return 0

def usage_value(usage: Any, *names: str) -> float:
    """
    Extrai contagem de tokens de estruturas variadas:
    - números, dicts/objetos com campos ('prompt_tokens', 'input_tokens', etc.),
    - listas/tuplas (soma recursiva).
    """
    if usage is None:
        return 0.0
    if isinstance(usage, (int, float)):
        return float(usage)
    if isinstance(usage, (list, tuple)):
        return float(sum(usage_value(u, *names) for u in usage))
    if names:
        val = get_first_available(usage, *names)
        if isinstance(val, (int, float)):
            return float(val)
    if isinstance(usage, Mapping):
        total = 0.0
        for v in usage.values():
            total += usage_value(v, *names)
        return float(total)
    for n in ("prompt_tokens", "input_tokens", "completion_tokens", "output_tokens"):
        if hasattr(usage, n):
            v = getattr(usage, n)
            if isinstance(v, (int, float)):
                return float(v)
    return 0.0
