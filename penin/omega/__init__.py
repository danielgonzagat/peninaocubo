#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω Core Module
===================

Core implementation of the PENIN-Ω auto-evolution system.
"""

from .ethics_metrics import EthicsCalculator, EthicsGate, EthicsMetrics

__all__ = [
    'EthicsCalculator',
    'EthicsGate',
    'EthicsMetrics'
]
