from dataclasses import dataclass
from typing import List, Dict
import math


def harmonic_mean_weighted(values: List[float], weights: List[float], eps: float = 1e-9) -> float:
    wsum = sum(weights) or eps
    den = 0.0
    for v, w in zip(values, weights):
        v = max(eps, float(v))
        den += w / v
    return wsum / max(eps, den)


@dataclass
class GateVerdict:
    verdict: str
    score: float


def score_gate(
    x1: float,
    x2: float,
    cost: float,
    x4: float,
    w1: float,
    w2: float,
    wcost: float,
    w4: float,
    tau: float,
    canary_margin: float = 0.05,
) -> GateVerdict:
    # Reward lower cost via (1 - cost)
    score = (w1 * x1) + (w2 * x2) + (w4 * x4) + (wcost * (1.0 - cost))
    # Treat equality as pass
    if score >= tau - 1e-12:
        return GateVerdict("pass", score)
    if score >= (tau - max(0.0, canary_margin)):
        return GateVerdict("canary", score)
    return GateVerdict("fail", score)


def normalize_series(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax <= vmin:
        return [0.5] * len(values)
    return [(v - vmin) / (vmax - vmin) for v in values]


def linf_harmonic(
    metrics, weights, cost_factor=None, lambda_c: float = 0.0, ethical_ok: bool = True, **kwargs
) -> float:
    """Compatibility linf: accepts list or dict inputs and cost_factor alias."""
    if isinstance(metrics, dict):
        m_vals = [float(metrics[k]) for k in sorted(metrics.keys())]
    else:
        m_vals = [float(x) for x in metrics]
    if isinstance(weights, dict):
        w_vals = [float(weights[k]) for k in sorted(weights.keys())]
    else:
        w_vals = [float(x) for x in weights]
    if not ethical_ok:
        return 0.0
    base = harmonic_mean_weighted(m_vals, w_vals)
    cost = cost_factor if cost_factor is not None else kwargs.get("cost_norm", 0.0)
    return base * math.exp(-max(0.0, float(lambda_c)) * max(0.0, float(cost or 0.0)))
