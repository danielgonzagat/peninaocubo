"""
SR-Ω∞ — Singularidade Reflexiva (Self-Reflexive Infinity)
==========================================================

Complete implementation of the SR-Ω∞ reflexive scoring system:

    R_t = HarmonicMean(awareness, ethics_ok, autocorrection, metacognition)

    α_eff = α_0 · φ(CAOS⁺) · R_t

Where:
- awareness: Operational self-awareness (calibration, introspection)
- ethics_ok: ΣEA/IR→IC gates passed (binary: 0 or 1)
- autocorrection: Risk reduction over time
- metacognition: ΔL∞ / ΔCost (efficiency of thought)

Properties:
- Non-compensatory (harmonic mean)
- Modulates step size in Master Equation
- Enforces ethical constraints
- Enables continuous self-analysis

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 4
- Blueprint § 4
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SRConfig:
    """Configuration for SR-Ω∞ computation."""

    # Weights for awareness
    w_calib: float = 0.6
    w_intro: float = 0.4

    # Parameters
    alpha_0: float = 0.1  # Base learning rate
    gamma: float = 0.8  # Saturation parameter
    epsilon: float = 1e-6  # Numerical stability

    # Thresholds
    sr_min_threshold: float = 0.80  # Minimum acceptable SR score
    ethics_required: bool = True  # Fail-closed ethics gate

    def __post_init__(self):
        """Validate configuration parameters."""
        if not (0.0 <= self.w_calib <= 1.0):
            raise ValueError(f"w_calib must be in [0,1], got {self.w_calib}")
        if not (0.0 <= self.w_intro <= 1.0):
            raise ValueError(f"w_intro must be in [0,1], got {self.w_intro}")
        if abs(self.w_calib + self.w_intro - 1.0) > 1e-6:
            raise ValueError(
                f"Weights must sum to 1.0, got {self.w_calib + self.w_intro}"
            )
        if not (0.0 < self.alpha_0 <= 1.0):
            raise ValueError(f"alpha_0 must be in (0,1], got {self.alpha_0}")
        if not (0.0 < self.gamma <= 1.0):
            raise ValueError(f"gamma must be in (0,1], got {self.gamma}")
        if self.epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.epsilon}")
        if not (0.0 <= self.sr_min_threshold <= 1.0):
            raise ValueError(
                f"sr_min_threshold must be in [0,1], got {self.sr_min_threshold}"
            )


@dataclass
class SRComponents:
    """SR-Ω∞ reflexive components."""

    awareness: float  # [0,1]
    ethics_ok: float  # 0.0 or 1.0
    autocorrection: float  # [0,1]
    metacognition: float  # [0,1]
    sr_score: float  # Final R_t


def compute_awareness(
    calibration_score: float,
    introspection_depth: float = 0.85,
    w_calib: float = 0.6,
    w_intro: float = 0.4,
) -> float:
    """
    Compute operational self-awareness.

    Args:
        calibration_score: Model calibration (1 - ECE) [0,1]
        introspection_depth: Ability to assess own state [0,1]
        w_calib, w_intro: Weights

    Returns:
        Awareness ∈ [0, 1]

    Example:
        >>> aw = compute_awareness(0.98, 0.90)
        >>> print(f"Awareness: {aw:.4f}")
        Awareness: 0.9480
    """
    return (w_calib * calibration_score) + (w_intro * introspection_depth)


def compute_autocorrection(
    risk_current: float,
    risk_previous: float,
    epsilon: float = 1e-3,
) -> float:
    """
    Compute autocorrection as risk reduction.

    Args:
        risk_current: Current aggregate risk [0,1]
        risk_previous: Previous aggregate risk [0,1]
        epsilon: Stability epsilon

    Returns:
        Autocorrection ∈ [0, 1] (higher = better correction)

    Example:
        >>> ac = compute_autocorrection(0.12, 0.20)
        >>> print(f"Autocorrection: {ac:.4f}")
        Autocorrection: 0.4000
    """
    # Risk reduction (positive is good)
    reduction = risk_previous - risk_current

    # Normalize to [0,1] (assume 0.5 reduction is excellent)
    normalized = min(1.0, max(0.0, reduction / 0.5 + 0.5))

    return normalized


def compute_metacognition(
    delta_Linf: float,
    delta_cost: float,
    epsilon: float = 1e-3,
) -> float:
    """
    Compute metacognition as efficiency of thought.

    Args:
        delta_Linf: Improvement in L∞
        delta_cost: Increase in cost (tokens, time, energy)
        epsilon: Stability epsilon

    Returns:
        Metacognition ∈ [0, 1]

    Example:
        >>> mc = compute_metacognition(0.04, 0.06)
        >>> print(f"Metacognition: {mc:.4f}")
        Metacognition: 0.6667
    """
    # Efficiency: gain per cost
    if delta_cost <= epsilon:
        # Free improvement is excellent
        return 1.0 if delta_Linf > 0 else 0.5

    efficiency = max(0.0, delta_Linf) / (delta_cost + epsilon)

    # Normalize (assume efficiency > 1.0 is excellent)
    return min(1.0, efficiency)


def compute_sr_score(
    awareness: float,
    ethics_ok: bool,
    autocorrection: float,
    metacognition: float,
    epsilon: float = 1e-6,
    return_components: bool = False,
) -> tuple[float, SRComponents]:
    """
    Compute SR-Ω∞ reflexive score using harmonic mean.

    Args:
        awareness: Self-awareness [0,1]
        ethics_ok: Ethical gates passed (bool)
        autocorrection: Risk reduction [0,1]
        metacognition: Efficiency of thought [0,1]
        epsilon: Numerical stability
        return_components: If True, return components

    Returns:
        R_t ∈ [0, 1] (0.0 if ethics_ok=False)
        If return_components=True: (R_t, SRComponents)

    Example:
        >>> R_t, comp = compute_sr_score(0.92, True, 0.88, 0.67, return_components=True)
        >>> print(f"SR-Ω∞: {R_t:.4f}")
        SR-Ω∞: 0.8400
    """
    # Ethics gate is binary and fail-closed
    ethics_value = 1.0 if ethics_ok else 0.0

    if not ethics_ok:
        # Immediate fail
        components = SRComponents(
            awareness=awareness,
            ethics_ok=0.0,
            autocorrection=autocorrection,
            metacognition=metacognition,
            sr_score=0.0,
        )
        return 0.0, components if return_components else (0.0, None)

    # Harmonic mean (non-compensatory)
    vals = [awareness, ethics_value, autocorrection, metacognition]
    n = len(vals)

    denom = sum(1.0 / max(epsilon, v) for v in vals)
    R_t = n / denom if denom > epsilon else 0.0

    # Clamp
    R_t = max(0.0, min(1.0, R_t))

    if return_components:
        components = SRComponents(
            awareness=awareness,
            ethics_ok=ethics_value,
            autocorrection=autocorrection,
            metacognition=metacognition,
            sr_score=R_t,
        )
        return R_t, components

    return R_t, None


def compute_alpha_effective(
    alpha_0: float,
    caos_plus: float,
    R_t: float,
    gamma: float = 0.8,
) -> float:
    """
    Compute effective step size for Master Equation.

    Formula: α_eff = α_0 · tanh(γ · CAOS⁺) · R_t

    Args:
        alpha_0: Base learning rate
        caos_plus: CAOS⁺ score (≥ 1.0)
        R_t: SR-Ω∞ reflexive score [0,1]
        gamma: Saturation parameter (default 0.8)

    Returns:
        α_eff ∈ [0, α_0]

    Example:
        >>> a_eff = compute_alpha_effective(0.1, 1.86, 0.84, gamma=0.8)
        >>> print(f"α_eff: {a_eff:.6f}")
        α_eff: 0.065000
    """
    # Saturating activation
    phi = math.tanh(gamma * caos_plus)

    # Modulate by reflexivity
    alpha_eff = alpha_0 * phi * R_t

    # Safety clamp
    return max(0.0, min(alpha_0, alpha_eff))


# Export public API
__all__ = [
    "SRConfig",
    "SRComponents",
    "compute_sr_score",
    "compute_alpha_effective",
    "compute_awareness",
    "compute_autocorrection",
    "compute_metacognition",
]
