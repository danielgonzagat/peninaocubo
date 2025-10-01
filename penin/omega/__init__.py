#!/usr/bin/env python3
"""
PENIN-Ω Core Module
===================

Core implementation of the PENIN-Ω auto-evolution system with CAOS+,
ethics metrics, and comprehensive evaluation modules.
"""

from __future__ import annotations

# CAOS+ metrics
from .caos import (
    CAOSComponents,
    CAOSPlusEngine,
    CAOSTracker,
    caos_plus,
    compute_caos_plus,
    compute_caos_plus_exponential,
    phi_caos,
    quick_caos_phi,
    validate_caos_stability,
)

# Ethics and safety
from .ethics_metrics import EthicsCalculator, EthicsGate, EthicsMetrics

# Scoring and evaluation
from .scoring import quick_harmonic, quick_score_gate

__all__ = [
    # CAOS
    "phi_caos",
    "compute_caos_plus",
    "compute_caos_plus_exponential",
    "caos_plus",
    "quick_caos_phi",
    "validate_caos_stability",
    "CAOSComponents",
    "CAOSPlusEngine",
    "CAOSTracker",
    # Ethics
    "EthicsCalculator",
    "EthicsGate",
    "EthicsMetrics",
    # Scoring
    "quick_harmonic",
    "quick_score_gate",
]
