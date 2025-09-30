#!/usr/bin/env python3
"""
Complete System Test - PENIN-Ω v7.1+
====================================

Comprehensive test suite for all system components.
"""

import sys
import time
from pathlib import Path

# Add workspace to path
sys.path.insert(0, "/workspace")


def test_imports():
    """Test all module imports"""
    print("\n[TEST] Module Imports")

    try:
        # Core omega modules
        from penin.omega import (
            scoring,
            caos,
            ethics_metrics,
            guards,
            sr,
            tuner,
            acfa,
            ledger,
            mutators,
            evaluators,
            runners,
        )

        print("  ✅ All omega modules imported")

        # Provider modules
        from penin.providers import base

        print("  ✅ Provider base imported")

        # Router
        from penin import router

        print("  ✅ Router imported")

        # Config
        from penin import config

        print("  ✅ Config imported")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_scoring_module():
    """Test scoring functions"""
    print("\n[TEST] Scoring Module")

    try:
        from penin.omega.scoring import (
            harmonic_mean,
            linf_harmonic,
            score_gate,
            normalize_series,
            ema,
            ScoreGateVerdict,
        )

        # Test harmonic mean
        values = [0.8, 0.6, 0.7]
        hm = harmonic_mean(values)
        assert 0 < hm <= 1.0, f"Harmonic mean out of range: {hm}"
        print(f"  ✅ Harmonic mean: {hm:.3f}")

        # Test score gate
        verdict, score = score_gate(U=0.8, S=0.7, C=0.3, L=0.6, wU=0.25, wS=0.25, wC=0.25, wL=0.25, tau=0.7)
        print(f"  ✅ Score gate: {verdict.value}, score={score:.3f}")

        # Test normalize series
        series = [1, 2, 3, 4, 5]
        normalized = normalize_series(series, method="minmax")
        assert min(normalized) == 0.0 and max(normalized) == 1.0
        print(f"  ✅ Normalize series: {normalized}")

        # Test EMA
        ema_val = ema(0.5, 0.8, alpha=0.2)
        assert 0 <= ema_val <= 1.0
        print(f"  ✅ EMA: {ema_val:.3f}")

        return True
    except Exception as e:
        print(f"  ❌ Scoring test failed: {e}")
        return False


def test_caos_module():
    """Test CAOS⁺ computation"""
    print("\n[TEST] CAOS Module")

    try:
        from penin.omega.caos import phi_caos, CAOSComponents, CAOSPlusEngine

        # Test phi_caos function
        phi = phi_caos(C=0.7, A=0.8, O=0.6, S=0.5)
        assert 0 <= phi < 1.0, f"Phi out of range: {phi}"
        print(f"  ✅ Phi CAOS: {phi:.4f}")

        # Test CAOSComponents
        components = CAOSComponents(C=0.8, A=0.9, O=0.7, S=0.6)
        assert components.C == 0.8
        print(f"  ✅ CAOS Components: {components.to_dict()}")

        # Test CAOSPlusEngine
        engine = CAOSPlusEngine(kappa=2.0, gamma=0.7)
        phi2 = engine.compute(0.7, 0.8, 0.6, 0.5)
        is_stable = engine.is_stable(0.7, 0.8, 0.6, 0.5)
        print(f"  ✅ CAOS Engine: phi={phi2:.4f}, stable={is_stable}")

        return True
    except Exception as e:
        print(f"  ❌ CAOS test failed: {e}")
        return False


