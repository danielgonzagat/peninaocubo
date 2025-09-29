from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

EPS = 1e-9


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def ema(prev: float | None, x: float, alpha: float = 0.2) -> float:
    if prev is None:
        return x
    return (1.0 - alpha) * prev + alpha * x


def normalize_minmax(x: float, xmin: float, xmax: float) -> float:
    if xmax <= xmin + EPS:
        return 0.0
    return clamp01((x - xmin) / (xmax - xmin))


def harmonic_mean_weighted(values: List[float], weights: List[float]) -> float:
    assert len(values) == len(weights) and len(values) > 0
    denom = 0.0
    for v, w in zip(values, weights):
        v_clamped = max(EPS, v)
        denom += w / v_clamped
    return 1.0 / max(EPS, denom)


def linf_harmonic(
    metrics: List[float],
    weights: List[float],
    cost_norm: float,
    lambda_c: float,
    ethical_ok: bool,
) -> float:
    base = harmonic_mean_weighted(metrics, weights)
    cost_penalty = math.exp(-max(0.0, lambda_c) * clamp01(cost_norm))
    gates = 1.0 if ethical_ok else 0.0
    return base * cost_penalty * gates


@dataclass
class ScoreGateVerdict:
    verdict: str
    score: float


def score_gate(
    U: float,
    S: float,
    C: float,
    L: float,
    wU: float,
    wS: float,
    wC: float,
    wL: float,
    tau: float,
    canary_margin: float = 0.05,
) -> ScoreGateVerdict:
    U = clamp01(U)
    S = clamp01(S)
    C = clamp01(C)
    L = clamp01(L)
    weights_sum = wU + wS + wC + wL
    if abs(weights_sum - 1.0) > 1e-6 and weights_sum > 0:
        wU, wS, wC, wL = (wU / weights_sum, wS / weights_sum, wC / weights_sum, wL / weights_sum)
    score = wU * U + wS * S - wC * C + wL * L
    if score >= tau:
        return ScoreGateVerdict("pass", score)
    if score >= max(0.0, tau - canary_margin):
        return ScoreGateVerdict("canary", score)
    return ScoreGateVerdict("fail", score)

