"""
PENIN-Ω Core — Modular Evolution Engine
========================================

Organização coesa do núcleo matemático:
- core.py: Equação Mestra (Π, atualização I_{t+1})
- scoring.py: L∞, U/S/C/L gate, normalização, EMA
- caos.py: CAOS⁺ com saturações/clamps
- sr.py: SR-Ω∞ agregação não-compensatória
- guards.py: Σ-Guard, IR→IC, ΣEA/LO-14
- acfa.py: Liga/matchmaker (shadow/canary/prod)
- mutators.py: Geradores de variantes
- evaluators.py: Baterias de tarefas/métricas
- tuner.py: Auto-tuning online (AdaGrad/ONS)
- ledger.py: WORM com schema pydantic
- runners.py: Orquestradores evolve/evaluate/promote
- ethics_metrics.py: Cálculo real ECE/ρ_bias/fairness/consent
"""

__version__ = "7.0.0"

from penin.omega.ethics_metrics import (
    calculate_ece,
    calculate_rho_bias,
    calculate_fairness,
    validate_consent,
    EthicsAttestation
)

__all__ = [
    "calculate_ece",
    "calculate_rho_bias", 
    "calculate_fairness",
    "validate_consent",
    "EthicsAttestation"
]