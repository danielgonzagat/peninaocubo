import math
from typing import Dict


def harmonic_noncomp(metrics: Dict[str, float], weights: Dict[str, float], eps: float = 1e-6) -> float:
    num = 0.0
    den = 0.0
    for k, v in metrics.items():
        w = weights.get(k, 1.0)
        den += w / max(eps, v)
        num += w
    return num / max(eps, den)


def linf_score(metrics: Dict[str, float], weights: Dict[str, float], cost: float, lambda_c: float = 0.01) -> float:
    base = harmonic_noncomp(metrics, weights)
    return base * math.exp(-lambda_c * max(0.0, cost))
