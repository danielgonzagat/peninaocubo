"""
PENIN-Ω Router Module
=====================

Production-ready multi-LLM router with cost-aware orchestration,
budget tracking, circuit breakers, and analytics.

Components:
- BudgetTracker: Daily USD budget tracking with soft/hard limits
- CircuitBreaker: Provider-level failure detection and isolation
- MultiLLMRouter: Cost-optimized routing across providers
- Analytics: Performance metrics and cost tracking
"""

from __future__ import annotations

# Import MultiLLMRouterComplete from parent router.py module
from penin.router import MultiLLMRouterComplete

# Import new components
from .budget_tracker import BudgetTracker, ProviderStats, RequestRecord

__all__ = [
    "MultiLLMRouterComplete",
    "BudgetTracker",
    "ProviderStats",
    "RequestRecord",
]
