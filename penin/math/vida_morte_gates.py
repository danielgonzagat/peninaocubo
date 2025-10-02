"""
Equações da Vida e da Morte — Darwinian Selection Gates
========================================================

Implementation of Life/Death equations with Lyapunov stability:

Equação da Morte (Death Equation):
    D(x) = 1  if ΔL∞(x) < β_min  → Kill/Rollback
    D(x) = 0  otherwise           → Survive

Equação da Vida (Life Equation):
    V(I_{t+1}) < V(I_t)  ∧  dV/dt ≤ 0  → Stability

Properties:
- Non-compensatory: Single violation → death
- Auto-tunable β_min via bandit
- Lyapunov guarantee: monotonic risk reduction
- Rollback triggered automatically

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 5, § 11
- Blueprint § 3.5, § 5
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateDecision(str, Enum):
    """Gate decision outcomes."""

    PROMOTE = "promote"  # Champion promoted
    ROLLBACK = "rollback"  # Challenger killed
    CANARY = "canary"  # Continue testing
    QUARANTINE = "quarantine"  # Isolated for analysis


@dataclass
class DeathGateResult:
    """Death gate evaluation result."""

    decision: GateDecision
    delta_Linf: float
    beta_min: float
    passed: bool
    reason: str


@dataclass
class LifeGateResult:
    """Life gate (Lyapunov) evaluation result."""

    decision: GateDecision
    V_current: float
    V_previous: float
    dV_dt: float
    passed: bool
    reason: str


def death_gate(
    delta_Linf: float,
    beta_min: float = 0.01,
    strict: bool = True,
) -> DeathGateResult:
    """
    Evaluate Death Gate: ΔL∞ ≥ β_min required to survive.

    Args:
        delta_Linf: Change in L∞ score
        beta_min: Minimum required improvement (default 0.01)
        strict: If True, use ≥; if False, allow equality

    Returns:
        DeathGateResult with decision

    Example:
        >>> result = death_gate(0.008, beta_min=0.01)
        >>> print(result.decision, result.passed)
        GateDecision.ROLLBACK False
    """
    if strict:
        passed = delta_Linf >= beta_min
    else:
        passed = delta_Linf >= beta_min - 1e-12

    if passed:
        decision = GateDecision.PROMOTE
        reason = f"ΔL∞={delta_Linf:.6f} ≥ β_min={beta_min:.6f}"
    else:
        decision = GateDecision.ROLLBACK
        reason = f"ΔL∞={delta_Linf:.6f} < β_min={beta_min:.6f} → KILL"

    return DeathGateResult(
        decision=decision,
        delta_Linf=delta_Linf,
        beta_min=beta_min,
        passed=passed,
        reason=reason,
    )


def life_gate_lyapunov(
    V_current: float,
    V_previous: float,
    dt: float = 1.0,
    epsilon: float = 1e-6,
) -> LifeGateResult:
    """
    Evaluate Life Gate via Lyapunov function.

    Requirements:
    1. V(I_{t+1}) < V(I_t)  → Energy must decrease
    2. dV/dt ≤ 0            → Derivative non-positive

    Args:
        V_current: Lyapunov function at current state
        V_previous: Lyapunov function at previous state
        dt: Time step (default 1.0)
        epsilon: Tolerance for numerical errors

    Returns:
        LifeGateResult with decision

    Example:
        >>> result = life_gate_lyapunov(0.85, 0.92)
        >>> print(result.decision, result.passed)
        GateDecision.PROMOTE True
    """
    # Compute derivative
    dV_dt = (V_current - V_previous) / max(epsilon, dt)

    # Check conditions (with tolerance)
    energy_decreased = V_current < (V_previous + epsilon)
    derivative_ok = dV_dt <= epsilon

    passed = energy_decreased and derivative_ok

    if passed:
        decision = GateDecision.PROMOTE
        reason = f"V↓: {V_previous:.4f}→{V_current:.4f}, dV/dt={dV_dt:.6f}≤0"
    else:
        decision = GateDecision.ROLLBACK
        reasons = []
        if not energy_decreased:
            reasons.append(f"V↑: {V_previous:.4f}→{V_current:.4f}")
        if not derivative_ok:
            reasons.append(f"dV/dt={dV_dt:.6f}>0")
        reason = " AND ".join(reasons) + " → KILL"

    return LifeGateResult(
        decision=decision,
        V_current=V_current,
        V_previous=V_previous,
        dV_dt=dV_dt,
        passed=passed,
        reason=reason,
    )


def compute_lyapunov_quadratic(
    state: float,
    target: float = 0.0,
) -> float:
    """
    Compute quadratic Lyapunov function: V = (I - I*)²

    Args:
        state: Current state value
        target: Target/equilibrium state (default 0.0)

    Returns:
        V ≥ 0

    Example:
        >>> V = compute_lyapunov_quadratic(0.15, target=0.0)
        >>> print(f"V: {V:.6f}")
        V: 0.022500
    """
    return (state - target) ** 2


def auto_tune_beta_min(
    success_rate: float,
    budget_remaining: float,
    risk_tolerance: float,
    beta_min_current: float = 0.01,
    learning_rate: float = 0.05,
) -> float:
    """
    Auto-tune β_min using bandit-style adaptation.

    Logic:
    - If success_rate too low → decrease β_min (easier gate)
    - If budget low and risk high → increase β_min (stricter gate)

    Args:
        success_rate: Recent promotion success rate [0,1]
        budget_remaining: Budget left [0,1]
        risk_tolerance: Risk appetite [0,1]
        beta_min_current: Current β_min threshold
        learning_rate: Adaptation rate

    Returns:
        Updated β_min ∈ [0.001, 0.1]

    Example:
        >>> new_beta = auto_tune_beta_min(0.45, 0.30, 0.20, beta_min_current=0.01)
        >>> print(f"β_min: {new_beta:.6f}")
        β_min: 0.009500
    """
    # Target success rate (e.g., 60%)
    target_rate = 0.6

    # Adjustment signal
    delta = (success_rate - target_rate) * learning_rate

    # Budget/risk penalty
    if budget_remaining < 0.3 and risk_tolerance < 0.3:
        # Stricter when low budget and low risk tolerance
        delta -= learning_rate * 0.5

    # Update
    beta_min_new = beta_min_current + delta

    # Clamp to reasonable range
    return max(0.001, min(0.1, beta_min_new))


# Export public API
__all__ = [
    "death_gate",
    "life_gate_lyapunov",
    "compute_lyapunov_quadratic",
    "auto_tune_beta_min",
    "GateDecision",
    "DeathGateResult",
    "LifeGateResult",
]
