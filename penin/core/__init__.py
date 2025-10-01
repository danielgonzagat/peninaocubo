"""
PENIN-Ω Core Mathematical Primitives
=====================================

This module contains the fundamental mathematical building blocks
for the IA³ (IA ao cubo) system:

- CAOS+ motor (Consistency, Autoevolution, Incognoscible, Silence)
- L∞ meta-function (non-compensatory global scoring)
- SR-Ω∞ singularity reflexive (metacognition)
- Lyapunov stability enforcement
- Validation gates
"""

from .caos_plus import (
    CAOSPlus,
    CAOSComponent,
    compute_caos_plus,
    compute_caos_plus_exponential,
    phi_caos,
)
from .linf import (
    LInfinity,
    compute_linf,
    harmonic_mean,
)
from .sr_omega import (
    SingularityReflexive,
    compute_sr_score,
    ReflexiveAxis,
)
from .lyapunov import (
    LyapunovStability,
    verify_stability,
    lyapunov_quadratic,
)
from .gates import (
    ValidationGate,
    GateResult,
    sigma_guard_gate,
)

__all__ = [
    # CAOS+
    "CAOSPlus",
    "CAOSComponent",
    "compute_caos_plus",
    "compute_caos_plus_exponential",
    "phi_caos",
    # L∞
    "LInfinity",
    "compute_linf",
    "harmonic_mean",
    # SR-Ω∞
    "SingularityReflexive",
    "compute_sr_score",
    "ReflexiveAxis",
    # Lyapunov
    "LyapunovStability",
    "verify_stability",
    "lyapunov_quadratic",
    # Gates
    "ValidationGate",
    "GateResult",
    "sigma_guard_gate",
]
