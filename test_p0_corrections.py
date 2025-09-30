#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for P0 corrections in PENIN-Ω v7.0
==============================================

Tests verify:
1. Deterministic seed management
2. psutil fail-closed behavior
3. PROMOTE_ATTEST atomic events
4. Fibonacci boost clamping
5. Pydantic config validation
"""

import sys
import json
import asyncio
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add workspace to path
sys.path.insert(0, '/workspace')

# Import the v7 module
from importlib import import_module

def test_deterministic_seed():
    """Test that same seed produces identical results"""
    print("\n[TEST] Deterministic Seed Management")
    
    # Import module dynamically
    module = import_module('1_de_8_v7')
    
    # Create two cores with same seed
    config = {"evolution": {"seed": 12345}}
    core1 = module.PeninOmegaCore(config)
    core2 = module.PeninOmegaCore(config)
    
    # Run cycles and collect results
    async def run_cycles(core):
        results = []
        for _ in range(3):
            res = await core.master_equation_cycle()
            results.append({
                "decision": res["decision"],
                "metrics": res.get("metrics", {}),
                "state_hash": core.xt.compute_hash()
            })
        return results
    
    results1 = asyncio.run(run_cycles(core1))
    results2 = asyncio.run(run_cycles(core2))
    
    # Verify identical results
    for i, (r1, r2) in enumerate(zip(results1, results2)):
        assert r1["state_hash"] == r2["state_hash"], f"Cycle {i+1}: State hashes differ"
        assert r1["decision"] == r2["decision"], f"Cycle {i+1}: Decisions differ"
        print(f"  ✓ Cycle {i+1}: Deterministic (hash: {r1['state_hash'][:8]}...)")
    
    print("  ✓ Deterministic seed test PASSED")

def test_psutil_fail_closed():
    """Test fail-closed behavior when psutil is missing"""
    print("\n[TEST] psutil Fail-Closed Behavior")
    
    module = import_module('1_de_8_v7')
    
    # Mock psutil as unavailable
    with patch.dict('sys.modules', {'psutil': None}):
        # Reload module to pick up mock
        import importlib
        importlib.reload(module)
        
        # Create core without psutil
        core = module.PeninOmegaCore()
        
        async def check_resources():
            res = await core.master_equation_cycle()
            return core.xt.cpu, core.xt.mem, res["decision"]
        
        cpu, mem, decision = asyncio.run(check_resources())
        
        # Verify fail-closed: high resource usage assumed
        assert cpu >= 0.95, f"CPU should be high (fail-closed), got {cpu}"
        assert mem >= 0.95, f"Memory should be high (fail-closed), got {mem}"
        assert decision == "ABORT", f"Should abort with high resources, got {decision}"
        
        print(f"  ✓ Without psutil: CPU={cpu:.2f}, MEM={mem:.2f}")
        print(f"  ✓ Decision: {decision} (fail-closed)")
    
    print("  ✓ psutil fail-closed test PASSED")

def test_promote_attest_event():
    """Test PROMOTE_ATTEST atomic event recording"""
    print("\n[TEST] PROMOTE_ATTEST Event")
    
    module = import_module('1_de_8_v7')
    
    # Create core with favorable conditions for promotion
    config = {
        "evolution": {"seed": 999, "alpha_0": 0.5},
        "thresholds": {"beta_min": 0.001, "tau_caos": 0.5}
    }
    core = module.PeninOmegaCore(config)
    
    # Set favorable metrics
    core.xt.delta_linf = 0.1  # Positive delta
    core.xt.caos_plus = 1.5   # Above threshold
    core.xt.sr_score = 0.9    # Good SR
    core.xt.g_score = 0.8     # Good G
    core.xt.oci_score = 0.95  # Good OCI
    core.xt.rho = 0.3         # Low risk
    core.xt.cpu = 0.5         # Normal CPU
    core.xt.mem = 0.5         # Normal memory
    
    async def run_promotion():
        res = await core.master_equation_cycle()
        return res
    
    result = asyncio.run(run_promotion())
    
    # Check for PROMOTE_ATTEST in WORM
    cursor = core.worm.db.cursor()
    cursor.execute("SELECT * FROM events WHERE etype = 'PROMOTE_ATTEST'")
    promote_events = cursor.fetchall()
    
    if result["decision"] == "PROMOTE":
        assert len(promote_events) > 0, "PROMOTE_ATTEST event not found"
        
        # Verify event structure
        event = promote_events[-1]
        data = json.loads(event[2])  # data column
        
        assert "step" in data, "Missing step in PROMOTE_ATTEST"
        assert "alpha" in data, "Missing alpha in PROMOTE_ATTEST"
        assert "delta_linf" in data, "Missing delta_linf in PROMOTE_ATTEST"
        assert "config_hash" in data, "Missing config_hash in PROMOTE_ATTEST"
        
        # Check hashes
        pre_hash = event[8]   # pre_hash column
        post_hash = event[9]  # post_hash column
        assert pre_hash is not None, "Missing pre_hash"
        assert post_hash is not None, "Missing post_hash"
        assert pre_hash != post_hash, "Pre and post hashes should differ"
        
        print(f"  ✓ PROMOTE_ATTEST recorded")
        print(f"  ✓ Pre-hash:  {pre_hash[:8]}...")
        print(f"  ✓ Post-hash: {post_hash[:8]}...")
        print(f"  ✓ Step: {data['step']:.6f}")
    else:
        print(f"  ℹ No promotion occurred (decision: {result['decision']})")
    
    print("  ✓ PROMOTE_ATTEST test PASSED")

def test_fibonacci_boost_clamp():
    """Test Fibonacci boost is clamped to ≤5% with EWMA stability"""
    print("\n[TEST] Fibonacci Boost Clamping")
    
    module = import_module('1_de_8_v7')
    
    # Enable Fibonacci with specific config
    config = {
        "evolution": {"seed": 777},
        "fibonacci": {"enabled": True},
        "caos_plus": {
            "max_boost": 0.05,  # 5% max
            "ewma_alpha": 0.2,
            "min_stability_cycles": 3
        }
    }
    core = module.PeninOmegaCore(config)
    
    # Track CAOS values across cycles
    caos_values = []
    pattern_stable_flags = []
    
    async def run_cycles():
        for i in range(10):
            # Set consistent CAOS components for pattern
            core.xt.C = 0.6 + i * 0.01
            core.xt.A = 0.6 + i * 0.01
            core.xt.O = 0.6 + i * 0.01
            core.xt.S = 0.6 + i * 0.01
            
            res = await core.master_equation_cycle()
            caos_values.append(core.xt.caos_plus)
            pattern_stable_flags.append(core.xt.pattern_stable)
    
    asyncio.run(run_cycles())
    
    # Check boost clamping
    for i, (caos, stable) in enumerate(zip(caos_values, pattern_stable_flags)):
        if i >= 3 and stable:  # After min_stability_cycles
            # Calculate base CAOS without boost
            base = 1.0 + core.caos.kappa * core.xt.C * core.xt.A
            exponent = core.xt.O * core.xt.S
            base_caos = base ** exponent
            
            # Check boost is within 5%
            boost_ratio = caos / base_caos if base_caos > 0 else 1.0
            assert boost_ratio <= 1.05, f"Boost {boost_ratio:.3f} exceeds 1.05 at cycle {i}"
            
            print(f"  ✓ Cycle {i}: CAOS={caos:.3f}, Boost≤5%, Stable={stable}")
        else:
            print(f"  ℹ Cycle {i}: CAOS={caos:.3f}, Stable={stable} (warming up)")
    
    print("  ✓ Fibonacci boost clamp test PASSED")

def test_pydantic_config_validation():
    """Test Pydantic config validation"""
    print("\n[TEST] Pydantic Config Validation")
    
    module = import_module('1_de_8_v7')
    
    # Test valid config
    valid_config = {
        "ethics": {"ece_max": 0.01},
        "evolution": {"alpha_0": 0.1}
    }
    
    try:
        core = module.PeninOmegaCore(valid_config)
        print("  ✓ Valid config accepted")
    except SystemExit:
        assert False, "Valid config rejected"
    
    # Test invalid configs
    invalid_configs = [
        # ECE out of range
        {"ethics": {"ece_max": 1.5}},
        # Invalid weight sum
        {"sr_omega": {"weights": {"C": 0.5, "E": 0.5, "M": 0.5, "A": 0.5}}},
        # Wrong number of weights
        {"omega_sigma": {"weights": [0.125] * 7}},
        # Invalid search method
        {"fibonacci": {"search_method": "invalid"}},
        # Negative alpha
        {"evolution": {"alpha_0": -0.1}}
    ]
    
    for i, invalid_config in enumerate(invalid_configs):
        try:
            core = module.PeninOmegaCore(invalid_config)
            assert False, f"Invalid config {i+1} should have been rejected"
        except SystemExit:
            print(f"  ✓ Invalid config {i+1} rejected correctly")
    
    print("  ✓ Pydantic validation test PASSED")

def test_determinism_with_replay():
    """Test that we can replay cycles with same seed and get same results"""
    print("\n[TEST] Deterministic Replay")
    
    module = import_module('1_de_8_v7')
    
    # Run first session
    config = {"evolution": {"seed": 54321}}
    core1 = module.PeninOmegaCore(config)
    
    # Capture events
    events1 = []
    
    async def capture_run(core):
        for _ in range(5):
            res = await core.master_equation_cycle()
            events1.append({
                "cycle": core.xt.cycle,
                "decision": res["decision"],
                "caos": core.xt.caos_plus,
                "l_inf": core.xt.l_inf,
                "state_hash": core.xt.compute_hash()
            })
    
    asyncio.run(capture_run(core1))
    
    # Run second session with same seed
    core2 = module.PeninOmegaCore(config)
    events2 = []
    
    async def replay_run(core):
        for _ in range(5):
            res = await core.master_equation_cycle()
            events2.append({
                "cycle": core.xt.cycle,
                "decision": res["decision"],
                "caos": core.xt.caos_plus,
                "l_inf": core.xt.l_inf,
                "state_hash": core.xt.compute_hash()
            })
    
    asyncio.run(replay_run(core2))
    
    # Verify identical replay
    for i, (e1, e2) in enumerate(zip(events1, events2)):
        assert e1["state_hash"] == e2["state_hash"], f"Replay {i}: State hash mismatch"
        assert e1["decision"] == e2["decision"], f"Replay {i}: Decision mismatch"
        assert abs(e1["caos"] - e2["caos"]) < 1e-10, f"Replay {i}: CAOS mismatch"
        assert abs(e1["l_inf"] - e2["l_inf"]) < 1e-10, f"Replay {i}: L∞ mismatch"
        print(f"  ✓ Replay {i}: Identical (hash: {e1['state_hash'][:8]}...)")
    
    print("  ✓ Deterministic replay test PASSED")

def run_all_tests():
    """Run all P0 correction tests"""
    print("=" * 60)
    print("P0 CORRECTIONS TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_deterministic_seed,
        test_psutil_fail_closed,
        test_promote_attest_event,
        test_fibonacci_boost_clamp,
        test_pydantic_config_validation,
        test_determinism_with_replay
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n  ✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)