"""
Circuit Breaker for Multi-LLM Router
=====================================

Implements circuit breaker pattern to prevent cascading failures.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit is open, requests are blocked
- HALF_OPEN: Testing if service recovered

Transitions:
- CLOSED → OPEN: After N consecutive failures
- OPEN → HALF_OPEN: After timeout period
- HALF_OPEN → CLOSED: After successful request
- HALF_OPEN → OPEN: After failure in half-open state
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 3  # Failures before opening
    timeout_seconds: float = 60.0  # Time before attempting recovery
    half_open_max_calls: int = 1  # Calls to test in half-open state


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker"""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    opened_at: float | None = None
    half_open_calls: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Prevents cascading failures by blocking requests to failing services
    and allowing periodic recovery attempts.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration (uses defaults if None)
        """
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state (with automatic state transitions)"""
        self._update_state()
        return self.stats.state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self.state == CircuitState.HALF_OPEN

    def can_execute(self) -> bool:
        """
        Check if a request can be executed.

        Returns:
            True if circuit is closed or in half-open state with available test slots
        """
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            return True

        if current_state == CircuitState.OPEN:
            return False

        # Half-open: allow limited test calls
        if current_state == CircuitState.HALF_OPEN:
            return self.stats.half_open_calls < self.config.half_open_max_calls

        return False

    def record_success(self) -> None:
        """
        Record a successful request.

        In HALF_OPEN state, closes the circuit.
        In CLOSED state, resets failure count.
        """
        self.stats.success_count += 1

        if self.stats.state == CircuitState.HALF_OPEN:
            # Success in half-open → close circuit
            self._close_circuit()
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0

    def record_failure(self) -> None:
        """
        Record a failed request.

        In CLOSED state, opens circuit after threshold failures.
        In HALF_OPEN state, reopens circuit immediately.
        """
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()

        if self.stats.state == CircuitState.HALF_OPEN:
            # Failure in half-open → reopen circuit
            self._open_circuit()
        elif self.stats.state == CircuitState.CLOSED:
            # Check if threshold exceeded
            if self.stats.failure_count >= self.config.failure_threshold:
                self._open_circuit()

    def reset(self) -> None:
        """Reset circuit breaker to initial state"""
        self.stats = CircuitBreakerStats()

    def _update_state(self) -> None:
        """Update state based on timeout (OPEN → HALF_OPEN transition)"""
        if self.stats.state == CircuitState.OPEN:
            if self.stats.opened_at is not None:
                time_open = time.time() - self.stats.opened_at
                if time_open >= self.config.timeout_seconds:
                    self._half_open_circuit()

    def _open_circuit(self) -> None:
        """Transition to OPEN state"""
        self.stats.state = CircuitState.OPEN
        self.stats.opened_at = time.time()
        self.stats.half_open_calls = 0

    def _half_open_circuit(self) -> None:
        """Transition to HALF_OPEN state"""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.half_open_calls = 0
        self.stats.failure_count = 0

    def _close_circuit(self) -> None:
        """Transition to CLOSED state"""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0
        self.stats.opened_at = None
        self.stats.half_open_calls = 0

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"CircuitBreaker(state={self.stats.state.value}, "
            f"failures={self.stats.failure_count}, "
            f"successes={self.stats.success_count})"
        )


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers (one per provider).

    Usage:
        manager = CircuitBreakerManager()
        
        if manager.can_execute("openai"):
            try:
                result = call_openai_api()
                manager.record_success("openai")
            except Exception:
                manager.record_failure("openai")
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """
        Initialize circuit breaker manager.

        Args:
            config: Default config for all circuit breakers
        """
        self.config = config or CircuitBreakerConfig()
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(self, provider: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for provider.

        Args:
            provider: Provider name (e.g., "openai")

        Returns:
            Circuit breaker for the provider
        """
        if provider not in self._breakers:
            self._breakers[provider] = CircuitBreaker(self.config)
        return self._breakers[provider]

    def can_execute(self, provider: str) -> bool:
        """
        Check if requests can be sent to provider.

        Args:
            provider: Provider name

        Returns:
            True if circuit is not open
        """
        breaker = self.get_breaker(provider)
        return breaker.can_execute()

    def record_success(self, provider: str) -> None:
        """
        Record successful request to provider.

        Args:
            provider: Provider name
        """
        breaker = self.get_breaker(provider)
        breaker.record_success()

    def record_failure(self, provider: str) -> None:
        """
        Record failed request to provider.

        Args:
            provider: Provider name
        """
        breaker = self.get_breaker(provider)
        breaker.record_failure()

    def reset(self, provider: str | None = None) -> None:
        """
        Reset circuit breaker(s).

        Args:
            provider: Provider to reset (None = reset all)
        """
        if provider is None:
            # Reset all
            for breaker in self._breakers.values():
                breaker.reset()
        else:
            # Reset specific
            if provider in self._breakers:
                self._breakers[provider].reset()

    def get_state(self, provider: str) -> CircuitState:
        """
        Get current state of provider's circuit.

        Args:
            provider: Provider name

        Returns:
            Current circuit state
        """
        breaker = self.get_breaker(provider)
        return breaker.state

    def get_all_states(self) -> dict[str, CircuitState]:
        """
        Get states of all circuits.

        Returns:
            Dict of provider -> state
        """
        return {provider: breaker.state for provider, breaker in self._breakers.items()}

    def export_metrics(self) -> dict[str, Any]:
        """
        Export Prometheus-style metrics.

        Returns:
            Dict of metric_name -> value
        """
        metrics = {}

        for provider, breaker in self._breakers.items():
            prefix = f'penin_circuit_breaker_{{provider="{provider}"}}'

            # State as numeric (0=closed, 1=half_open, 2=open)
            state_value = {
                CircuitState.CLOSED: 0,
                CircuitState.HALF_OPEN: 1,
                CircuitState.OPEN: 2,
            }[breaker.stats.state]

            metrics[f"{prefix}_state"] = state_value
            metrics[f"{prefix}_failures"] = breaker.stats.failure_count
            metrics[f"{prefix}_successes"] = breaker.stats.success_count

        return metrics
