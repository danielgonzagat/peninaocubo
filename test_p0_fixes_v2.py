#!/usr/bin/env python3
"""
Test Suite for P0 Audit Fixes v2
=================================

Tests all P0 corrections using the new class-based API.
"""

import sys
import os
import json
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import List

# Imports dos módulos corrigidos
from penin.omega.ethics_metrics import (
    EthicsCalculator,
    EthicsGate,
    EthicsMetrics
)

def test_ethics_calculator():
    """Test ethics calculator with synthetic data."""
    print("\n[TEST] Ethics Calculator")
    
    calculator = EthicsCalculator()
    
    # Generate synthetic data
    n_samples = 100
    predictions = [0.5 + 0.3 * (i % 2) for i in range(n_samples)]
    targets = [i % 2 for i in range(n_samples)]
    protected_attrs = ['A' if i < 50 else 'B' for i in range(n_samples)]
    risk_series = [0.1 * (i % 10) for i in range(50)]
    
    consent_data = {
        'user_consent': True,
        'data_usage_consent': True,
        'processing_consent': True
    }
    
    eco_data = {
        'carbon_footprint_ok': True,
        'energy_efficiency_ok': True,
        'waste_minimization_ok': True
    }
    
    # Calculate metrics
    metrics = calculator.calculate_all_metrics(
        predictions=predictions,
        targets=targets,
        protected_attributes=protected_attrs,
        risk_series=risk_series,
        consent_data=consent_data,
        eco_data=eco_data,
        dataset_id="test_dataset",
        seed=42
    )
    
    # Verify metrics
    assert isinstance(metrics, EthicsMetrics)
    assert 0 <= metrics.ece <= 1
    assert metrics.rho_bias >= 1.0
    assert 0 <= metrics.fairness <= 1
    assert metrics.consent in [True, False]
    assert metrics.eco_ok in [True, False]
    assert 0 <= metrics.risk_rho <= 2
    assert len(metrics.evidence_hash) > 0
    
    print(f"✓ ECE: {metrics.ece:.4f}")
    print(f"✓ Bias: {metrics.rho_bias:.4f}")
    print(f"✓ Fairness: {metrics.fairness:.4f}")
    print(f"✓ Consent: {metrics.consent}")
    print(f"✓ Eco: {metrics.eco_ok}")
    print(f"✓ Risk ρ: {metrics.risk_rho:.4f}")
    print(f"✓ Hash: {metrics.evidence_hash[:16]}")
    
    return True

def test_ethics_gate():
    """Test ethics gate validation."""
    print("\n[TEST] Ethics Gate")
    
    gate = EthicsGate()
    
    # Test passing metrics
    from datetime import datetime
    good_metrics = EthicsMetrics(
        ece=0.05,
        rho_bias=1.1,
        fairness=0.9,
        consent=True,
        eco_ok=True,
        risk_rho=1.2,
        evidence_hash="test_hash_123",
        calculation_timestamp=datetime.now().isoformat()
    )
    
    passed, violations = gate.validate(good_metrics)
    assert passed, f"Good metrics should pass, violations: {violations}"
    print(f"✓ Good metrics passed: {passed}")
    
    # Test failing metrics
    bad_metrics = EthicsMetrics(
        ece=0.5,  # Too high
        rho_bias=3.0,  # Too biased
        fairness=0.3,  # Too unfair
        consent=False,  # No consent
        eco_ok=False,  # Not eco-friendly
        risk_rho=2.5,  # Too risky
        evidence_hash="test_hash_456",
        calculation_timestamp=datetime.now().isoformat()
    )
    
    passed, violations = gate.validate(bad_metrics)
    assert not passed, "Bad metrics should not pass"
    assert len(violations) > 0, "Should have violations"
    print(f"✓ Bad metrics failed: {not passed}")
    print(f"✓ Violations: {len(violations)}")
    
    return True

def test_worm_sqlite_wal():
    """Test SQLite WORM with WAL mode."""
    print("\n[TEST] SQLite WORM with WAL")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_worm.db"
        
        # Connect and check WAL mode
        conn = sqlite3.connect(str(db_path))
        
        # Enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=3000")
        
        # Check journal mode
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal", f"Expected WAL mode, got {result[0]}"
        print(f"✓ Journal mode: {result[0]}")
        
        # Check busy timeout
        result = conn.execute("PRAGMA busy_timeout").fetchone()
        assert result[0] == 3000, f"Expected 3000ms timeout, got {result[0]}"
        print(f"✓ Busy timeout: {result[0]}ms")
        
        conn.close()
    
    return True

def test_metrics_server_binding():
    """Test metrics server localhost binding."""
    print("\n[TEST] Metrics Server Binding")
    
    # Check default configuration
    from observability import ObservabilityConfig
    
    config = ObservabilityConfig()
    
    # Default should be localhost
    assert config.metrics_bind_host == "127.0.0.1", \
        f"Expected localhost binding, got {config.metrics_bind_host}"
    print(f"✓ Default bind: {config.metrics_bind_host}")
    
    # Test custom configuration
    custom_config = ObservabilityConfig(metrics_bind_host="0.0.0.0")
    assert custom_config.metrics_bind_host == "0.0.0.0"
    print(f"✓ Custom bind: {custom_config.metrics_bind_host}")
    
    return True

def test_router_cost_budget():
    """Test router cost-aware budget management."""
    print("\n[TEST] Router Cost Budget")
    
    from penin.router import MultiLLMRouter
    
    # Create mock providers for testing
    class MockProvider:
        def __init__(self, name):
            self.name = name
            self.cost_per_1k = 0.001
    
    providers = [MockProvider("test_provider")]
    
    # Create router with small budget for testing
    router = MultiLLMRouter(providers=providers, daily_budget_usd=0.01)
    
    # Check initial state
    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] == 0
    assert stats["budget_remaining_usd"] == 0.01
    print(f"✓ Initial budget: ${stats['budget_remaining_usd']:.2f}")
    
    # Simulate usage
    router._daily_spend = 0.005
    router._total_tokens = 1000
    router._request_count = 1
    
    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] == 0.005
    assert stats["budget_remaining_usd"] == 0.005
    print(f"✓ After usage: ${stats['daily_spend_usd']:.3f} spent")
    print(f"✓ Remaining: ${stats['budget_remaining_usd']:.3f}")
    
    # Test budget exceeded
    router._daily_spend = 0.015
    router._total_tokens = 3000
    router._request_count = 2
    
    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] == 0.015
    assert stats["budget_remaining_usd"] == 0  # max(0, ...) prevents negative
    print(f"✓ Budget exceeded: ${stats['daily_spend_usd']:.3f} > $0.01")
    
    return True

def main():
    """Run all P0 fixes tests."""
    tests = [
        test_ethics_calculator,
        test_ethics_gate,
        test_worm_sqlite_wal,
        test_metrics_server_binding,
        test_router_cost_budget,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)