"""
PENIN-Ω Omega Module
====================

Core auto-evolution components with fail-closed gates, non-compensatory scoring,
and deterministic, auditable evolution cycles.

Modules:
- core: Master equation and projection operators
- scoring: L∞, U/S/C/L score gates, normalization, EMA
- caos: CAOS⁺ stable computation with log-space and saturation
- sr: SR-Ω∞ reflexive score with non-compensatory aggregation
- guards: Σ-Guard ethics/safety gates and IR→IC contractivity
- acfa: Champion/challenger matchmaking with canary/shadow traffic
- mutators: Parameter sweeps and prompt variant generation
- evaluators: Task batteries for U/S/C/L metric collection
- tuner: AdaGrad/ONS auto-tuning for hyperparameters
- ledger: WORM append-only ledger with Pydantic schema
- runners: Orchestration of evolution cycles
- ethics_metrics: ECE, bias, fairness, and consent computation
"""

from .ethics_metrics import (
    compute_ece,
    compute_bias_ratio,
    compute_fairness_metrics,
    validate_consent,
    EthicsMetricsResult
)

from .guards import (
    sigma_guard,
    ir_to_ic_contractive,
    GuardResult
)

from .scoring import (
    normalize_series,
    ema,
    linf_harmonic,
    score_gate,
    ScoreVerdict
)

__all__ = [
    'compute_ece',
    'compute_bias_ratio', 
    'compute_fairness_metrics',
    'validate_consent',
    'EthicsMetricsResult',
    'sigma_guard',
    'ir_to_ic_contractive',
    'GuardResult',
    'normalize_series',
    'ema',
    'linf_harmonic',
    'score_gate',
    'ScoreVerdict'
]

__version__ = "1.0.0"