from __future__ import annotations

import math

EPS = 1e-9


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def phi_caos(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = 0.7,
) -> float:
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
def phi_caos(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = 0.7,
) -> float:
    """Calculate the phi_caos metric.
    
    Args:
        C, A, O, S: Input values (will be clamped to [0,1])
        kappa: Scaling factor (will be clamped to [1.0, kappa_max])
        kappa_max: Maximum kappa value
        gamma: Gamma parameter (will be clamped to [0.1, 2.0])
    
    Returns:
        float: The calculated phi_caos value in range [0,1)
    """
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
    kappa = max(1.0, min(kappa_max, kappa))
    base = 1.0 + kappa * C * A
    base = max(base, 1.0 + EPS)
    exp_term = max(0.0, min(1.0, O * S))
    log_caos = exp_term * math.log(base)
    return math.tanh(max(0.1, min(2.0, gamma)) * log_caos)
    log_caos = exp_term * math.log(base)
    return math.tanh(max(0.1, min(2.0, gamma)) * log_caos)

