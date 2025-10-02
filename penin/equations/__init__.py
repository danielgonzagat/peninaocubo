"""
PENIN-Ω Complete Equations Suite
=================================

Implementação completa das 15 equações centrais do PENIN-Ω conforme
especificação técnica para IAAA (Inteligência Artificial Adaptativa
Autoevolutiva Autoconsciente e Auditável).

Módulos:
--------
- penin_equation: Equação de Penin (autoevolução recursiva)
- linf_meta: Meta-função L∞ não-compensatória
- caos_plus: Motor CAOS⁺ (Consistência, Autoevolução, Incognoscível, Silêncio)
- sr_omega_infinity: Singularidade Reflexiva SR-Ω∞
- death_equation: Equação da Morte (seleção darwiniana)
- ir_ic_contractive: IR→IC (Incerteza Restrita → Certa)
- acfa_epv: ACFA EPV (Expected Possession Value)
- agape_index: Índice Agápe (ΣEA/LO-14)
- omega_sea_total: Coerência Global (Ω-ΣEA Total)
- auto_tuning: Auto-Tuning Online (AdaGrad genérico)
- lyapunov_contractive: Contratividade Lyapunov
- oci_closure: OCI (Organizational Closure Index)
- delta_linf_growth: Crescimento composto de ΔL∞
- anabolization: Auto-Evolução de Penin (Anabolização)
- sigma_guard_gate: Gate Σ-Guard (bloqueio fail-closed)

Princípios invioláveis (ΣEA/LO-14):
-----------------------------------
- Sem antropomorfismo ou promessa de consciência/vida
- Fail-closed ético em todos os gates
- WORM ledger para auditoria completa
- Contratividade de risco (IR→IC) obrigatória
- Nenhuma melhoria técnica compensa violação ética
"""

from penin.core.caos import CAOSConfig, compute_caos_plus_complete
from penin.equations.acfa_epv import EPVConfig, expected_possession_value
from penin.equations.agape_index import AgapeConfig, compute_agape_index
from penin.equations.anabolization import AnabolizationConfig, anabolize_penin
from penin.equations.auto_tuning import AutoTuningConfig, auto_tune_hyperparams
from penin.equations.death_equation import DeathConfig, death_gate_check
from penin.equations.delta_linf_growth import (
    DeltaLInfConfig,
    delta_linf_compound_growth,
)
from penin.equations.ir_ic_contractive import ContractivityConfig, ir_to_ic
from penin.equations.lyapunov_contractive import LyapunovConfig, lyapunov_check
from penin.equations.oci_closure import OCIConfig, organizational_closure_index
from penin.equations.omega_sea_total import OmegaSEAConfig, omega_sea_coherence
from penin.equations.penin_equation import PeninState, penin_update
from penin.equations.sigma_guard_gate import SigmaGuardConfig, sigma_guard_check
from penin.math.linf import LInfConfig, compute_linf_meta

# SR-Ω∞ moved to penin/math/sr_omega_infinity.py for better organization
from penin.math.sr_omega_infinity import (
    SRComponents,
    SRConfig,
    compute_sr_score,
)

# Backward compatibility aliases
SRScore = SRComponents  # Type alias for compatibility
compute_sr_omega_infinity = compute_sr_score  # Function alias

__all__ = [
    # Equation 1: Penin Equation
    "penin_update",
    "PeninState",
    # SR-Ω∞
    "SRConfig",
    "SRComponents",
    "compute_sr_score",
    # Equation 2: L∞ Meta-Function
    "compute_linf_meta",
    "LInfConfig",
    # Equation 3: CAOS⁺ Motor
    "compute_caos_plus_complete",
    "CAOSConfig",
    # Equation 4: SR-Ω∞
    "compute_sr_omega_infinity",
    "SRConfig",
    # Equation 5: Death Equation
    "death_gate_check",
    "DeathConfig",
    # Equation 6: IR→IC
    "ir_to_ic",
    "ContractivityConfig",
    # Equation 7: ACFA EPV
    "expected_possession_value",
    "EPVConfig",
    # Equation 8: Agápe Index
    "compute_agape_index",
    "AgapeConfig",
    # Equation 9: Ω-ΣEA Total
    "omega_sea_coherence",
    "OmegaSEAConfig",
    # Equation 10: Auto-Tuning
    "auto_tune_hyperparams",
    "AutoTuningConfig",
    # Equation 11: Lyapunov Contractivity
    "lyapunov_check",
    "LyapunovConfig",
    # Equation 12: OCI
    "organizational_closure_index",
    "OCIConfig",
    # Equation 13: ΔL∞ Growth
    "delta_linf_compound_growth",
    "DeltaLInfConfig",
    # Equation 14: Anabolization
    "anabolize_penin",
    "AnabolizationConfig",
    # Equation 15: Σ-Guard Gate
    "sigma_guard_check",
    "SigmaGuardConfig",
]

__version__ = "1.0.0"
