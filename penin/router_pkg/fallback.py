"""
Fallback Logic for Multi-LLM Router
====================================

Implements automatic fallback to alternative providers when primary fails.

Features:
- Priority-based provider ordering
- Automatic fallback on failure
- Circuit breaker integration
- Cost-aware fallback selection
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FallbackConfig:
    """Configuration for fallback logic"""

    max_fallback_attempts: int = 3  # Maximum fallback attempts
    prefer_cheapest: bool = True  # Prefer cheaper providers in fallback
    respect_circuit_breaker: bool = True  # Skip providers with open circuits


class FallbackStrategy:
    """
    Fallback strategy for provider selection.

    Manages automatic fallback to alternative providers when primary fails.
    """

    def __init__(self, config: FallbackConfig | None = None):
        """
        Initialize fallback strategy.

        Args:
            config: Fallback configuration
        """
        self.config = config or FallbackConfig()

    def get_fallback_sequence(
        self,
        providers: list[str],
        primary_provider: str,
        provider_costs: dict[str, float] | None = None,
        open_circuits: set[str] | None = None,
    ) -> list[str]:
        """
        Get ordered list of fallback providers.

        Args:
            providers: Available providers
            primary_provider: Primary provider that failed
            provider_costs: Cost per provider (for sorting)
            open_circuits: Providers with open circuits (to skip)

        Returns:
            Ordered list of providers to try (excluding primary)
        """
        # Start with all providers except primary
        candidates = [p for p in providers if p != primary_provider]

        # Filter out open circuits if configured
        if self.config.respect_circuit_breaker and open_circuits:
            candidates = [p for p in candidates if p not in open_circuits]

        # Sort by cost if configured and costs available
        if self.config.prefer_cheapest and provider_costs:
            candidates.sort(key=lambda p: provider_costs.get(p, float("inf")))

        # Limit to max attempts
        return candidates[: self.config.max_fallback_attempts]

    def should_fallback(
        self,
        attempt_count: int,
        error_type: type[Exception] | None = None,
    ) -> bool:
        """
        Determine if fallback should be attempted.

        Args:
            attempt_count: Current attempt number
            error_type: Type of error that occurred

        Returns:
            True if fallback should be attempted
        """
        # Check attempt limit
        if attempt_count >= self.config.max_fallback_attempts:
            return False

        # Could add error-type specific logic here
        # e.g., don't fallback on authentication errors
        return True
