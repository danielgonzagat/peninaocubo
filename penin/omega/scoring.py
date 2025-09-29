"""
Scoring Module
==============

Implements normalization, EMA, L∞ (harmonic mean with cost penalty),
and the U/S/C/L universal score gate.

All scoring is non-compensatory using harmonic means to prevent
gaming through single metric optimization.
"""

import math
from typing import List, Dict, Tuple, Optional, Union
from enum import Enum
from collections import deque
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    
    # Fallback implementation
    class np_fallback:
        @staticmethod
        def std(values):
            if len(values) < 2:
                return 0.0
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            return math.sqrt(variance)
    
    if not HAS_NUMPY:
        np = np_fallback()


class ScoreVerdict(Enum):
    """Verdict from score gate evaluation"""
    PASS = "pass"
    CANARY = "canary"
    FAIL = "fail"


def normalize_series(values: List[float],
                    method: str = "minmax",
                    target_range: Tuple[float, float] = (0.0, 1.0),
                    epsilon: float = 1e-8) -> List[float]:
    """
    Normalize a series of values.
    
    Args:
        values: Input values to normalize
        method: Normalization method ('minmax', 'zscore', 'sigmoid')
        target_range: Target range for normalization
        epsilon: Small value to prevent division by zero
        
    Returns:
        Normalized values
    """
    if not values:
        return []
    
    values = [float(v) for v in values]
    
    if method == "minmax":
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        
        if range_val < epsilon:
            # All values are the same
            mid = (target_range[0] + target_range[1]) / 2
            return [mid] * len(values)
        
        normalized = [(v - min_val) / range_val for v in values]
        # Scale to target range
        range_target = target_range[1] - target_range[0]
        return [target_range[0] + n * range_target for n in normalized]
    
    elif method == "zscore":
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance + epsilon)
        
        if std_dev < epsilon:
            mid = (target_range[0] + target_range[1]) / 2
            return [mid] * len(values)
        
        # Z-score normalization
        zscores = [(v - mean_val) / std_dev for v in values]
        
        # Map to target range using sigmoid
        sigmoid_vals = [1 / (1 + math.exp(-z)) for z in zscores]
        range_target = target_range[1] - target_range[0]
        return [target_range[0] + s * range_target for s in sigmoid_vals]
    
    elif method == "sigmoid":
        # Direct sigmoid mapping
        sigmoid_vals = [1 / (1 + math.exp(-v)) for v in values]
        range_target = target_range[1] - target_range[0]
        return [target_range[0] + s * range_target for s in sigmoid_vals]
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def ema(values: List[float],
        alpha: float = 0.3,
        init_value: Optional[float] = None) -> List[float]:
    """
    Exponential Moving Average (EMA).
    
    Args:
        values: Input values
        alpha: Smoothing factor (0 < alpha <= 1)
        init_value: Initial value for EMA
        
    Returns:
        EMA values
    """
    if not values:
        return []
    
    if not 0 < alpha <= 1:
        raise ValueError(f"Alpha must be in (0, 1], got {alpha}")
    
    ema_values = []
    current = init_value if init_value is not None else values[0]
    
    for value in values:
        current = alpha * value + (1 - alpha) * current
        ema_values.append(current)
    
    return ema_values


def harmonic_mean(values: List[float],
                  weights: Optional[List[float]] = None,
                  epsilon: float = 1e-8) -> float:
    """
    Compute weighted harmonic mean (non-compensatory).
    
    Args:
        values: Input values
        weights: Optional weights (must sum to 1)
        epsilon: Small value to prevent division by zero
        
    Returns:
        Harmonic mean
    """
    if not values:
        return 0.0
    
    # Handle zeros and negatives
    values = [max(epsilon, v) for v in values]
    
    if weights is None:
        weights = [1.0 / len(values)] * len(values)
    else:
        if len(weights) != len(values):
            raise ValueError("Weights and values must have same length")
        # Normalize weights
        weight_sum = sum(weights)
        if weight_sum < epsilon:
            weights = [1.0 / len(values)] * len(values)
        else:
            weights = [w / weight_sum for w in weights]
    
    # Weighted harmonic mean
    denominator = sum(w / v for w, v in zip(weights, values))
    
    if denominator < epsilon:
        return epsilon
    
    return 1.0 / denominator


def linf_harmonic(metrics: List[float],
                  weights: Optional[List[float]] = None,
                  cost: float = 0.0,
                  lambda_c: float = 0.1,
                  ethical_ok: bool = True,
                  epsilon: float = 1e-8) -> float:
    """
    L∞ score using harmonic mean with cost penalty.
    
    L∞ = H(metrics) * exp(-λ_c * cost) * Σ-Guard
    
    Args:
        metrics: Individual metric values [0,1]
        weights: Metric weights (normalized internally)
        cost: Normalized cost [0,1]
        lambda_c: Cost penalty coefficient
        ethical_ok: Whether Σ-Guard passed
        epsilon: Small value for stability
        
    Returns:
        L∞ score [0,1]
    """
    if not metrics:
        return 0.0
    
    # Fail-closed: if ethics failed, score is 0
    if not ethical_ok:
        return 0.0
    
    # Compute harmonic mean of metrics
    h_score = harmonic_mean(metrics, weights, epsilon)
    
    # Apply cost penalty
    cost_penalty = math.exp(-lambda_c * max(0, cost))
    
    # Final score
    linf = h_score * cost_penalty
    
    # Clamp to [0,1]
    return max(0.0, min(1.0, linf))


