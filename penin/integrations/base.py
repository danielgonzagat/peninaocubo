"""
Base classes and interfaces for PENIN-Ω SOTA integrations.

All external technology adapters should inherit from these base classes
to ensure consistent interface, error handling, and auditability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntegrationStatus(Enum):
    """Status of SOTA integration"""

    NOT_INSTALLED = "not_installed"  # Package not available
    INSTALLED = "installed"  # Package installed but not initialized
    INITIALIZED = "initialized"  # Initialized and ready
    ACTIVE = "active"  # Currently in use
    FAILED = "failed"  # Initialization or runtime failure
    DISABLED = "disabled"  # Manually disabled


class IntegrationPriority(Enum):
    """Priority level for SOTA integration"""

    P1_CRITICAL = 1  # Neuromorphic Metacognitive Agents
    P2_HIGH = 2  # Self-Modifying Evolution
    P3_MEDIUM = 3  # Conscious Collectives
    P4_LOW = 4  # Experimental


@dataclass
class IntegrationMetrics:
    """Metrics tracked for each SOTA integration"""

    invocations: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    avg_quality_score: float = 0.0
    samples_processed: int = 0

    @property
    def success_rate(self) -> float:
        """Success rate [0, 1]"""
        if self.invocations == 0:
            return 0.0
        return self.successes / self.invocations

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds"""
        if self.invocations == 0:
            return 0.0
        return self.total_latency_ms / self.invocations

    @property
    def cost_per_sample(self) -> float:
        """Cost per processed sample in USD"""
        if self.samples_processed == 0:
            return 0.0
        return self.total_cost_usd / self.samples_processed


class IntegrationConfig(BaseModel):
    """Base configuration for all SOTA integrations"""

    enabled: bool = Field(default=True, description="Enable this integration")
    priority: IntegrationPriority = Field(
        default=IntegrationPriority.P4_LOW, description="Priority level"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Max retry attempts on failure"
    )
    timeout_seconds: float = Field(default=30.0, gt=0, description="Operation timeout")
    fail_open: bool = Field(
        default=False, description="Fail-open (True) or fail-closed (False)"
    )
    audit_trail: bool = Field(
        default=True, description="Log all operations to WORM ledger"
    )
    dry_run: bool = Field(
        default=False, description="Dry-run mode (no actual execution)"
    )

    class Config:
        """Pydantic config"""

        extra = "allow"  # Allow technology-specific fields


class BaseIntegrationAdapter(ABC):
    """
    Abstract base class for all SOTA integration adapters.

    All adapters must implement:
    - initialize(): Setup and validate installation
    - is_available(): Check if technology is installed
    - get_status(): Current status
    - execute(): Main execution method (technology-specific)
    """

    def __init__(self, config: IntegrationConfig | None = None):
        self.config = config or IntegrationConfig()
        self.status = IntegrationStatus.NOT_INSTALLED
        self.metrics = IntegrationMetrics()
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the integration.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the required package is installed and available.

        Returns:
            True if package is available, False otherwise
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Get current status and health metrics.

        Returns:
            Dictionary with status information
        """
        pass

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the main functionality of this integration.

        Technology-specific implementation.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result (technology-specific)

        Raises:
            IntegrationError: On failure
        """
        pass

    def record_invocation(
        self, success: bool, latency_ms: float, cost_usd: float = 0.0
    ):
        """Record metrics for an invocation"""
        self.metrics.invocations += 1
        if success:
            self.metrics.successes += 1
        else:
            self.metrics.failures += 1
        self.metrics.total_latency_ms += latency_ms
        self.metrics.total_cost_usd += cost_usd

    def get_metrics(self) -> dict[str, Any]:
        """Get integration metrics"""
        return {
            "invocations": self.metrics.invocations,
            "successes": self.metrics.successes,
            "failures": self.metrics.failures,
            "success_rate": self.metrics.success_rate,
            "avg_latency_ms": self.metrics.avg_latency_ms,
            "total_cost_usd": self.metrics.total_cost_usd,
            "cost_per_sample": self.metrics.cost_per_sample,
            "avg_quality_score": self.metrics.avg_quality_score,
        }


class IntegrationError(Exception):
    """Base exception for integration errors"""

    def __init__(
        self, adapter_name: str, message: str, original_error: Exception | None = None
    ):
        self.adapter_name = adapter_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{adapter_name}] {message}")


class IntegrationNotAvailableError(IntegrationError):
    """Raised when required package is not installed"""

    pass


class IntegrationInitializationError(IntegrationError):
    """Raised when initialization fails"""

    pass


class IntegrationExecutionError(IntegrationError):
    """Raised when execution fails"""

    pass


# Type aliases for convenience
IntegrationResult = dict[str, Any]
IntegrationMetadata = dict[str, Any]


__all__ = [
    "BaseIntegrationAdapter",
    "IntegrationConfig",
    "IntegrationStatus",
    "IntegrationPriority",
    "IntegrationMetrics",
    "IntegrationError",
    "IntegrationNotAvailableError",
    "IntegrationInitializationError",
    "IntegrationExecutionError",
    "IntegrationResult",
    "IntegrationMetadata",
]
