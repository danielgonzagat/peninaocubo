"""
PENIN-Ω Omega Module — Modular Evolution Engine
================================================

Core auto-evolution components with fail-closed gates, non-compensatory scoring,
and deterministic, auditable evolution cycles.

Modules:
- core: Master equation and projection operators (Π, atualização I_{t+1})
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
    compute_risk_contractivity,
    compute_ecological_impact,
    evaluate_ethics_comprehensive,
    EthicsMetricsResult
)

from .guards import (
    sigma_guard,
    ir_to_ic_contractive,
    combined_guard_check,
    SigmaGuardPolicy,
    GuardResult
)

from .scoring import (
    normalize_series,
    ema,
    harmonic_mean,
    linf_harmonic,
    score_gate,
    compute_delta_linf,
    aggregate_scores,
    ScoreVerdict,
    ScoreTracker
)

from .caos import (
    compute_caos_plus,
    apply_saturation,
    compute_caos_harmony,
    caos_gradient,
    CAOSConfig,
    CAOSTracker
)

from .sr import (
    compute_sr_omega,
    compute_awareness_score,
    compute_autocorrection_score,
    compute_metacognition_score,
    SRConfig,
    SRTracker
)

__all__ = [
    # Ethics metrics
    'compute_ece',
    'compute_bias_ratio', 
    'compute_fairness_metrics',
    'validate_consent',
    'compute_risk_contractivity',
    'compute_ecological_impact',
    'evaluate_ethics_comprehensive',
    'EthicsMetricsResult',
    
    # Guards
    'sigma_guard',
    'ir_to_ic_contractive',
    'combined_guard_check',
    'SigmaGuardPolicy',
    'GuardResult',
    
    # Scoring
    'normalize_series',
    'ema',
    'harmonic_mean',
    'linf_harmonic',
    'score_gate',
    'compute_delta_linf',
    'aggregate_scores',
    'ScoreVerdict',
    'ScoreTracker',
    
    # CAOS
    'compute_caos_plus',
    'apply_saturation',
    'compute_caos_harmony',
    'caos_gradient',
    'CAOSConfig',
    'CAOSTracker',
    
    # SR
    'compute_sr_omega',
    'compute_awareness_score',
    'compute_autocorrection_score',
    'compute_metacognition_score',
    'SRConfig',
    'SRTracker'
]

__version__ = "7.0.0"