def test_ethics_module():
    """Test ethics metrics"""
    print("\n[TEST] Ethics Metrics Module")

    try:
        from penin.omega.ethics_metrics import EthicsCalculator, EthicsGate, EthicsMetrics

        # Create calculator
        calc = EthicsCalculator()

        # Test ECE calculation
        predictions = [0.9, 0.8, 0.7, 0.6, 0.5] * 20
        targets = [1, 1, 0, 0, 0] * 20
        ece, ece_evidence = calc.calculate_ece(predictions, targets, n_bins=10)
        assert 0 <= ece <= 1.0, f"ECE out of range: {ece}"
        print(f"  ✅ ECE: {ece:.4f}")

        # Test bias ratio
        protected_attrs = ["A", "B", "A", "B", "A"] * 20
        rho_bias, bias_evidence = calc.calculate_bias_ratio(predictions, targets, protected_attrs)
        assert rho_bias >= 1.0, f"Bias ratio invalid: {rho_bias}"
        print(f"  ✅ Bias ratio: {rho_bias:.4f}")

        # Test fairness
        fairness, fairness_evidence = calc.calculate_fairness(predictions, targets, protected_attrs)
        assert 0 <= fairness <= 1.0, f"Fairness out of range: {fairness}"
        print(f"  ✅ Fairness: {fairness:.4f}")

        # Test risk contraction
        risk_series = [0.5 - i * 0.01 for i in range(50)]
        rho_risk, risk_evidence = calc.calculate_risk_contraction(risk_series)
        print(f"  ✅ Risk rho: {rho_risk:.4f}")

        return True
    except Exception as e:
        print(f"  ❌ Ethics test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_guards_module():
    """Test guards orchestrator"""
    print("\n[TEST] Guards Module")

    try:
        from penin.omega.guards import GuardOrchestrator

        orchestrator = GuardOrchestrator()

        # Test with good state
        good_state = {
            "consent": True,
            "eco": True,
            "ece": 0.005,
            "bias": 1.02,
            "fairness": 0.98,
            "rho": 0.85,
            "U": 0.8,
            "S": 0.7,
            "C": 0.3,
            "L": 0.6,
        }

        passed, violations, evidence = orchestrator.check_all_guards(good_state)
        print(f"  ✅ Guards check (good): passed={passed}, violations={len(violations)}")

        # Test with bad state
        bad_state = good_state.copy()
        bad_state["ece"] = 0.15  # Too high
        bad_state["consent"] = False

        passed2, violations2, evidence2 = orchestrator.check_all_guards(bad_state)
        print(f"  ✅ Guards check (bad): passed={passed2}, violations={len(violations2)}")

        return True
    except Exception as e:
        print(f"  ❌ Guards test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_evaluators_module():
    """Test evaluators"""
    print("\n[TEST] Evaluators Module")

    try:
        from penin.omega.evaluators import (
            ComprehensiveEvaluator,
            UtilityEvaluator,
            StabilityEvaluator,
            CostEvaluator,
            LearningEvaluator,
        )

        # Mock model
        def mock_model(prompt: str) -> str:
            if "json" in prompt.lower():
                return '{"nome": "João Silva", "email": "joao@email.com", "telefone": "(11) 99999-9999"}'
            elif "capital" in prompt.lower():
                return "Brasília"
            elif "resumo" in prompt.lower():
                return "IA transforma economia com investimentos bilionários."
            else:
                return f"Resposta para: {prompt[:30]}..."

        # Test comprehensive evaluator
        evaluator = ComprehensiveEvaluator(baseline_cost_usd=0.01)
        result = evaluator.evaluate_model(
            mock_model, config={"temperature": 0.7}, provider_id="test", model_name="test-model"
        )

        print(f"  ✅ U: {result.U:.3f}")
        print(f"  ✅ S: {result.S:.3f}")
        print(f"  ✅ C: {result.C:.3f}")
        print(f"  ✅ L: {result.L:.3f}")
        print(f"  ✅ Tokens: {result.total_tokens}")
        print(f"  ✅ Cost: ${result.total_cost_usd:.4f}")

        return True
    except Exception as e:
        print(f"  ❌ Evaluators test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_evolution_runner():
    """Test evolution runner"""
    print("\n[TEST] Evolution Runner")

    try:
        from penin.omega.runners import quick_evolution_cycle

        # Run quick cycle
        print("  Running quick evolution cycle...")
        result = quick_evolution_cycle(n_challengers=2, budget_usd=0.1, seed=12345)

        print(f"  ✅ Cycle: {result.cycle_id[:16]}...")
        print(f"  ✅ Success: {result.success}")
        print(f"  ✅ Phase: {result.phase.value}")
        print(f"  ✅ Duration: {result.duration_s:.2f}s")
        print(f"  ✅ Promotions: {result.promotions}")
        print(f"  ✅ Canaries: {result.canaries}")
        print(f"  ✅ Rejections: {result.rejections}")

        return result.success
    except Exception as e:
        print(f"  ❌ Runner test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_router():
    """Test multi-LLM router"""
    print("\n[TEST] Router Module")

    try:
        from penin.router import MultiLLMRouter
        from penin.providers.base import BaseProvider, LLMResponse

        # Create mock provider
        class MockProvider(BaseProvider):
            def __init__(self, provider_id: str):
                super().__init__(provider_id=provider_id)

            async def chat(self, messages, **kwargs):
                return LLMResponse(
                    content="Mock response",
                    provider_id=self.provider_id,
                    model="mock-model",
                    latency_s=0.1,
                    cost_usd=0.001,
                    prompt_tokens=10,
                    completion_tokens=20,
                )

        # Create router
        providers = [MockProvider("mock1"), MockProvider("mock2")]
        router = MultiLLMRouter(providers=providers, daily_budget_usd=5.0)

        # Get budget status
        status = router.get_budget_status()
        print(f"  ✅ Budget status: ${status['current_usage_usd']:.2f} / ${status['daily_budget_usd']:.2f}")

        # Get usage stats
        stats = router.get_usage_stats()
        print(f"  ✅ Usage stats: {stats['request_count']} requests")

        return True
    except Exception as e:
        print(f"  ❌ Router test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("PENIN-Ω COMPLETE SYSTEM TEST")
    print("=" * 70)

    start_time = time.time()

    tests = [
        ("Imports", test_imports),
        ("Scoring", test_scoring_module),
        ("CAOS", test_caos_module),
        ("Ethics", test_ethics_module),
        ("Guards", test_guards_module),
        ("Evaluators", test_evaluators_module),
        ("Evolution Runner", test_evolution_runner),
        ("Router", test_router),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    duration = time.time() - start_time

    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")
    print(f"Duration: {duration:.2f}s")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
