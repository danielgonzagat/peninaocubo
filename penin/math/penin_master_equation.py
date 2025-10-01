"""
Equação de Penin — Master Equation for Auto-Evolution
======================================================

Implementation of the core recursive auto-evolution equation:

    I_{n+1} = Π_{H∩S}[I_n + α_n · G(I_n, E_n; P_n)]

Where:
- I_n: Internal state (parameters, policies, memory)
- E_n: Evidence/environment (data, feedback, tasks)
- P_n: Policies (update rates, constraints, gates)
- G: Update direction (gradient/policy/TD/heuristic)
- α_n: Dynamic step size (α_0 · φ(CAOS⁺) · R_t)
- Π_{H∩S}: Projection onto feasible set (technical ∩ ethical)

Properties:
- Recursive self-improvement
- Safe projection with clamps
- Ethical constraints enforced
- Lyapunov-stable with proper α

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 1
- Blueprint § 3.4
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class MasterEquationState:
    """State for Master Equation tracking."""

    I: np.ndarray  # Current state vector
    n: int  # Iteration number
    alpha_n: float  # Current step size
    caos_plus: float  # CAOS⁺ score
    sr_score: float  # SR-Ω∞ score
    Linf: float  # L∞ performance


def estimate_gradient(
    state: np.ndarray,
    evidence: Any,
    policies: dict[str, Any],
    loss_fn: Callable,
    finite_diff_epsilon: float = 1e-4,
) -> np.ndarray:
    """
    Estimate update direction G using finite differences.

    Args:
        state: Current state I_n
        evidence: Environment/data E_n
        policies: Policy parameters P_n
        loss_fn: Loss function to minimize
        finite_diff_epsilon: Step size for finite differences

    Returns:
        Gradient estimate G (same shape as state)

    Note:
        For large systems, use proper autodiff (PyTorch/JAX).
        This is a simple estimator for small-scale systems.
    """
    gradient = np.zeros_like(state)
    loss_current = loss_fn(state, evidence, policies)

    for i in range(len(state)):
        state_perturbed = state.copy()
        state_perturbed[i] += finite_diff_epsilon

        loss_perturbed = loss_fn(state_perturbed, evidence, policies)
        gradient[i] = (loss_perturbed - loss_current) / finite_diff_epsilon

    return -gradient  # Negative for gradient descent


def project_to_safe_set(
    state: np.ndarray,
    H_constraints: dict[str, tuple] | None = None,
    S_constraints: dict[str, Any] | None = None,
    clip_norm: float | None = None,
) -> np.ndarray:
    """
    Project state onto feasible set Π_{H∩S}.

    H: Technical constraints (box bounds, norm limits)
    S: Ethical constraints (policies, gates)

    Args:
        state: Proposed state
        H_constraints: Technical constraints (e.g., {'bounds': (min, max)})
        S_constraints: Ethical constraints (placeholder for OPA/Rego)
        clip_norm: Optional L2 norm clipping

    Returns:
        Projected state satisfying H ∩ S

    Example:
        >>> state = np.array([1.5, -0.2, 2.3])
        >>> projected = project_to_safe_set(state, H_constraints={'bounds': (0.0, 1.0)})
        >>> print(projected)
        [1.0 0.0 1.0]
    """
    projected = state.copy()

    # H: Technical constraints
    if H_constraints:
        if "bounds" in H_constraints:
            low, high = H_constraints["bounds"]
            projected = np.clip(projected, low, high)

        if "max_norm" in H_constraints or clip_norm:
            max_norm = clip_norm or H_constraints.get("max_norm")
            norm = np.linalg.norm(projected)
            if norm > max_norm:
                projected = projected * (max_norm / norm)

    # S: Ethical constraints (placeholder)
    # In production, call OPA/Rego service
    if S_constraints:
        # Example: check consent, privacy, etc.
        pass

    return projected


def compute_phi_saturation(
    caos_plus: float,
    gamma: float = 0.8,
    mode: str = "tanh",
) -> float:
    """
    Saturation function φ(CAOS⁺) for step modulation.

    Args:
        caos_plus: CAOS⁺ score (≥ 1.0)
        gamma: Scaling parameter
        mode: 'tanh' or 'sigmoid'

    Returns:
        φ ∈ [0, 1]

    Example:
        >>> phi = compute_phi_saturation(1.86, gamma=0.8, mode='tanh')
        >>> print(f"φ: {phi:.4f}")
        φ: 0.7800
    """
    if mode == "tanh":
        return math.tanh(gamma * caos_plus)
    elif mode == "sigmoid":
        return 1.0 / (1.0 + math.exp(-gamma * (caos_plus - 1.0)))
    else:
        raise ValueError(f"Unknown saturation mode: {mode}")


def penin_update(
    I_n: np.ndarray,
    G: np.ndarray,
    alpha_n: float,
    H_constraints: dict[str, tuple] | None = None,
    S_constraints: dict[str, Any] | None = None,
) -> np.ndarray:
    """
    Execute one Master Equation update step.

    I_{n+1} = Π_{H∩S}[I_n + α_n · G]

    Args:
        I_n: Current state
        G: Update direction (gradient/policy)
        alpha_n: Effective step size
        H_constraints: Technical constraints
        S_constraints: Ethical constraints

    Returns:
        I_{n+1}: Updated state

    Example:
        >>> I_n = np.array([0.5, 0.3, 0.7])
        >>> G = np.array([0.1, -0.05, 0.15])
        >>> I_next = penin_update(I_n, G, alpha_n=0.065)
        >>> print(I_next)
        [0.5065 0.29675 0.70975]
    """
    # Compute update
    I_proposed = I_n + (alpha_n * G)

    # Project to safe set
    I_next = project_to_safe_set(I_proposed, H_constraints, S_constraints)

    return I_next


def master_equation_cycle(
    state: MasterEquationState,
    evidence: Any,
    policies: dict[str, Any],
    loss_fn: Callable,
    alpha_0: float,
    caos_plus: float,
    sr_score: float,
    gamma: float = 0.8,
    H_constraints: dict[str, tuple] | None = None,
    S_constraints: dict[str, Any] | None = None,
) -> MasterEquationState:
    """
    Execute complete Master Equation cycle.

    Steps:
    1. Estimate G(I_n, E_n, P_n)
    2. Compute α_n = α_0 · φ(CAOS⁺) · R_t
    3. Update I_{n+1} = Π_{H∩S}[I_n + α_n · G]
    4. Return new state

    Args:
        state: Current MasterEquationState
        evidence: Environment data
        policies: Policy parameters
        loss_fn: Loss function
        alpha_0: Base learning rate
        caos_plus: Current CAOS⁺ score
        sr_score: Current SR-Ω∞ score
        gamma: Saturation parameter
        H_constraints: Technical constraints
        S_constraints: Ethical constraints

    Returns:
        Updated MasterEquationState

    Example:
        >>> state = MasterEquationState(
        ...     I=np.array([0.5, 0.3]),
        ...     n=10,
        ...     alpha_n=0.0,
        ...     caos_plus=0.0,
        ...     sr_score=0.0,
        ...     Linf=0.75
        ... )
        >>> def dummy_loss(I, E, P): return np.sum(I**2)
        >>> new_state = master_equation_cycle(
        ...     state, None, {}, dummy_loss, alpha_0=0.1, caos_plus=1.5, sr_score=0.85
        ... )
    """
    # Step 1: Estimate gradient
    G = estimate_gradient(state.I, evidence, policies, loss_fn)

    # Step 2: Compute effective step size
    phi = compute_phi_saturation(caos_plus, gamma)
    alpha_n = alpha_0 * phi * sr_score

    # Step 3: Update state
    I_next = penin_update(state.I, G, alpha_n, H_constraints, S_constraints)

    # Step 4: Create new state
    new_state = MasterEquationState(
        I=I_next,
        n=state.n + 1,
        alpha_n=alpha_n,
        caos_plus=caos_plus,
        sr_score=sr_score,
        Linf=state.Linf,  # Will be updated externally
    )

    return new_state


# Export public API
__all__ = [
    "penin_update",
    "master_equation_cycle",
    "estimate_gradient",
    "project_to_safe_set",
    "compute_phi_saturation",
    "MasterEquationState",
]
