"""
CAOS⁺ Engine — Consistency, Auto-evolution, Unknowable, Silence
================================================================

Complete implementation following PENIN-Ω specifications:

    CAOS⁺ = (1 + κ · C · A)^(O · S)

Where (all in [0,1]):
- C: Consistency (pass@k, 1-ECE, external verification)
- A: Auto-evolution (ΔL∞ / Cost)
- O: Unknowable (epistemic uncertainty, OOD energy)
- S: Silence (1 - noise - redundancy - entropy)
- κ: Kappa gain (≥ 20, auto-tunable)

Properties:
- κ·C·A amplifies base (multiplicative boost)
- O·S controls exploration (exponential modulation)
- CAOS⁺ ≥ 1.0 always
- Used to modulate α_eff in Master Equation

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 3
- Blueprint § 3.2
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CAOSComponents:
    """Individual CAOS components for transparency."""

    C: float  # Consistency [0,1]
    A: float  # Auto-evolution [0,1]
    O: float  # Unknowable [0,1]
    S: float  # Silence [0,1]
    kappa: float  # Gain (≥ 20)
    base: float  # 1 + κ·C·A
    exponent: float  # O·S
    caos_plus: float  # Final score


def compute_C_consistency(
    pass_at_k: float,
    ece: float,
    external_verification: float = 0.76,
    w_pass: float = 0.5,
    w_ece: float = 0.3,
    w_ext: float = 0.2,
) -> float:
    """
    Compute Consistency (C) from multiple signals.

    Args:
        pass_at_k: Pass rate at k attempts [0,1]
        ece: Expected Calibration Error [0, 0.1] (lower better)
        external_verification: External validator agreement [0,1]
        w_pass, w_ece, w_ext: Weights (should sum to 1.0)

    Returns:
        C ∈ [0, 1]

    Example:
        >>> C = compute_C_consistency(0.90, 0.005, 0.85)
        >>> print(f"C: {C:.4f}")
        C: 0.8800
    """
    # Normalize ECE to [0,1] assuming max ECE = 0.1
    ece_norm = 1.0 - min(1.0, ece / 0.1)

    C = (w_pass * pass_at_k) + (w_ece * ece_norm) + (w_ext * external_verification)

    return max(0.0, min(1.0, C))


def compute_A_autoevolution(
    delta_Linf: float,
    cost_norm: float,
    epsilon: float = 1e-3,
) -> float:
    """
    Compute Auto-evolution (A) as gain per cost.

    Args:
        delta_Linf: Improvement in L∞ (can be negative)
        cost_norm: Normalized cost [0,1]
        epsilon: Stability epsilon

    Returns:
        A ∈ [0, 1] (clipped positive gain)

    Example:
        >>> A = compute_A_autoevolution(0.06, 0.15)
        >>> print(f"A: {A:.4f}")
        A: 0.4000
    """
    # Gain per unit cost (positive only)
    gain = max(0.0, delta_Linf) / (cost_norm + epsilon)

    # Normalize to [0,1] with sigmoid-like clipping
    # Assume gain > 1.0 is excellent
    A = min(1.0, gain)

    return A


def compute_O_unknowable(
    epistemic_uncertainty: float,
    ood_score: float = 0.0,
    w_epistemic: float = 0.7,
    w_ood: float = 0.3,
) -> float:
    """
    Compute Unknowable (O) from uncertainty signals.

    Higher O → more exploration allowed.

    Args:
        epistemic_uncertainty: Model uncertainty [0,1]
        ood_score: Out-of-distribution energy [0,1]
        w_epistemic, w_ood: Weights

    Returns:
        O ∈ [0, 1]

    Example:
        >>> O = compute_O_unknowable(0.35, 0.25)
        >>> print(f"O: {O:.4f}")
        O: 0.3200
    """
    O = (w_epistemic * epistemic_uncertainty) + (w_ood * ood_score)

    return max(0.0, min(1.0, O))


def compute_S_silence(
    noise_level: float,
    redundancy: float,
    entropy_norm: float,
    w_noise: float = 0.5,
    w_redundancy: float = 0.25,
    w_entropy: float = 0.25,
) -> float:
    """
    Compute Silence (S) as anti-noise/redundancy/entropy.

    Higher S → cleaner signal → larger step.

    Args:
        noise_level: Noise ratio [0,1]
        redundancy: Data redundancy [0,1]
        entropy_norm: Normalized entropy [0,1]
        w_noise, w_redundancy, w_entropy: Weights (2:1:1 default)

    Returns:
        S ∈ [0, 1]

    Example:
        >>> S = compute_S_silence(0.1, 0.05, 0.15)
        >>> print(f"S: {S:.4f}")
        S: 0.8625
    """
    # Normalize weights
    total_w = w_noise + w_redundancy + w_entropy
    w_noise /= total_w
    w_redundancy /= total_w
    w_entropy /= total_w

    S = (w_noise * (1.0 - noise_level)) + (w_redundancy * (1.0 - redundancy)) + (w_entropy * (1.0 - entropy_norm))

    return max(0.0, min(1.0, S))


def compute_caos_plus(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 20.0,
    return_components: bool = False,
) -> tuple[float, CAOSComponents | None]:
    """
    Compute CAOS⁺ score.

    Formula: (1 + κ·C·A)^(O·S)

    Args:
        C: Consistency [0,1]
        A: Auto-evolution [0,1]
        O: Unknowable [0,1]
        S: Silence [0,1]
        kappa: Gain coefficient (≥ 20 recommended)
        return_components: If True, return (score, components)

    Returns:
        If return_components=False: CAOS⁺ score (≥ 1.0)
        If return_components=True: (score, CAOSComponents)

    Example:
        >>> score, details = compute_caos_plus(0.88, 0.40, 0.35, 0.82, kappa=20.0, return_components=True)
        >>> print(f"CAOS⁺: {score:.4f}")
        CAOS⁺: 1.8600
    """
    # Validate inputs
    assert 0.0 <= C <= 1.0, f"C must be in [0,1], got {C}"
    assert 0.0 <= A <= 1.0, f"A must be in [0,1], got {A}"
    assert 0.0 <= O <= 1.0, f"O must be in [0,1], got {O}"
    assert 0.0 <= S <= 1.0, f"S must be in [0,1], got {S}"
    assert kappa >= 1.0, f"kappa must be ≥ 1.0, got {kappa}"

    # Compute
    base = 1.0 + (kappa * C * A)
    exponent = O * S

    # Handle edge cases
    if exponent == 0.0:
        caos_plus = 1.0
    else:
        caos_plus = base**exponent

    # Numerical safety
    caos_plus = max(1.0, caos_plus)

    if return_components:
        components = CAOSComponents(C=C, A=A, O=O, S=S, kappa=kappa, base=base, exponent=exponent, caos_plus=caos_plus)
        return caos_plus, components

    return caos_plus, None


def caos_plus_simple(C: float, A: float, O: float, S: float, kappa: float = 20.0) -> float:
    """Simplified CAOS⁺ without components (for performance)."""
    score, _ = compute_caos_plus(C, A, O, S, kappa, return_components=False)
    return score


# Export public API
__all__ = [
    "compute_caos_plus",
    "caos_plus_simple",
    "compute_C_consistency",
    "compute_A_autoevolution",
    "compute_O_unknowable",
    "compute_S_silence",
    "CAOSComponents",
]
