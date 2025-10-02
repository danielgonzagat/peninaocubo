"""
PENIN-Ω Prometheus Metrics
===========================

Exports key metrics for monitoring:
- Mathematical scores (L∞, CAOS+, SR, coherence)
- Gate status (Sigma Guard)
- Budget and cost
- Request latencies
- Success rates

Usage:
------
    from penin.observability.prometheus_metrics import metrics_registry
    
    # Update metrics
    metrics_registry.record_linf_score(0.85)
    metrics_registry.record_request("openai", latency_ms=150, cost_usd=0.05, success=True)
    
    # Export for Prometheus scraping
    from prometheus_client import generate_latest
    metrics_text = generate_latest(metrics_registry.registry)
"""

from __future__ import annotations

import time
from typing import Any

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        Info,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when Prometheus not installed
    class Counter:
        def __init__(self, *args, **kwargs):
            self.value = 0
        def inc(self, amount=1):
            self.value += amount
        def labels(self, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            self.value = 0.0
        def set(self, value):
            self.value = value
        def labels(self, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            self.values = []
        def observe(self, value):
            self.values.append(value)
        def labels(self, **kwargs):
            return self
    
    class Info:
        def __init__(self, *args, **kwargs):
            self.data = {}
        def info(self, data):
            self.data = data
    
    class CollectorRegistry:
        pass


class PeninMetricsRegistry:
    """
    Central registry for all PENIN-Ω metrics.
    
    Organizes metrics by category for easy monitoring.
    """
    
    def __init__(self, registry: CollectorRegistry | None = None):
        """
        Initialize metrics registry.
        
        Args:
            registry: Custom registry (optional, creates default if None)
        """
        self.registry = registry or CollectorRegistry()
        
        # ====================================================================
        # MATHEMATICAL METRICS
        # ====================================================================
        
        # L∞ Meta-Function
        self.linf_score = Gauge(
            "penin_linf_score",
            "Current L∞ meta-function score [0, 1]",
            registry=self.registry,
        )
        
        # CAOS+ Motor
        self.caos_plus_score = Gauge(
            "penin_caos_plus_score",
            "Current CAOS+ amplification score [1, 100]",
            registry=self.registry,
        )
        
        # SR-Ω∞ Reflexivity
        self.sr_omega_score = Gauge(
            "penin_sr_omega_score",
            "Current SR-Ω∞ reflexivity score [0, 1]",
            registry=self.registry,
        )
        
        # Global Coherence
        self.omega_sea_score = Gauge(
            "penin_omega_sea_score",
            "Global coherence (Ω-ΣEA) score [0, 1]",
            registry=self.registry,
        )
        
        # ΔL∞ Growth
        self.delta_linf = Gauge(
            "penin_delta_linf",
            "ΔL∞ compound growth metric",
            registry=self.registry,
        )
        
        # ====================================================================
        # GATE METRICS
        # ====================================================================
        
        # Sigma Guard decisions
        self.sigma_guard_decisions = Counter(
            "penin_sigma_guard_decisions_total",
            "Total Sigma Guard decisions by action",
            ["action"],  # Labels: promote, rollback, block
            registry=self.registry,
        )
        
        # Individual gates
        self.gate_pass_rate = Gauge(
            "penin_gate_pass_rate",
            "Pass rate for individual gates",
            ["gate_name"],
            registry=self.registry,
        )
        
        # Ethics violations
        self.ethics_violations = Counter(
            "penin_ethics_violations_total",
            "Total ethics violations by law",
            ["law_code"],  # LO-01, LO-02, etc.
            registry=self.registry,
        )
        
        # ====================================================================
        # OPERATIONAL METRICS
        # ====================================================================
        
        # LLM requests
        self.llm_requests = Counter(
            "penin_llm_requests_total",
            "Total LLM requests by provider",
            ["provider", "status"],  # provider: openai, anthropic; status: success, error
            registry=self.registry,
        )
        
        # Request latency
        self.request_latency = Histogram(
            "penin_request_latency_seconds",
            "LLM request latency distribution",
            ["provider"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry,
        )
        
        # Budget usage
        self.budget_used = Gauge(
            "penin_budget_used_usd",
            "Current daily budget usage in USD",
            registry=self.registry,
        )
        
        self.budget_remaining = Gauge(
            "penin_budget_remaining_usd",
            "Remaining daily budget in USD",
            registry=self.registry,
        )
        
        # Cost per request
        self.cost_per_request = Histogram(
            "penin_cost_per_request_usd",
            "Cost per LLM request in USD",
            ["provider"],
            buckets=(0.001, 0.01, 0.05, 0.10, 0.50, 1.0, 5.0),
            registry=self.registry,
        )
        
        # ====================================================================
        # PERFORMANCE METRICS
        # ====================================================================
        
        # Throughput
        self.requests_per_second = Gauge(
            "penin_requests_per_second",
            "Current requests per second",
            registry=self.registry,
        )
        
        # Cache hits
        self.cache_hits = Counter(
            "penin_cache_hits_total",
            "Cache hits by cache level",
            ["level"],  # L1, L2
            registry=self.registry,
        )
        
        # ====================================================================
        # SYSTEM INFO
        # ====================================================================
        
        self.system_info = Info(
            "penin_system",
            "PENIN-Ω system information",
            registry=self.registry,
        )
        
        # Set static info
        self.system_info.info({
            "version": "1.0.0-rc1",
            "equations": "15",
            "laws": "14",
            "gates": "10",
        })
    
    # ========================================================================
    # RECORDING METHODS
    # ========================================================================
    
    def record_linf_score(self, score: float) -> None:
        """Record L∞ score"""
        self.linf_score.set(score)
    
    def record_caos_plus(self, score: float) -> None:
        """Record CAOS+ score"""
        self.caos_plus_score.set(score)
    
    def record_sr_omega(self, score: float) -> None:
        """Record SR-Ω∞ score"""
        self.sr_omega_score.set(score)
    
    def record_coherence(self, score: float) -> None:
        """Record global coherence"""
        self.omega_sea_score.set(score)
    
    def record_delta_linf(self, value: float) -> None:
        """Record ΔL∞"""
        self.delta_linf.set(value)
    
    def record_sigma_guard_decision(self, action: str) -> None:
        """Record Sigma Guard decision"""
        self.sigma_guard_decisions.labels(action=action).inc()
    
    def record_ethics_violation(self, law_code: str) -> None:
        """Record ethics violation"""
        self.ethics_violations.labels(law_code=law_code).inc()
    
    def record_request(
        self,
        provider: str,
        latency_ms: float,
        cost_usd: float,
        success: bool,
    ) -> None:
        """Record LLM request"""
        status = "success" if success else "error"
        self.llm_requests.labels(provider=provider, status=status).inc()
        self.request_latency.labels(provider=provider).observe(latency_ms / 1000.0)  # Convert to seconds
        self.cost_per_request.labels(provider=provider).observe(cost_usd)
    
    def record_budget(self, used_usd: float, remaining_usd: float) -> None:
        """Record budget status"""
        self.budget_used.set(used_usd)
        self.budget_remaining.set(remaining_usd)
    
    def record_cache_hit(self, level: str) -> None:
        """Record cache hit"""
        self.cache_hits.labels(level=level).inc()


# Global singleton instance
metrics_registry = PeninMetricsRegistry()


__all__ = ["PeninMetricsRegistry", "metrics_registry", "PROMETHEUS_AVAILABLE"]
