#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω Observability Module
=============================

Provides structured logging and Prometheus metrics export for the PENIN-Ω system.

Features:
- JSON structured logging with trace IDs
- Prometheus metrics collection and export
- Performance tracking and alerting
- Gate failure tracking
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import uuid

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary,
        generate_latest, CONTENT_TYPE_LATEST,
        CollectorRegistry
    )
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    # Create dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def inc(self, amount=1): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, value): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, value): pass
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, value): pass
    class CollectorRegistry:
        def __init__(self): pass
    def generate_latest(registry): return b""
    CONTENT_TYPE_LATEST = "text/plain"
    print("WARNING: prometheus_client not installed. Metrics export disabled.")

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False
    print("INFO: structlog not installed. Using standard JSON logging.")

# -----------------------------------------------------------------------------
# Structured Logger
# -----------------------------------------------------------------------------
class StructuredLogger:
    """JSON structured logger with trace ID support"""
    
    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.name = name
        self.trace_id = None
        self.log_file = log_file
        
        if HAS_STRUCTLOG:
            # Configure structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    self._add_trace_id,
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            self.logger = structlog.get_logger(name)
        else:
            # Fallback to standard logging with JSON formatter
            self.logger = logging.getLogger(name)
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(JSONFormatter())
                self.logger.addHandler(file_handler)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _add_trace_id(self, logger, method_name, event_dict):
        """Add trace ID to log events"""
        if self.trace_id:
            event_dict['trace_id'] = self.trace_id
        return event_dict
    
    @contextmanager
    def trace(self, trace_id: Optional[str] = None):
        """Context manager for trace ID"""
        old_trace = self.trace_id
        self.trace_id = trace_id or str(uuid.uuid4())
        try:
            yield self.trace_id
        finally:
            self.trace_id = old_trace
    
    def info(self, msg: str, **kwargs):
        """Log info with structured data"""
        if HAS_STRUCTLOG:
            self.logger.info(msg, **kwargs)
        else:
            self.logger.info(json.dumps({"msg": msg, "trace_id": self.trace_id, **kwargs}))
    
    def warning(self, msg: str, **kwargs):
        """Log warning with structured data"""
        if HAS_STRUCTLOG:
            self.logger.warning(msg, **kwargs)
        else:
            self.logger.warning(json.dumps({"msg": msg, "trace_id": self.trace_id, **kwargs}))
    
    def error(self, msg: str, **kwargs):
        """Log error with structured data"""
        if HAS_STRUCTLOG:
            self.logger.error(msg, **kwargs)
        else:
            self.logger.error(json.dumps({"msg": msg, "trace_id": self.trace_id, **kwargs}))
    
    def debug(self, msg: str, **kwargs):
        """Log debug with structured data"""
        if HAS_STRUCTLOG:
            self.logger.debug(msg, **kwargs)
        else:
            self.logger.debug(json.dumps({"msg": msg, "trace_id": self.trace_id, **kwargs}))

