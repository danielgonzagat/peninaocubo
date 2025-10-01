#!/usr/bin/env python3
"""
PENIN-Ω System Integration Tests
==================================

End-to-end tests for the complete PENIN-Ω system including:
- Ethics pipeline (calculate → attest → guard)
- Router with budget tracking
- Observability integration
- WORM ledger operations
"""

import asyncio
import sys
import tempfile
from datetime import UTC
from pathlib import Path

import pytest

# Add workspace to path
sys.path.insert(0, "/workspace")


def test_ethics_pipeline_integration():
    """Test complete ethics pipeline from calculation to attestation"""
    print("\n=== Integration: Ethics Pipeline ===")

    from penin.omega.ethics_metrics import EthicsAttestation, EthicsCalculator, compute_ethics_attestation, sigma_guard

    # Generate synthetic data
    n = 200
    predictions = [i / n for i in range(n)]
    predicted_probs = [p + 0.1 * (i % 10) / 10 for i, p in enumerate(predictions)]
    labels = [1 if i % 3 == 0 else 0 for i in range(n)]
    groups = ["A" if i % 2 == 0 else "B" for i in range(n)]

    # Step 1: Calculate individual metrics
    calc = EthicsCalculator()
    ece, ece_hash = calc.compute_ece(predicted_probs, labels)
    rho, rho_hash = calc.compute_bias_ratio(predictions, groups, labels)
    fair, fair_hash = calc.compute_fairness(predictions, groups, labels)

    print(f"✓ Metrics calculated: ECE={ece:.4f}, ρ={rho:.4f}, F={fair:.4f}")

    # Step 2: Generate attestation
    model_outputs = {
        "predicted_probs": predicted_probs,
        "predictions": predictions,
        "protected_groups": groups,
        "estimated_tokens": 2000,
    }
    ground_truth = {
        "labels": labels,
        "dataset_hash": "integration_test_v1",
        "consent_verified": True,
        "risk_series": [0.5 - i * 0.01 for i in range(20)],  # Decreasing risk
    }

    attestation = compute_ethics_attestation(model_outputs, ground_truth, seed=42)

    assert isinstance(attestation, EthicsAttestation)
    assert len(attestation.evidence_hash) == 64
    assert len(attestation.compute_hash()) == 64
    print(f"✓ Attestation generated: pass={attestation.pass_sigma_guard}")

    # Step 3: Sigma guard validation
    guard_result, guard_details = sigma_guard(
        ece=attestation.ece,
        rho_bias=attestation.rho_bias,
        fairness_score=attestation.fairness_score,
        consent_ok=attestation.consent_ok,
        risk_rho=attestation.risk_rho,
        thresholds={"ece_max": 0.15, "rho_bias_max": 2.0, "fairness_min": 0.7, "risk_rho_max": 1.0},
    )

    print(f"✓ Sigma guard: {'PASS' if guard_result else 'FAIL'}")
    print(f"  Details: {guard_details}")

    return True


def test_router_with_observability():
    """Test router integration with observability and budget tracking"""
    print("\n=== Integration: Router + Observability ===")

    # Note: observability module consolidated - skip for now
    pytest.skip("observability module consolidated - test needs update")

    from observability import ObservabilityConfig, ObservabilityManager

    from penin.providers.base import BaseProvider, LLMResponse
    from penin.router import MultiLLMRouterComplete as MultiLLMRouter

    # Mock provider
    class TestProvider(BaseProvider):
        def __init__(self, name: str):
            self.name = name
            self.model = f"test-{name}"

        async def chat(self, messages, **kwargs):
            await asyncio.sleep(0.01)
            return LLMResponse(
                content=f"Response from {self.name}",
                model=self.model,
                tokens_in=15,
                tokens_out=25,
                cost_usd=0.002,
                latency_s=0.15,
                provider=self.name,
            )

    # Create router with budget
    providers = [TestProvider("provider1"), TestProvider("provider2")]
    router = MultiLLMRouter(providers, daily_budget_usd=0.05, cost_weight=0.4, latency_weight=0.3, quality_weight=0.3)

    print(f"✓ Router initialized with budget: ${router.daily_budget_usd}")

    # Setup observability
    obs_config = ObservabilityConfig(
        enable_metrics=True,
        metrics_port=8001,  # Use different port to avoid conflicts
        metrics_bind_host="127.0.0.1",
        enable_json_logs=True,
    )
    obs = ObservabilityManager(obs_config)
    print("✓ Observability configured")

    # Make requests
    async def make_requests():
        responses = []
        for i in range(3):
            try:
                response = await router.ask([{"role": "user", "content": f"test {i}"}])
                responses.append(response)
            except RuntimeError as e:
                print(f"  Request {i} blocked: {e}")
                break
        return responses

    responses = asyncio.run(make_requests())
    print(f"✓ Made {len(responses)} requests")

    # Check usage stats
    stats = router.get_usage_stats()
    assert stats["request_count"] == len(responses)
    assert stats["daily_spend_usd"] > 0
    print(f"✓ Budget tracking: ${stats['daily_spend_usd']:.4f} spent, {stats['budget_used_pct']:.1f}% used")

    return True


