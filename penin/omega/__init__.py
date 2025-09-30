"""
PENIN-Ω Core Modules
====================

This package contains the core mathematical and algorithmic components
of the PENIN-Ω self-evolving system.

Modules:
- scoring: L∞ scoring, U/S/C/L gates, normalization and EMA
- caos: CAOS⁺ with log-space computation and saturation
- sr: SR-Ω∞ non-compensatory self-reflection scoring  
- guards: Σ-Guard (ethics/security) and IR→IC (risk contractivity)
- ledger: WORM append-only ledger with file locks
- mutators: Challenger generation (param sweeps, prompt variants)
- evaluators: Task batteries for U/S/C/L measurement
- acfa: League orchestrator (shadow/canary/promote)
- tuner: Online hyperparameter tuning (AdaGrad/ONS)
- runners: Master orchestration loop (evolve_one_cycle)
"""

__version__ = "7.1.0"
__all__ = [
    "scoring",
    "caos",
    "sr",
    "guards",
    "ledger",
    "mutators",
    "evaluators",
    "acfa",
    "tuner",
    "runners",
]