"""
PENIN-Ω Core Modules
===================

Módulos fundamentais do sistema de auto-evolução PENIN-Ω:
- scoring: Normalização, EMA, L∞ harmônica e Score U/S/C/L
- caos: φ(CAOS⁺) com log-space e saturação tanh
- sr: SR-Ω∞ não-compensatório (harmônica/min-soft)
- guards: Σ-Guard + IR→IC (fail-closed detalhado)
- ledger: WORM append-only com schema pydantic
- mutators: Param sweeps + prompt variants determinísticos
- evaluators: Suíte de avaliação U/S/C/L com métricas normalizadas
- acfa: Canário + decisão de promoção com ΔL∞ e gates
- tuner: Auto-tuning AdaGrad com clamps por ciclo
- runners: evolve_one_cycle orquestrado e auditável
"""

__version__ = "7.0.0"
__author__ = "Daniel Penin and contributors"