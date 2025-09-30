from __future__ import annotations

from typing import Dict, List, Tuple


EPS = 1e-9


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def normalize_minmax(x: float, xmin: float, xmax: float) -> float:
    if xmax <= xmin:
        return 0.0
    return clamp01((x - xmin) / (xmax - xmin))


def ema(prev: float | None, value: float, alpha: float = 0.2) -> float:
    if prev is None:
        return value
    return (1.0 - alpha) * prev + alpha * value


def harmonic_mean_weighted(values: List[float], weights: List[float]) -> float:
    denom = 0.0
    for v, w in zip(values, weights):
        v = max(EPS, v)
        denom += w / v
    if denom <= EPS:
        return 0.0
    return sum(weights) / denom  # Use sum of weights for proper normalization
        denom += w / v
    if denom <= EPS:
        return 0.0
    return 1.0 / denom


def linf_harmonic(metrics: Dict[str, float], weights: Dict[str, float], cost_norm: float, lambda_c: float, ethical_ok: bool) -> float:
    # Enforce gates
    if not ethical_ok:
        return 0.0
    # Compose metrics with cost penalty
    vals: List[float] = []
    wts: List[float] = []
    for k, w in weights.items():
        v = metrics.get(k, 0.0)
        vals.append(clamp01(v))
        wts.append(max(0.0, min(1.0, float(w))))
    base = harmonic_mean_weighted(vals, wts)
    penalty = pow(2.718281828, -lambda_c * clamp01(cost_norm))
    return base * penalty


def score_gate(u: float, s: float, c: float, l: float, w: Dict[str, float], tau: float) -> Tuple[str, float]:
    # Inputs are assumed in [0,1], cost c is higher=worse
    u = clamp01(u)
    s = clamp01(s)
    c = clamp01(c)
    l = clamp01(l)
    wu = float(w.get("U", 0.25))
    ws = float(w.get("S", 0.25))
    wc = float(w.get("C", 0.25))
    wl = float(w.get("L", 0.25))
    score = wu * u + ws * s - wc * c + wl * l
    verdict = "fail"
    if score >= tau:
        verdict = "pass"
    elif score >= max(0.0, tau - 0.05):
        verdict = "canary"
    return verdict, score

