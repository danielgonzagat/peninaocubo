"""
Backwards-compatible wrapper for CAOS+ computation.

The main CAOS+ implementation has been consolidated in :mod:`penin.omega.caos`.
This module maintains compatibility by re-exporting the exponential formula.
"""

from penin.omega.caos import compute_caos_plus_exponential


def compute_caos_plus(C: float, A: float, O: float, S: float, kappa: float = 20.0) -> float:
    """
    CAOS⁺ exponential formula: (1 + κ·C·A)^(O·S)
    
    Monotonic in C, A, O, S; κ shifts the base.
    
    This is a wrapper around the consolidated implementation in penin.omega.caos.
    For the primary CAOS+ implementation with details, use penin.omega.caos.compute_caos_plus().
    """
    return compute_caos_plus_exponential(C, A, O, S, kappa)
