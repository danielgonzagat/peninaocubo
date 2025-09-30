from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict
from enum import Enum

EPS = 1e-9

class ScoreVerdict(Enum):
    """Verdict for score gates"""
    PROMOTE = "promote"
    CANARY = "canary"
    FAIL = "fail"

class ScoreGateVerdict(Enum):
    """Verdict for score gates"""
    PROMOTE = "promote"
    CANARY = "canary"
    FAIL = "fail"


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

def ema_update(prev: float | None, x: float, alpha: float = 0.2) -> float:
    """EMA update function"""
    return ema(prev, x, alpha)


def normalize_minmax(x: float, xmin: float, xmax: float) -> float:
    if xmax <= xmin + EPS:
        return 0.0
    return clamp01((x - xmin) / (xmax - xmin))


def harmonic_mean(values: List[float]) -> float:
    """Simple harmonic mean"""
    if not values:
        return 0.0
    return len(values) / sum(1.0 / max(EPS, v) for v in values)

def quick_harmonic(values: List[float]) -> float:
    """Quick harmonic mean for testing"""
    return harmonic_mean(values)

def harmonic_mean_weighted(values: List[float], weights: List[float]) -> float:
    assert len(values) == len(weights) and len(values) > 0
    denom = 0.0
    weight_sum = sum(weights)
    if weight_sum <= EPS:
        # If all weights are zero, return simple harmonic mean
        return len(values) / sum(1.0 / max(EPS, v) for v in values)
    
    for v, w in zip(values, weights):
        v_clamped = max(EPS, v)
        denom += w / v_clamped
    return 1.0 / max(EPS, denom)


def linf_harmonic(
    metrics: List[float] | dict,
    weights: List[float] | dict,
    cost_norm: float | None = None,
    lambda_c: float = 0.0,
    ethical_ok: bool = True,
    **kwargs,
) -> float:
    # Accept dicts for metrics/weights
    if isinstance(metrics, dict):
        m_vals = [float(metrics[k]) for k in sorted(metrics.keys())]
    else:
        m_vals = metrics
    if isinstance(weights, dict):
        w_vals = [float(weights[k]) for k in sorted(weights.keys())]
    else:
        w_vals = weights

    base = harmonic_mean_weighted(m_vals, w_vals)
    # Back-compat aliases
    if cost_norm is None:
        cost_norm = kwargs.get("cost_factor", 0.0)
    cost_penalty = math.exp(-max(0.0, lambda_c) * clamp01(float(cost_norm))) if cost_norm is not None else 1.0
    gates = 1.0 if ethical_ok else 0.0
    return base * cost_penalty * gates


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
):
    U = clamp01(U)
    S = clamp01(S)
    C = clamp01(C)
    L = clamp01(L)
    weights_sum = wU + wS + wC + wL
    if abs(weights_sum - 1.0) > 1e-6 and weights_sum > 0:
        wU, wS, wC, wL = (wU / weights_sum, wS / weights_sum, wC / weights_sum, wL / weights_sum)
    # Favor higher U, S, L and lower C (cost). Lower cost increases score via (1 - C).
    score = wU * U + wS * S + wL * L + wC * (1.0 - C)
    if score >= tau:
        return type("GateResult", (), {"verdict": "pass", "score": score})()
    if score >= max(0.0, tau - canary_margin):
        return type("GateResult", (), {"verdict": "canary", "score": score})()
    return type("GateResult", (), {"verdict": "fail", "score": score})()

def quick_score_gate(U: float, S: float, C: float, L: float) -> Tuple[ScoreVerdict, float]:
    """Quick score gate for testing"""
    res = score_gate(U, S, C, L, 0.25, 0.25, 0.25, 0.25, 0.7)
    mapping = {"pass": ScoreVerdict.PROMOTE, "canary": ScoreVerdict.CANARY, "fail": ScoreVerdict.FAIL}
    return mapping[res.verdict], res.score

def normalize_series(values: List[float], method: str = 'minmax') -> List[float]:
    """Normalize a series of values"""
    if not values:
        return []
    
    if method == 'minmax':
        min_val = min(values)
        max_val = max(values)
        if max_val <= min_val:
            return [0.5] * len(values)
        return [(v - min_val) / (max_val - min_val) for v in values]
    elif method == 'sigmoid':
        return [1.0 / (1.0 + math.exp(-v)) for v in values]
    else:
        return values

@dataclass
class USCLScorer:
    """U/S/C/L scorer for testing"""
    weights: List[float] = None
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = [0.25, 0.25, 0.25, 0.25]
    
    def score(self, U: float, S: float, C: float, L: float) -> float:
        """Score U/S/C/L metrics"""
        return (self.weights[0] * U + self.weights[1] * S + 
                self.weights[2] * C + self.weights[3] * L)

@dataclass
class LInfinityScorer:
    """L∞ scorer for testing"""
    weights: List[float] = None
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = [0.25, 0.25, 0.25, 0.25]
    
    def score(self, metrics: List[float]) -> float:
        """Score using harmonic mean"""
        return harmonic_mean_weighted(metrics, self.weights)


# Quick utility functions for easy usage
def quick_harmonic(values: List[float], weights: List[float] = None) -> float:
    """Quick harmonic mean calculation"""
    if weights is None:
        weights = [1.0] * len(values)
    return harmonic_mean_weighted(values, weights)


def quick_score_gate(U: float, S: float, C: float, L: float, tau: float = 0.7) -> Tuple[bool, Dict[str, Any]]:
    """Quick score gate with default weights"""
    # Use the existing score_gate function with default weights
    res = score_gate(U, S, C, L, wU=0.25, wS=0.25, wC=0.25, wL=0.25, tau=tau)
    passed = res.verdict == "pass"
    details = {
        'verdict': res.verdict,
        'score': res.score,
        'threshold': tau,
        'passed': passed
    }
    return passed, details

