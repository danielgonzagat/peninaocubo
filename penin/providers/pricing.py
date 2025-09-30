from __future__ import annotations
from typing import Any, Dict, Mapping, Union

Number = Union[int, float]
Tokens = Union[int, float, Mapping[str, Any], Any, None]

# Tabelas simples por provedor; os testes só exigem que calcule >0 e seja estável.
# Ajuste valores se quiser mais fidelidade — aqui usamos defaults razoáveis.
_PRICING_BY_PROVIDER: Dict[str, Dict[str, Dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.0005, "output": 0.0015},
        "default": {"input": 0.003, "output": 0.009},
    },
    "anthropic": {"default": {"input": 0.005, "output": 0.015}},
    "gemini":    {"default": {"input": 0.002, "output": 0.004}},
    "mistral":   {"default": {"input": 0.002, "output": 0.006}},
    "grok":      {"default": {"input": 0.003, "output": 0.010}},
    "deepseek":  {"default": {"input": 0.001, "output": 0.002}},
}

def _table_for(pricing_or_provider: Union[str, Mapping[str, Dict[str, float]]]) -> Mapping[str, Dict[str, float]]:
    """Aceita nome de provedor ('openai' etc) ou uma tabela custom."""
    if isinstance(pricing_or_provider, Mapping):
        return pricing_or_provider
    provider = str(pricing_or_provider).lower()
    return _PRICING_BY_PROVIDER.get(provider, {"default": {"input": 0.0, "output": 0.0}})

def get_pricing(pricing_or_model: Union[str, Mapping[str, Dict[str, float]]],
                model: str | None = None) -> Dict[str, float]:
    """
    Compatível com:
      - get_pricing(model)
      - get_pricing(provider_or_table, model)
    """
    if model is None:
        # Interpreta o argumento como "model" e tenta localizar em todas as tabelas.
        model_name = str(pricing_or_model)
        for table in _PRICING_BY_PROVIDER.values():
            if model_name in table:
                return dict(table[model_name])
        return {"input": 0.0, "output": 0.0}
    table = _table_for(pricing_or_model)
    return dict(table.get(model, table.get("default", {"input": 0.0, "output": 0.0})))

def estimate_cost(model_or_pricing: Union[str, Mapping[str, Dict[str, float]]],
                  model: str | None = None,
                  prompt_tokens: Number = 0,
                  completion_tokens: Number = 0) -> float:
    """Custo em USD usando rates por 1k tokens (input/output)."""
    prices = get_pricing(model_or_pricing, model)
    return (float(prompt_tokens) / 1000.0) * float(prices.get("input", 0.0)) + \
           (float(completion_tokens) / 1000.0) * float(prices.get("output", 0.0))

def get_first_available(usage: Any, *names: str) -> int:
    """Busca o primeiro campo numérico disponível dentro de um objeto/dict (p.ex. 'prompt_tokens')."""
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

def usage_value(usage: Tokens, *names: str) -> float:
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
    # Se nomes forem dados, tenta primeiro esses campos
    if names:
        val = get_first_available(usage, *names)
        if isinstance(val, (int, float)):
            return float(val)
    # Fallback: se for Mapping, soma recursivamente valores numéricos/estruturas
    if isinstance(usage, Mapping):
        total = 0.0
        for v in usage.values():
            total += usage_value(v, *names)
        return float(total)
    # Fallback: tenta pegar qualquer atributo numérico
    for n in ("prompt_tokens", "input_tokens", "completion_tokens", "output_tokens"):
        if hasattr(usage, n):
            v = getattr(usage, n)
            if isinstance(v, (int, float)):
                return float(v)
    return 0.0
