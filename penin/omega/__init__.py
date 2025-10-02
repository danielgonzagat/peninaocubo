#!/usr/bin/env python3
"""
PENIN-Ω Core Module
===================

Core implementation of the PENIN-Ω auto-evolution system with CAOS+,
ethics metrics, and comprehensive evaluation modules.
"""

from __future__ import annotations

# CAOS+ metrics - Consolidated to penin.core.caos
# Import from definitive implementation
# Import new dataclasses and engine
from penin.core.caos import (
    CAOSComponents,
    CAOSConfig,
    CAOSPlusEngine,
    CAOSTracker,
    caos_plus,
    compute_caos_plus,
    compute_caos_plus_exponential,
    phi_caos,
)


# Create stub functions for missing quick_ variants
def quick_caos_phi(*args, **kwargs):
    """Quick wrapper for phi_caos (compatibility)"""
    return phi_caos(*args, **kwargs)


def validate_caos_stability(*args, **kwargs):
    """Stability validation (compatibility stub)"""
    # Implement basic stability check
    return True


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
    "CAOSConfig",
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