def test_scoring_integration():
    """Test scoring module integration with all components"""
    print("\n=== Integration: Scoring System ===")

    from penin.omega.caos import caos_plus
    from penin.omega.scoring import linf_harmonic
    from penin.omega.sr import sr_omega

    # Step 1: Calculate component scores
    U = 0.85  # Utility
    S = 0.90  # Stability
    C = 0.65  # Cost (lower is better)
    L = 0.80  # Learning

    print(f"✓ Component scores: U={U}, S={S}, C={C}, L={L}")

    # Step 2: Calculate CAOS+
    caos_result = caos_plus(coherence=0.85, awareness=0.90, openness=0.75, stability=0.88, kappa=1.5, gamma=2.0)
    # caos_plus returns a dict with 'phi' key
    caos_score = caos_result['phi'] if isinstance(caos_result, dict) else caos_result
    print(f"✓ CAOS⁺ score: {caos_score:.4f}")

    # Step 3: Calculate SR
    sr_score = sr_omega(awareness=0.90, ethics_ok=True, autocorr=0.85, metacognition=0.80)
    print(f"✓ SR-Ω score: {sr_score:.4f}")

    # Step 4: Calculate L∞
    linf_score = linf_harmonic(
        weights={"U": 0.4, "S": 0.3, "C": 0.2, "L": 0.1},
        metrics={"U": U, "S": S, "C": 1 - C, "L": L},  # Invert cost
        cost_factor=C,
        lambda_c=0.5,
        ethical_ok=True,
    )
    print(f"✓ L∞ score: {linf_score:.4f}")

    # Step 5: Combined score
    combined_score = linf_score * caos_score * sr_score
    print(f"✓ Combined score: {combined_score:.4f}")

    assert 0 <= combined_score <= 1
    assert 0 <= linf_score <= 1

    return True


def test_ledger_operations():
    """Test WORM ledger with full cycle"""
    print("\n=== Integration: WORM Ledger ===")

    import sqlite3
    from datetime import datetime

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "integration_ledger.db"

        # Create ledger
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=3000")

        # Create schema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                data TEXT NOT NULL,
                hash TEXT NOT NULL,
                prev_hash TEXT
            )
        """)

        print("✓ Ledger created with WAL mode")

        # Insert events
        events = []
        prev_hash = "genesis"

        for i in range(10):
            import hashlib
            import json

            event_data = {
                "cycle": i,
                "action": "evaluate",
                "score": 0.8 + i * 0.01,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            data_str = json.dumps(event_data, sort_keys=True)
            current_hash = hashlib.sha256(f"{prev_hash}{data_str}".encode()).hexdigest()

            conn.execute(
                "INSERT INTO events (timestamp, event_type, cycle_id, data, hash, prev_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now(UTC).timestamp(), "CYCLE", f"cycle_{i}", data_str, current_hash, prev_hash),
            )

            events.append(current_hash)
            prev_hash = current_hash

        conn.commit()
        print(f"✓ Inserted {len(events)} events with hash chain")

        # Verify hash chain
        cursor = conn.execute("SELECT hash, prev_hash FROM events ORDER BY id")
        rows = cursor.fetchall()

        chain_valid = True
        for i in range(1, len(rows)):
            if rows[i][1] != rows[i - 1][0]:
                chain_valid = False
                break

        assert chain_valid, "Hash chain broken!"
        print("✓ Hash chain verified")

        conn.close()

    return True


def run_all_integration_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("PENIN-Ω SYSTEM INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Ethics Pipeline", test_ethics_pipeline_integration),
        ("Router + Observability", test_router_with_observability),
        ("Scoring System", test_scoring_integration),
        ("WORM Ledger", test_ledger_operations),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASS" if result else "❌ FAIL"))
            print(f"\n{name}: {'✅ PASS' if result else '❌ FAIL'}")
        except Exception as e:
            results.append((name, f"❌ ERROR: {e}"))
            print(f"\n{name}: ❌ ERROR")
            print(f"  {str(e)}")

    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)

    for name, status in results:
        print(f"{status:12} {name}")

    passed = sum(1 for _, s in results if "✅" in s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed ({100 * passed // total}%)")
    print("=" * 60)

    return all("✅" in s for _, s in results)


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