class JSONFormatter(logging.Formatter):
    """JSON formatter for standard logging"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, 'trace_id'):
            log_obj['trace_id'] = record.trace_id
        return json.dumps(log_obj)

# -----------------------------------------------------------------------------
# Prometheus Metrics
# -----------------------------------------------------------------------------
class MetricsCollector:
    """Prometheus metrics collector for PENIN-Ω"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if not HAS_PROMETHEUS:
            self.enabled = False
            return
        
        self.enabled = True
        self.registry = registry or CollectorRegistry()
        
        # Core metrics
        self.alpha = Gauge(
            'penin_alpha',
            'Current alpha_t^Ω value',
            registry=self.registry
        )
        
        self.delta_linf = Gauge(
            'penin_delta_linf',
            'Current ΔL∞ value',
            registry=self.registry
        )
        
        self.caos = Gauge(
            'penin_caos',
            'Current CAOS⁺ value',
            registry=self.registry
        )
        
        self.sr = Gauge(
            'penin_sr',
            'Current SR score',
            registry=self.registry
        )
        
        self.g = Gauge(
            'penin_g',
            'Current G (global coherence) score',
            registry=self.registry
        )
        
        self.oci = Gauge(
            'penin_oci',
            'Current OCI score',
            registry=self.registry
        )
        
        self.linf = Gauge(
            'penin_linf',
            'Current L∞ score',
            registry=self.registry
        )
        
        # Resource metrics
        self.cpu = Gauge(
            'penin_cpu',
            'CPU usage (0-1)',
            registry=self.registry
        )
        
        self.mem = Gauge(
            'penin_mem',
            'Memory usage (0-1)',
            registry=self.registry
        )
        
        # Decision counters
        self.decisions = Counter(
            'penin_decisions_total',
            'Total decisions by type',
            ['type'],
            registry=self.registry
        )
        
        # Gate failures
        self.gate_failures = Counter(
            'penin_gate_fail_total',
            'Total gate failures by gate',
            ['gate'],
            registry=self.registry
        )
        
        # Cycle metrics
        self.cycle_duration = Histogram(
            'penin_cycle_duration_seconds',
            'Cycle execution time in seconds',
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'penin_cache_hits_total',
            'Total cache hits by level',
            ['level'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'penin_cache_misses_total',
            'Total cache misses by level',
            ['level'],
            registry=self.registry
        )
        
        # Fibonacci optimizations
        self.fib_optimizations = Counter(
            'penin_fibonacci_optimizations_total',
            'Total Fibonacci optimizations performed',
            registry=self.registry
        )
        
        # Pattern stability
        self.pattern_stable = Gauge(
            'penin_pattern_stable',
            'Whether Fibonacci pattern is stable (0 or 1)',
            registry=self.registry
        )
        
        # WORM events
        self.worm_events = Counter(
            'penin_worm_events_total',
            'Total WORM events by type',
            ['event_type'],
            registry=self.registry
        )
    
    def update_from_state(self, state: Dict[str, Any]):
        """Update metrics from OmegaMEState"""
        if not self.enabled:
            return
        
        self.alpha.set(state.get('alpha_omega', 0))
        self.delta_linf.set(state.get('delta_linf', 0))
        self.caos.set(state.get('caos_plus', 0))
        self.sr.set(state.get('sr_score', 0))
        self.g.set(state.get('g_score', 0))
        self.oci.set(state.get('oci_score', 0))
        self.linf.set(state.get('l_inf', 0))
        self.cpu.set(state.get('cpu', 0))
        self.mem.set(state.get('mem', 0))
        self.pattern_stable.set(1 if state.get('pattern_stable', False) else 0)
    
    def record_decision(self, decision: str):
        """Record a decision"""
        if not self.enabled:
            return
        self.decisions.labels(type=decision).inc()
    
    def record_gate_failure(self, gate: str):
        """Record a gate failure"""
        if not self.enabled:
            return
        self.gate_failures.labels(gate=gate).inc()
    
    def record_cycle_duration(self, duration: float):
        """Record cycle duration"""
        if not self.enabled:
            return
        self.cycle_duration.observe(duration)
    
    def record_cache_hit(self, level: str):
        """Record cache hit"""
        if not self.enabled:
            return
        self.cache_hits.labels(level=level).inc()
    
    def record_cache_miss(self, level: str):
        """Record cache miss"""
        if not self.enabled:
            return
        self.cache_misses.labels(level=level).inc()
    
    def record_fib_optimization(self):
        """Record Fibonacci optimization"""
        if not self.enabled:
            return
        self.fib_optimizations.inc()
    
    def record_worm_event(self, event_type: str):
        """Record WORM event"""
        if not self.enabled:
            return
        self.worm_events.labels(event_type=event_type).inc()
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        if not self.enabled:
            return b""
        return generate_latest(self.registry)

# -----------------------------------------------------------------------------
# Metrics Server
# -----------------------------------------------------------------------------
class MetricsServer:
    """Simple HTTP server for Prometheus metrics with basic auth"""
    
    def __init__(self, collector: MetricsCollector, port: int = 8000, bind_host: str = "127.0.0.1", auth_token: Optional[str] = None, host: Optional[str] = None):
        self.collector = collector
        self.port = port
        # Support legacy parameter name 'host' as an alias for bind_host (used in some tests)
        self.bind_host = host if host is not None else bind_host
        # Back-compat attribute expected by some tests
        self.host = self.bind_host
        self.auth_token = auth_token
        self.server = None
        self.thread = None
    
    def start(self):
        """Start metrics server in background thread"""
        if not HAS_PROMETHEUS:
            return
        
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self):
                if handler_self.path == '/metrics':
                    # Check authentication if token is set
                    if self.auth_token:
                        auth_header = handler_self.headers.get('Authorization', '')
                        if not auth_header.startswith('Bearer '):
                            handler_self.send_response(401)
                            handler_self.send_header('WWW-Authenticate', 'Bearer')
                            handler_self.end_headers()
                            handler_self.wfile.write(b'Authentication required')
                            return
                        
                        token = auth_header[7:]  # Remove 'Bearer '
                        if token != self.auth_token:
                            handler_self.send_response(403)
                            handler_self.end_headers()
                            handler_self.wfile.write(b'Invalid token')
                            return
                    
                    handler_self.send_response(200)
                    handler_self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                    handler_self.end_headers()
                    handler_self.wfile.write(self.collector.get_metrics())
                elif handler_self.path == '/health':
                    # Health check endpoint (no auth required)
                    handler_self.send_response(200)
                    handler_self.send_header('Content-Type', 'application/json')
                    handler_self.end_headers()
                    handler_self.wfile.write(b'{"status": "healthy"}')
                else:
                    handler_self.send_response(404)
                    handler_self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress request logs
        
        # P0 Fix: Bind to localhost only for security (configurable)
        self.server = HTTPServer((self.bind_host, self.port), MetricsHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print(f"Metrics server started on {self.bind_host}:{self.port}")
    
    def stop(self):
        """Stop metrics server"""
        if self.server:
            self.server.shutdown()
            self.thread.join()

# -----------------------------------------------------------------------------
# Observability Manager
# -----------------------------------------------------------------------------
@dataclass
class ObservabilityConfig:
    """Configuration for observability"""
    enable_metrics: bool = True
    metrics_port: int = 8000
    metrics_bind_host: str = "127.0.0.1"  # Default to localhost for security
    metrics_auth_token: Optional[str] = None  # Bearer token for /metrics endpoint
    enable_json_logs: bool = True
    log_file: Optional[Path] = None
    log_level: str = "INFO"

class ObservabilityManager:
    """Manages all observability features"""
    
    def __init__(self, config: ObservabilityConfig = None):
        self.config = config or ObservabilityConfig()
        
        # Initialize logger
        self.logger = StructuredLogger(
            "PENIN-Ω",
            log_file=self.config.log_file
        )
        
        # Initialize metrics
        self.metrics = MetricsCollector() if self.config.enable_metrics else None
        
        # Initialize metrics server
        self.metrics_server = None
        if self.config.enable_metrics and HAS_PROMETHEUS:
            self.metrics_server = MetricsServer(
                self.metrics,
                port=self.config.metrics_port,
                bind_host=self.config.metrics_bind_host,
                auth_token=self.config.metrics_auth_token
            )
    
    def start(self):
        """Start observability services"""
        if self.metrics_server:
            self.metrics_server.start()
        self.logger.info("Observability manager started", 
                        metrics_enabled=self.config.enable_metrics,
                        json_logs_enabled=self.config.enable_json_logs)
    
    def stop(self):
        """Stop observability services"""
        if self.metrics_server:
            self.metrics_server.stop()
        self.logger.info("Observability manager stopped")
    
    @contextmanager
    def trace_cycle(self, cycle_num: int):
        """Context manager for tracing a cycle"""
        trace_id = f"cycle-{cycle_num}-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        with self.logger.trace(trace_id) as tid:
            self.logger.info("Cycle started", cycle=cycle_num, trace_id=tid)
            try:
                yield tid
            finally:
                duration = time.time() - start_time
                self.logger.info("Cycle completed", 
                               cycle=cycle_num, 
                               duration_ms=duration * 1000,
                               trace_id=tid)
                if self.metrics:
                    self.metrics.record_cycle_duration(duration)
    
    def log_gate_failure(self, gate: str, value: Any, threshold: Any, msg: str):
        """Log and record gate failure"""
        self.logger.warning("Gate failed",
                          gate=gate,
                          value=value,
                          threshold=threshold,
                          message=msg)
        if self.metrics:
            self.metrics.record_gate_failure(gate)
    
    def log_decision(self, decision: str, reason: Optional[str] = None, **kwargs):
        """Log and record decision"""
        self.logger.info("Decision made",
                        decision=decision,
                        reason=reason,
                        **kwargs)
        if self.metrics:
            self.metrics.record_decision(decision)
    
    def update_metrics(self, state: Dict[str, Any]):
        """Update metrics from state"""
        if self.metrics:
            self.metrics.update_from_state(state)

# -----------------------------------------------------------------------------
# Integration helper
# -----------------------------------------------------------------------------
def integrate_observability(core_instance):
    """
    Integrate observability into PeninOmegaCore instance
    
    Usage:
        from observability import integrate_observability
        core = PeninOmegaCore()
        obs = integrate_observability(core)
        obs.start()
    """
    import os
    obs_config = ObservabilityConfig(
        enable_metrics=True,
        metrics_port=8000,
        metrics_auth_token=os.getenv("PENIN_METRICS_TOKEN"),  # Set via env var
        enable_json_logs=True,
        log_file=Path("/opt/penin_omega/logs/penin_structured.log")
    )
    
    obs = ObservabilityManager(obs_config)
    
    # Monkey-patch core to use observability
    original_cycle = core_instance.master_equation_cycle
    
    async def wrapped_cycle(*args, **kwargs):
        with obs.trace_cycle(core_instance.xt.cycle):
            result = await original_cycle(*args, **kwargs)
            
            # Update metrics
            obs.update_metrics(core_instance.xt.to_dict())
            
            # Log decision
            obs.log_decision(
                result.get("decision", "UNKNOWN"),
                result.get("reason"),
                success=result.get("success", False)
            )
            
            # Log gate failures
            for gate_info in result.get("gate_trace", []):
                if not gate_info.get("passed", True):
                    obs.log_gate_failure(
                        gate_info.get("gate", "UNKNOWN"),
                        gate_info.get("value"),
                        gate_info.get("threshold"),
                        gate_info.get("msg", "")
                    )
            
            return result
    
    core_instance.master_equation_cycle = wrapped_cycle
    
    return obs

if __name__ == "__main__":
    # Demo
    print("Testing observability module...")
    
    config = ObservabilityConfig()
    obs = ObservabilityManager(config)
    obs.start()
    
    # Simulate some events
    with obs.trace_cycle(1):
        time.sleep(0.1)
        obs.log_decision("PROMOTE", reason="All gates passed")
        obs.update_metrics({
            "alpha_omega": 0.15,
            "delta_linf": 0.03,
            "caos_plus": 1.2,
            "sr_score": 0.85,
            "g_score": 0.78,
            "oci_score": 0.92,
            "l_inf": 0.73,
            "cpu": 0.45,
            "mem": 0.62
        })
    
    if HAS_PROMETHEUS:
        print(f"\nMetrics available at http://localhost:{config.metrics_port}/metrics")
        print("Press Ctrl+C to exit...")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            pass
    
    obs.stop()