def score_gate(U: float,
               S: float, 
               C: float,
               L: float,
               wU: float = 0.3,
               wS: float = 0.2,
               wC: float = 0.3,
               wL: float = 0.2,
               tau: float = 0.7,
               canary_margin: float = 0.1) -> Tuple[ScoreVerdict, float, Dict]:
    """
    Universal U/S/C/L score gate.
    
    Score = wU·U + wS·S - wC·C + wL·L
    
    Note: C (cost) is subtracted as higher cost is worse.
    
    Args:
        U: Utility score [0,1]
        S: Stability score [0,1]
        C: Cost score [0,1] (higher is worse)
        L: Learning/future potential score [0,1]
        wU, wS, wC, wL: Weights (should sum to 1)
        tau: Threshold for passing
        canary_margin: Margin below tau for canary zone
        
    Returns:
        Tuple of (verdict, score, details)
    """
    # Normalize weights
    weight_sum = wU + wS + wC + wL
    if weight_sum > 0:
        wU /= weight_sum
        wS /= weight_sum
        wC /= weight_sum
        wL /= weight_sum
    
    # Clamp inputs to [0,1]
    U = max(0.0, min(1.0, U))
    S = max(0.0, min(1.0, S))
    C = max(0.0, min(1.0, C))
    L = max(0.0, min(1.0, L))
    
    # Compute weighted score
    # Note: C is subtracted (cost penalty)
    score = wU * U + wS * S - wC * C + wL * L
    
    # Determine verdict
    if score >= tau:
        verdict = ScoreVerdict.PASS
    elif score >= (tau - canary_margin):
        verdict = ScoreVerdict.CANARY
    else:
        verdict = ScoreVerdict.FAIL
    
    details = {
        "components": {
            "U": U,
            "S": S,
            "C": C,
            "L": L
        },
        "weights": {
            "wU": wU,
            "wS": wS,
            "wC": wC,
            "wL": wL
        },
        "contributions": {
            "U_contrib": wU * U,
            "S_contrib": wS * S,
            "C_contrib": -wC * C,
            "L_contrib": wL * L
        },
        "threshold": tau,
        "canary_margin": canary_margin,
        "canary_zone": [tau - canary_margin, tau]
    }
    
    return verdict, score, details


def compute_delta_linf(current: float,
                      previous: float,
                      min_delta: float = 0.01) -> Tuple[float, bool]:
    """
    Compute ΔL∞ and check if it meets minimum threshold.
    
    Args:
        current: Current L∞ score
        previous: Previous L∞ score
        min_delta: Minimum required improvement
        
    Returns:
        Tuple of (delta, meets_threshold)
    """
    delta = current - previous
    meets_threshold = delta >= min_delta
    return delta, meets_threshold


def aggregate_scores(scores: List[float],
                    method: str = "harmonic",
                    weights: Optional[List[float]] = None) -> float:
    """
    Aggregate multiple scores using specified method.
    
    Args:
        scores: List of scores to aggregate
        method: Aggregation method ('harmonic', 'geometric', 'arithmetic', 'min')
        weights: Optional weights
        
    Returns:
        Aggregated score
    """
    if not scores:
        return 0.0
    
    # Filter out zeros for some methods
    epsilon = 1e-8
    scores = [max(epsilon, s) for s in scores]
    
    if method == "harmonic":
        return harmonic_mean(scores, weights, epsilon)
    
    elif method == "geometric":
        if weights is None:
            weights = [1.0 / len(scores)] * len(scores)
        else:
            # Normalize weights
            weight_sum = sum(weights)
            weights = [w / weight_sum for w in weights]
        
        # Weighted geometric mean
        product = 1.0
        for score, weight in zip(scores, weights):
            product *= score ** weight
        return product
    
    elif method == "arithmetic":
        if weights is None:
            return sum(scores) / len(scores)
        else:
            weight_sum = sum(weights)
            weights = [w / weight_sum for w in weights]
            return sum(s * w for s, w in zip(scores, weights))
    
    elif method == "min":
        return min(scores)
    
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


class ScoreTracker:
    """Track scores over time with EMA and statistics"""
    
    def __init__(self, window_size: int = 100, ema_alpha: float = 0.3):
        self.window_size = window_size
        self.ema_alpha = ema_alpha
        self.history = deque(maxlen=window_size)
        self.ema_value = None
        
    def add(self, value: float):
        """Add a new score value"""
        self.history.append(value)
        
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = self.ema_alpha * value + (1 - self.ema_alpha) * self.ema_value
    
    def get_ema(self) -> Optional[float]:
        """Get current EMA value"""
        return self.ema_value
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistics of recent scores"""
        if not self.history:
            return {}
        
        values = list(self.history)
        return {
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "std": np.std(values) if len(values) > 1 else 0.0,
            "ema": self.ema_value,
            "count": len(values)
        }
    
    def get_trend(self, lookback: int = 10) -> str:
        """Determine recent trend"""
        if len(self.history) < 2:
            return "insufficient_data"
        
        recent = list(self.history)[-lookback:]
        if len(recent) < 2:
            return "insufficient_data"
        
        # Simple linear regression
        x = list(range(len(recent)))
        y = recent
        
        n = len(x)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator < 1e-8:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"