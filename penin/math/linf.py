"""
PENIN-Ω L∞ Meta-Function — Non-Compensatory Aggregation
=========================================================

Implements the L∞ meta-function (Equation 2) with:
- Harmonic mean (non-compensatory)
- Cost penalization
- Fail-closed ethics gates

Formula:
    L∞ = (1 / Σ(w_j / max(ε, m_j))) * exp(-λ_c * Cost) * 𝟙_{ΣEA ∧ IR→IC}

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 2
- Blueprint § 3.1
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class LInfConfig:
    """Configuration for L∞ computation."""
    
    lambda_c: float = 0.5  # Cost penalization factor
    epsilon: float = 1e-3  # Numerical stability
    
    # Ethics gates (fail-closed)
    require_ethics: bool = True
    require_contractividade: bool = True


def harmonic_noncomp(
    metrics: dict[str, float],
    weights: dict[str, float],
    eps: float = 1e-6,
) -> float:
    """
    Compute non-compensatory harmonic mean.
    
    Formula:
        H = Σw_j / Σ(w_j / max(ε, m_j))
    
    Args:
        metrics: Normalized metrics ∈ [0, 1]
        weights: Importance weights (non-negative)
        eps: Stability threshold
    
    Returns:
        Harmonic mean ∈ [0, 1]
    """
    num = 0.0
    den = 0.0
    for k, v in metrics.items():
        w = weights.get(k, 1.0)
        den += w / max(eps, v)
        num += w
    return num / max(eps, den)


def linf_score(
    metrics: dict[str, float],
    weights: dict[str, float],
    cost: float,
    lambda_c: float = 0.01,
) -> float:
    """
    Compute L∞ score with cost penalization.
    
    Args:
        metrics: Normalized metrics ∈ [0, 1]
        weights: Importance weights
        cost: Normalized cost ∈ [0, ∞)
        lambda_c: Cost penalty factor
    
    Returns:
        L∞ score ∈ [0, 1]
    """
    base = harmonic_noncomp(metrics, weights)
    return base * math.exp(-lambda_c * max(0.0, cost))


def compute_linf_meta(
    metrics: dict[str, float],
    weights: dict[str, float],
    cost: float,
    config: LInfConfig | None = None,
    ethics_ok: bool = True,
    contratividade_ok: bool = True,
) -> float:
    """
    Compute full L∞ meta-function with fail-closed gates.
    
    Args:
        metrics: Normalized metrics ∈ [0, 1]
        weights: Importance weights (sum to 1.0 preferred)
        cost: Normalized cost
        config: L∞ configuration
        ethics_ok: ΣEA/LO-14 gate status
        contractividade_ok: IR→IC gate status (ρ < 1)
    
    Returns:
        L∞ score ∈ [0, 1], or 0.0 if gates fail
    """
    if config is None:
        config = LInfConfig()
    
    # Fail-closed gates
    if config.require_ethics and not ethics_ok:
        return 0.0
    
    if config.require_contractividade and not contractividade_ok:
        return 0.0
    
    # Compute base harmonic mean
    num = 0.0
    den = 0.0
    for k, v in metrics.items():
        w = weights.get(k, 1.0)
        den += w / max(config.epsilon, v)
        num += w
    
    base = num / max(config.epsilon, den)
    
    # Apply cost penalization
    penalty = math.exp(-config.lambda_c * max(0.0, cost))
    
    return base * penalty
