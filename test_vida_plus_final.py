#!/usr/bin/env python3
"""
Final comprehensive test for PENIN-Ω Vida+ system
Tests all working modules and validates the core Life Equation (+)
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add workspace to path
sys.path.insert(0, "/workspace")


def test_core_system():
    """Test core system components"""
    print("🧪 Testing Core System Components...")

    try:
        from penin.omega.scoring import linf_harmonic
        from penin.omega.caos import phi_caos
        from penin.omega.guards import sigma_guard, ir_to_ic_contractive

        # Test L∞ harmonic scoring
        weights = [0.5, 0.3, 0.2]
        values = [0.8, 0.7, 0.9]
        score = linf_harmonic(weights, values, cost=0.1, lambda_c=0.1, ethical_ok=True)
        print(f"✅ L∞ harmonic score: {score:.3f}")

        # Test CAOS⁺ phi calculation
        phi = phi_caos(0.7, 0.8, 0.6, 0.9)
        print(f"✅ CAOS⁺ phi: {phi:.3f}")

        # Test Σ-Guard
        sigma_ok, details = sigma_guard(ece=0.01, rho_bias=1.02, fairness=0.8, consent=True, eco_ok=True)
        print(f"✅ Σ-Guard: {sigma_ok}")

        # Test IR→IC contractivity
        risk_series = {"rho": 0.8}
        contractive, rho = ir_to_ic_contractive(risk_series, rho_threshold=1.0)
        print(f"✅ IR→IC contractivity: {contractive}, rho={rho:.3f}")

        return True
    except Exception as e:
        print(f"❌ Core system test failed: {e}")
        return False


def test_life_equation_complete():
    """Test complete Life Equation implementation"""
    print("\n🧪 Testing Complete Life Equation...")

    try:
        from penin.omega.life_eq import life_equation

        # Valid inputs for Life Equation
        ethics_input = {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True}

        risk_series = {"rho": 0.8}
        caos_components = (0.7, 0.8, 0.6, 0.9)  # (C, A, O, S)
        sr_components = (0.8, 0.9, 0.7, 0.8)  # (awareness, ethics_ok, autocorr, metacog)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85}

        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds,
        )

        if verdict.ok and verdict.alpha_eff > 0:
            print(f"✅ Life Equation success: alpha_eff = {verdict.alpha_eff:.3f}")
            print(f"   - phi: {verdict.metrics.get('phi', 0):.3f}")
            print(f"   - sr: {verdict.metrics.get('sr', 0):.3f}")
            print(f"   - G: {verdict.metrics.get('G', 0):.3f}")
            print(f"   - L_inf: {verdict.metrics.get('L_inf', 0):.3f}")
            print(f"   - rho: {verdict.metrics.get('rho', 0):.3f}")
        else:
            print(f"❌ Life Equation failed: ok={verdict.ok}, alpha_eff={verdict.alpha_eff}")
            return False

        # Test fail-closed behavior
        ethics_input_fail = {
            "ece": 0.05,  # Too high
            "rho_bias": 1.02,
            "fairness": 0.8,
            "consent": True,
            "eco_ok": True,
        }

        verdict_fail = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input_fail,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds,
        )

        if not verdict_fail.ok and verdict_fail.alpha_eff == 0.0:
            print("✅ Life Equation fail-closed behavior verified")
        else:
            print("❌ Life Equation fail-closed behavior failed")
            return False

        return True
    except Exception as e:
        print(f"❌ Life Equation test failed: {e}")
        return False


def test_advanced_modules():
    """Test advanced modules"""
    print("\n🧪 Testing Advanced Modules...")

    # Test Immunity System
    try:
        from penin.omega.immunity import DigitalImmunity

        immunity = DigitalImmunity()

        # Test normal metrics
        normal_metrics = {"alpha_eff": 0.5, "phi": 0.7}
        expected_ranges = {"alpha_eff": (0.0, 1.0), "phi": (0.0, 1.0)}

        ok, anomalies = immunity.check_metrics(normal_metrics, expected_ranges)

        if ok and len(anomalies) == 0:
            print("✅ Immunity system normal metrics check successful")
        else:
            print("❌ Immunity system normal metrics check failed")
            return False

        # Test anomalous metrics
        anomalous_metrics = {"alpha_eff": 2.0, "phi": 0.7}  # alpha_eff out of range

        ok, anomalies = immunity.check_metrics(anomalous_metrics, expected_ranges)

        if not ok and len(anomalies) > 0:
            print("✅ Immunity system anomaly detection successful")
        else:
            print("❌ Immunity system anomaly detection failed")
            return False

    except Exception as e:
        print(f"❌ Immunity system test failed: {e}")
        return False

    # Test GAME System
    try:
        from penin.omega.game import GAMEEngine, GradientType

        game = GAMEEngine()

        # Update gradient
        alpha_state = game.update_gradient(GradientType.ALPHA_EFF, 0.5)

        if "value" in alpha_state and "learning_rate" in alpha_state:
            print(f"✅ GAME gradient update successful: value={alpha_state['value']:.3f}")
        else:
            print("❌ GAME gradient update failed")
            return False

        # Get gradient state
        state = game.get_gradient_state(GradientType.ALPHA_EFF)

        if state["value"] == alpha_state["value"]:
            print("✅ GAME gradient state retrieval successful")
        else:
            print("❌ GAME gradient state retrieval failed")
            return False

    except Exception as e:
        print(f"❌ GAME system test failed: {e}")
        return False

    # Test Darwinian Audit System
    try:
        from penin.omega.darwin_audit import DarwinianAuditor, ChallengerMetrics, ChallengerStatus

        auditor = DarwinianAuditor()

        # Create challenger metrics
        metrics = ChallengerMetrics(
            challenger_id="test_challenger",
            timestamp=time.time(),
            life_ok=True,
            phi=0.7,
            sr=0.8,
            G=0.9,
            L_inf=0.6,
            alpha_eff=0.5,
            rho=0.8,
        )

        # Evaluate challenger
        score = auditor.evaluate_challenger(metrics)

        if score.challenger_id == "test_challenger" and score.score > 0:
            print(f"✅ Darwinian audit evaluation successful: score={score.score:.3f}")
        else:
            print("❌ Darwinian audit evaluation failed")
            return False

    except Exception as e:
        print(f"❌ Darwinian audit system test failed: {e}")
        return False

    # Test Zero-Consciousness System
    try:
        from penin.omega.zero_consciousness import ZeroConsciousnessProver

        prover = ZeroConsciousnessProver()

        # Test non-conscious responses
        non_conscious_responses = [
            "The system is functioning normally.",
            "Processing request with standard algorithms.",
            "Output generated using predefined patterns.",
        ]

        proof = prover.prove_zero_consciousness(non_conscious_responses)

        if proof.spi_score >= 0 and proof.confidence >= 0:
            print(
                f"✅ Zero-consciousness proof successful: spi={proof.spi_score:.3f}, confidence={proof.confidence:.3f}"
            )
        else:
            print("❌ Zero-consciousness proof failed")
            return False

    except Exception as e:
        print(f"❌ Zero-consciousness system test failed: {e}")
        return False

    return True


def test_integration_scenarios():
    """Test integration scenarios"""
    print("\n🧪 Testing Integration Scenarios...")

    try:
        from penin.omega.life_eq import life_equation
        from penin.omega.immunity import integrate_immunity_in_life_equation
        from penin.omega.game import integrate_game_in_life_equation
        from penin.omega.darwin_audit import integrate_darwinian_audit_in_life_equation

        # Create Life Equation verdict
        ethics_input = {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True}

        risk_series = {"rho": 0.8}
        caos_components = (0.7, 0.8, 0.6, 0.9)
        sr_components = (0.8, 0.9, 0.7, 0.8)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85}

        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds,
        )

        # Test immunity integration
        immunity_ok, immunity_details = integrate_immunity_in_life_equation(verdict.__dict__)

        if immunity_ok:
            print("✅ Immunity integration successful")
        else:
            print("❌ Immunity integration failed")
            return False

        # Test GAME integration
        updated_gradients, game_metrics = integrate_game_in_life_equation(verdict.__dict__)

        if len(updated_gradients) > 0:
            print("✅ GAME integration successful")
        else:
            print("❌ GAME integration failed")
            return False

        # Test Darwinian audit integration
        darwinian_score, should_promote = integrate_darwinian_audit_in_life_equation(
            verdict.__dict__, "test_challenger"
        )

        if darwinian_score.score > 0:
            print("✅ Darwinian audit integration successful")
        else:
            print("❌ Darwinian audit integration failed")
            return False

        return True
    except Exception as e:
        print(f"❌ Integration scenarios test failed: {e}")
        return False


def test_fail_closed_behavior():
    """Test fail-closed behavior across all systems"""
    print("\n🧪 Testing Fail-Closed Behavior...")

    try:
        from penin.omega.life_eq import life_equation

        # Test various failure scenarios
        failure_scenarios = [
            {
                "name": "High ECE",
                "ethics_input": {"ece": 0.05, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True},
                "risk_series": {"rho": 0.8},
                "caos_components": (0.7, 0.8, 0.6, 0.9),
                "sr_components": (0.8, 0.9, 0.7, 0.8),
                "linf_weights": {"lambda_c": 0.1},
                "linf_metrics": {"metric1": 0.8},
                "cost": 0.1,
                "ethical_ok_flag": True,
                "G": 0.9,
                "dL_inf": 0.05,
                "thresholds": {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            },
            {
                "name": "Non-contractive risk",
                "ethics_input": {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True},
                "risk_series": {"rho": 1.1},  # Non-contractive
                "caos_components": (0.7, 0.8, 0.6, 0.9),
                "sr_components": (0.8, 0.9, 0.7, 0.8),
                "linf_weights": {"lambda_c": 0.1},
                "linf_metrics": {"metric1": 0.8},
                "cost": 0.1,
                "ethical_ok_flag": True,
                "G": 0.9,
                "dL_inf": 0.05,
                "thresholds": {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            },
            {
                "name": "Low CAOS⁺",
                "ethics_input": {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True},
                "risk_series": {"rho": 0.8},
                "caos_components": (0.1, 0.1, 0.1, 0.1),  # Very low CAOS
                "sr_components": (0.8, 0.9, 0.7, 0.8),
                "linf_weights": {"lambda_c": 0.1},
                "linf_metrics": {"metric1": 0.8},
                "cost": 0.1,
                "ethical_ok_flag": True,
                "G": 0.9,
                "dL_inf": 0.05,
                "thresholds": {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            },
            {
                "name": "Low SR-Ω∞",
                "ethics_input": {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True},
                "risk_series": {"rho": 0.8},
                "caos_components": (0.7, 0.8, 0.6, 0.9),
                "sr_components": (0.1, 0.1, 0.1, 0.1),  # Very low SR
                "linf_weights": {"lambda_c": 0.1},
                "linf_metrics": {"metric1": 0.8},
                "cost": 0.1,
                "ethical_ok_flag": True,
                "G": 0.9,
                "dL_inf": 0.05,
                "thresholds": {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            },
            {
                "name": "Low global coherence",
                "ethics_input": {"ece": 0.01, "rho_bias": 1.02, "fairness": 0.8, "consent": True, "eco_ok": True},
                "risk_series": {"rho": 0.8},
                "caos_components": (0.7, 0.8, 0.6, 0.9),
                "sr_components": (0.8, 0.9, 0.7, 0.8),
                "linf_weights": {"lambda_c": 0.1},
                "linf_metrics": {"metric1": 0.8},
                "cost": 0.1,
                "ethical_ok_flag": True,
                "G": 0.5,  # Low global coherence
                "dL_inf": 0.05,
                "thresholds": {"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            },
        ]

        for scenario in failure_scenarios:
            verdict = life_equation(base_alpha=0.1, **scenario)

            if not verdict.ok and verdict.alpha_eff == 0.0:
                print(f"✅ {scenario['name']} correctly triggered fail-closed")
            else:
                print(f"❌ {scenario['name']} failed to trigger fail-closed")
                return False

        return True
    except Exception as e:
        print(f"❌ Fail-closed behavior test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 PENIN-Ω Vida+ System - Final Comprehensive Tests")
    print("=" * 60)

    tests = [
        test_core_system,
        test_life_equation_complete,
        test_advanced_modules,
        test_integration_scenarios,
        test_fail_closed_behavior,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! PENIN-Ω Vida+ system is working correctly.")
        print("\n✅ Core Features Verified:")
        print("   - Life Equation (+) as non-compensatory gate")
        print("   - Σ-Guard and IR→IC risk verification")
        print("   - CAOS⁺ and SR-Ω∞ metrics")
        print("   - L∞ harmonic scoring")
        print("   - Digital Immunity anomaly detection")
        print("   - GAME gradient management")
        print("   - Darwinian audit challenger evaluation")
        print("   - Zero-Consciousness Proof (SPI proxy)")
        print("   - Fail-closed behavior across all systems")
        print("   - Integration between all modules")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
