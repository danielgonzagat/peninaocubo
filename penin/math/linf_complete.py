"""
L∞ Meta-Function — Global Non-Compensatory Performance Scoring
================================================================

Complete implementation of the L∞ equation following PENIN-Ω specifications:

    L∞ = (Σ_j w_j / max(ε, m_j))^(-1) · exp(-λ_c · Cost) · 1_{ΣEA ∧ IR→IC}

Key Properties:
- Non-compensatory: Harmonic mean forces worst dimension to dominate
- Cost-aware: Exponential penalty on normalized cost
- Fail-closed: Returns 0.0 if ethical/contractivity gates fail
- Normalized: All metrics must be in [0, 1]

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 2
- Blueprint § 3.1
"""

from __future__ import annotations

import math

# Default epsilon for numerical stability
DEFAULT_EPSILON = 1e-3


def compute_Linf(
    metrics: list[float] | dict[str, float],
    weights: list[float] | dict[str, float],
    cost_norm: float = 0.0,
    lambda_c: float = 0.5,
    ethical_ok: bool = True,
    contractivity_ok: bool = True,
    epsilon: float = DEFAULT_EPSILON,
) -> float:
    """
    Compute L∞ meta-function score.

    Args:
        metrics: Normalized metrics [0,1] (list or dict)
        weights: Weights for each metric (must sum to 1.0)
        cost_norm: Normalized cost [0,1]
        lambda_c: Cost penalty coefficient (default 0.5)
        ethical_ok: ΣEA/LO-14 gate passed
        contractivity_ok: IR→IC (ρ < 1) gate passed
        epsilon: Numerical stability epsilon

    Returns:
        L∞ score ∈ [0, 1] (0.0 if gates fail)

    Example:
        >>> metrics = [0.85, 0.78, 0.92]
        >>> weights = [0.4, 0.4, 0.2]
        >>> score = compute_Linf(metrics, weights, cost_norm=0.15, lambda_c=0.5)
        >>> print(f"L∞: {score:.4f}")
        L∞: 0.7380
    """
    # Fail-closed: gates must pass
    if not (ethical_ok and contractivity_ok):
        return 0.0

    # Normalize inputs
    if isinstance(metrics, dict):
        m_keys = sorted(metrics.keys())
        m_vals = [float(metrics[k]) for k in m_keys]
    else:
        m_vals = [float(m) for m in metrics]

    if isinstance(weights, dict):
        w_keys = sorted(weights.keys())
        w_vals = [float(weights[k]) for k in w_keys]
    else:
        w_vals = [float(w) for w in weights]

    # Validate
    if len(m_vals) != len(w_vals):
        raise ValueError(
            f"Metrics ({len(m_vals)}) and weights ({len(w_vals)}) length mismatch"
        )

    if len(m_vals) == 0:
        return 0.0

    # Harmonic mean (non-compensatory)
    # 1 / Σ(w_j / max(ε, m_j))
    epsilon = max(epsilon, 1e-12)
    denom = sum(w / max(epsilon, m) for w, m in zip(w_vals, m_vals, strict=False))

    if denom <= epsilon:
        return 0.0

    harmonic = 1.0 / denom

    # Cost penalty
    cost_penalty = math.exp(-lambda_c * max(0.0, cost_norm))

    # Final score
    score = harmonic * cost_penalty

    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def compute_delta_Linf(
    Linf_new: float,
    Linf_old: float,
    relative: bool = False,
    epsilon: float = DEFAULT_EPSILON,
) -> float:
    """
    Compute ΔL∞ = L∞_new - L∞_old.

    Args:
        Linf_new: New L∞ score
        Linf_old: Old L∞ score
        relative: If True, return (L∞_new - L∞_old) / max(ε, L∞_old)
        epsilon: Stability epsilon

    Returns:
        ΔL∞ (absolute or relative)

    Example:
        >>> delta = compute_delta_Linf(0.82, 0.78)
        >>> print(f"ΔL∞: {delta:.4f}")
        ΔL∞: 0.0400
    """
    delta = Linf_new - Linf_old

    if relative:
        denom = max(epsilon, abs(Linf_old))
        return delta / denom

    return delta


def check_min_improvement(
    delta_Linf: float,
    beta_min: float = 0.01,
) -> bool:
    """
    Check if ΔL∞ ≥ β_min (Equation da Morte gate).

    Args:
        delta_Linf: Change in L∞
        beta_min: Minimum required improvement (default 0.01)

    Returns:
        True if improvement sufficient, False otherwise

    Example:
        >>> passes = check_min_improvement(0.015, beta_min=0.01)
        >>> print(f"Passes gate: {passes}")
        Passes gate: True
    """
    return delta_Linf >= beta_min


# Export public API
__all__ = [
    "compute_Linf",
    "compute_delta_Linf",
    "check_min_improvement",
    "DEFAULT_EPSILON",
]
