"""
PENIN-Ω Mathematical Utilities
===============================

Core mathematical functions for AGAPE, L∞, OCI, CAOS⁺, SR-Ω∞, and Master Equation.
"""

from __future__ import annotations

# Agape Index - Consolidated to penin.ethics.agape
from penin.ethics.agape import AgapeIndex, compute_agape_score

# Backward compatibility alias
agape_index = compute_agape_score

# Try to import legacy functions
try:
    from .linf import linf_aggregate, linf_distance
except (ImportError, AttributeError):
    linf_aggregate = None
    linf_distance = None

try:
    from .oci import oci_score
except (ImportError, AttributeError):
    oci_score = None

# New complete implementations
try:
    from .linf_complete import check_min_improvement, compute_delta_Linf, compute_Linf
except ImportError:
    compute_Linf = None
    compute_delta_Linf = None
    check_min_improvement = None

try:
    from .caos_plus_complete import (
        caos_plus_simple,
        compute_A_autoevolution,
        compute_C_consistency,
        compute_caos_plus,
        compute_O_unknowable,
        compute_S_silence,
    )
except ImportError:
    compute_caos_plus = None
    caos_plus_simple = None
    compute_C_consistency = None
    compute_A_autoevolution = None
    compute_O_unknowable = None
    compute_S_silence = None

try:
    from .sr_omega_infinity import (
        compute_alpha_effective,
        compute_autocorrection,
        compute_awareness,
        compute_metacognition,
        compute_sr_score,
    )
except ImportError:
    compute_sr_score = None
    compute_alpha_effective = None
    compute_awareness = None
    compute_autocorrection = None
    compute_metacognition = None

try:
    from .vida_morte_gates import (
        auto_tune_beta_min,
        compute_lyapunov_quadratic,
        death_gate,
        life_gate_lyapunov,
    )
except ImportError:
    death_gate = None
    life_gate_lyapunov = None
    compute_lyapunov_quadratic = None
    auto_tune_beta_min = None

try:
    from .ir_ic_contractivity import (
        RiskProfile,
        apply_Lpsi_operator,
        check_contractivity,
        compute_risk_entropy,
        iterative_refinement,
    )
except ImportError:
    RiskProfile = None
    compute_risk_entropy = None
    apply_Lpsi_operator = None
    check_contractivity = None
    iterative_refinement = None

try:
    from .penin_master_equation import (
        MasterEquationState,
        compute_phi_saturation,
        master_equation_cycle,
        penin_update,
        project_to_safe_set,
    )
except ImportError:
    penin_update = None
    master_equation_cycle = None
    MasterEquationState = None
    project_to_safe_set = None
    compute_phi_saturation = None

__all__ = [
    # Legacy
    "agape_index",
    "linf_aggregate",
    "linf_distance",
    "oci_score",
    # L∞
    "compute_Linf",
    "compute_delta_Linf",
    "check_min_improvement",
    # CAOS⁺
    "compute_caos_plus",
    "caos_plus_simple",
    "compute_C_consistency",
    "compute_A_autoevolution",
    "compute_O_unknowable",
    "compute_S_silence",
    # SR-Ω∞
    "compute_sr_score",
    "compute_alpha_effective",
    "compute_awareness",
    "compute_autocorrection",
    "compute_metacognition",
    # Vida/Morte
    "death_gate",
    "life_gate_lyapunov",
    "compute_lyapunov_quadratic",
    "auto_tune_beta_min",
    # IR→IC
    "RiskProfile",
    "compute_risk_entropy",
    "apply_Lpsi_operator",
    "check_contractivity",
    "iterative_refinement",
    # Master Equation
    "penin_update",
    "master_equation_cycle",
    "MasterEquationState",
    "project_to_safe_set",
    "compute_phi_saturation",
]
