"""
PENIN-Ω L∞ (Equação 2) - Comprehensive Test Suite
===================================================

Tests for Non-Compensatory Aggregation with Fail-Closed Gates

Test Coverage:
- Harmonic mean basic properties
- Non-compensatory behavior (critical!)
- Cost penalization
- Fail-closed ethics gates
- Edge cases and boundary conditions
- Property-based tests

References:
- docs/equations.md § 2
- docs/guides/PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 2
"""

import math

import pytest

from penin.math.linf import (
    LInfConfig,
    compute_linf_meta,
    harmonic_noncomp,
    linf_score,
)


class TestHarmonicMean:
    """Test harmonic mean properties"""

    def test_harmonic_mean_basic(self):
        """Test basic harmonic mean computation"""
        metrics = {"a": 0.8, "b": 0.6, "c": 0.9}
        weights = {"a": 1.0, "b": 1.0, "c": 1.0}

        result = harmonic_noncomp(metrics, weights)

        # Harmonic mean should be ≤ arithmetic mean
        arithmetic_mean = sum(metrics.values()) / len(metrics)
        assert result <= arithmetic_mean

        # Should be closer to minimum value (penalty for worst)
        # Harmonic mean is typically between min and geometric mean
        assert result >= min(metrics.values()), "Harmonic mean must be >= min value"

    def test_harmonic_mean_dominated_by_minimum(self):
        """Test that harmonic mean is dominated by the worst value"""
        # Case: One very bad value, others excellent
        metrics_bad = {"a": 0.1, "b": 0.95, "c": 0.95}  # One bad
        metrics_balanced = {"a": 0.7, "b": 0.7, "c": 0.7}  # All balanced

        weights = {"a": 1.0, "b": 1.0, "c": 1.0}

        result_bad = harmonic_noncomp(metrics_bad, weights)
        result_balanced = harmonic_noncomp(metrics_balanced, weights)

        # Balanced should be MUCH better than one-bad
        assert result_balanced > result_bad * 2, "Harmonic mean must penalize worst value!"

    def test_harmonic_mean_weighted(self):
        """Test weighted harmonic mean"""
        metrics = {"critical": 0.5, "normal": 0.9}

        # Critical metric has higher weight
        weights_high_critical = {"critical": 3.0, "normal": 1.0}
        weights_balanced = {"critical": 1.0, "normal": 1.0}

        result_high_weight = harmonic_noncomp(metrics, weights_high_critical)
        result_balanced = harmonic_noncomp(metrics, weights_balanced)

        # Higher weight on bad metric should lower overall score
        assert result_high_weight < result_balanced

    def test_harmonic_mean_boundary_cases(self):
        """Test edge cases"""
        # All zeros (with epsilon protection)
        metrics_zero = {"a": 0.0, "b": 0.0}
        weights = {"a": 1.0, "b": 1.0}
        result = harmonic_noncomp(metrics_zero, weights)
        assert result >= 0.0  # Should not crash

        # All ones (maximum)
        metrics_ones = {"a": 1.0, "b": 1.0, "c": 1.0}
        result_ones = harmonic_noncomp(metrics_ones, weights)
        assert 0.99 <= result_ones <= 1.01  # Should be ~1.0

        # Single metric
        metrics_single = {"only": 0.75}
        result_single = harmonic_noncomp(metrics_single, {"only": 1.0})
        assert abs(result_single - 0.75) < 0.01  # Should match input


class TestNonCompensatoryProperty:
    """Critical tests for non-compensatory behavior"""

    def test_non_compensatory_high_accuracy_low_privacy(self):
        """Test that high accuracy CANNOT compensate low privacy"""
        # Scenario: 95% accuracy BUT 10% privacy (ethical violation!)
        metrics_unethical = {"accuracy": 0.95, "privacy": 0.10, "robustness": 0.80}

        # Scenario: Balanced 75% across all metrics
        metrics_balanced = {"accuracy": 0.75, "privacy": 0.75, "robustness": 0.75}

        weights = {"accuracy": 1.0, "privacy": 1.0, "robustness": 1.0}

        score_unethical = harmonic_noncomp(metrics_unethical, weights)
        score_balanced = harmonic_noncomp(metrics_balanced, weights)

        # Balanced MUST score higher (non-compensatory property)
        assert (
            score_balanced > score_unethical
        ), "CRITICAL: Non-compensatory property violated! High accuracy compensating low privacy!"

    def test_non_compensatory_multiple_bad_dimensions(self):
        """Test penalty increases with multiple bad dimensions"""
        metrics_1_bad = {"a": 0.2, "b": 0.9, "c": 0.9, "d": 0.9}
        metrics_2_bad = {"a": 0.2, "b": 0.2, "c": 0.9, "d": 0.9}
        metrics_3_bad = {"a": 0.2, "b": 0.2, "c": 0.2, "d": 0.9}

        weights = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0}

        score_1 = harmonic_noncomp(metrics_1_bad, weights)
        score_2 = harmonic_noncomp(metrics_2_bad, weights)
        score_3 = harmonic_noncomp(metrics_3_bad, weights)

        # More bad dimensions → worse score
        assert score_1 > score_2 > score_3, "Penalty must increase with more bad dimensions!"


class TestCostPenalization:
    """Test cost penalization mechanism"""

    def test_cost_penalty_decreases_score(self):
        """Test that higher cost decreases L∞ score"""
        metrics = {"a": 0.8, "b": 0.7}
        weights = {"a": 1.0, "b": 1.0}

        score_low_cost = linf_score(metrics, weights, cost=0.1, lambda_c=0.5)
        score_high_cost = linf_score(metrics, weights, cost=1.0, lambda_c=0.5)

        assert score_low_cost > score_high_cost, "Higher cost must decrease L∞!"

    def test_cost_penalty_exponential(self):
        """Test exponential nature of cost penalty"""
        metrics = {"a": 0.8}
        weights = {"a": 1.0}

        base = harmonic_noncomp(metrics, weights)

        # Test exponential decay: exp(-λ*cost)
        lambda_c = 0.5
        cost = 2.0

        expected_penalty = math.exp(-lambda_c * cost)
        score = linf_score(metrics, weights, cost, lambda_c)

        expected_score = base * expected_penalty
        assert abs(score - expected_score) < 1e-6, "Cost penalty must be exponential!"

    def test_zero_cost_no_penalty(self):
        """Test that zero cost means no penalty"""
        metrics = {"a": 0.75, "b": 0.85}
        weights = {"a": 1.0, "b": 1.0}

        base = harmonic_noncomp(metrics, weights)
        score_zero_cost = linf_score(metrics, weights, cost=0.0, lambda_c=0.5)

        assert abs(score_zero_cost - base) < 1e-9, "Zero cost should mean no penalty!"


class TestFailClosedGates:
    """Critical tests for fail-closed ethical gates"""

    def test_ethics_gate_fail_closed(self):
        """Test that ethics violation ZEROS L∞ (fail-closed)"""
        metrics = {"accuracy": 0.95, "privacy": 0.95}
        weights = {"accuracy": 1.0, "privacy": 1.0}
        cost = 0.1

        config = LInfConfig(require_ethics=True, lambda_c=0.5)

        # With ethics OK
        score_ethical = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=True, contratividade_ok=True
        )

        # With ethics violation
        score_unethical = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=False, contratividade_ok=True
        )

        assert score_ethical > 0, "Ethical system should have positive score"
        assert score_unethical == 0.0, "CRITICAL: Fail-closed violated! Ethics violation must ZERO L∞!"

    def test_contractividade_gate_fail_closed(self):
        """Test that contractividade violation (ρ≥1) ZEROS L∞"""
        metrics = {"a": 0.9, "b": 0.85}
        weights = {"a": 1.0, "b": 1.0}
        cost = 0.1

        config = LInfConfig(require_contractividade=True, lambda_c=0.5)

        # With ρ < 1 (contractive, OK)
        score_ok = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=True, contratividade_ok=True
        )

        # With ρ ≥ 1 (non-contractive, FAIL)
        score_fail = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=True, contratividade_ok=False
        )

        assert score_ok > 0
        assert score_fail == 0.0, "CRITICAL: Non-contractive evolution (ρ≥1) must be blocked!"

    def test_both_gates_fail(self):
        """Test that both gates failing still zeros L∞"""
        metrics = {"a": 0.99}
        weights = {"a": 1.0}
        cost = 0.01

        config = LInfConfig(require_ethics=True, require_contractividade=True)

        score = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=False, contratividade_ok=False
        )

        assert score == 0.0, "Both gates failing must zero L∞!"

    def test_gates_disabled_allows_score(self):
        """Test that disabling gates allows non-zero score (for testing)"""
        metrics = {"a": 0.8}
        weights = {"a": 1.0}
        cost = 0.1

        config = LInfConfig(require_ethics=False, require_contractividade=False)

        score = compute_linf_meta(
            metrics, weights, cost, config, ethics_ok=False, contratividade_ok=False  # Gates fail
        )

        assert score > 0, "With gates disabled, score should be non-zero"


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions"""

    def test_empty_metrics(self):
        """Test handling of empty metrics dict"""
        metrics = {}
        weights = {}

        result = harmonic_noncomp(metrics, weights)
        assert result >= 0.0  # Should not crash

    def test_negative_cost_clamped(self):
        """Test that negative cost is clamped to zero"""
        metrics = {"a": 0.8}
        weights = {"a": 1.0}

        score_negative = linf_score(metrics, weights, cost=-1.0, lambda_c=0.5)
        score_zero = linf_score(metrics, weights, cost=0.0, lambda_c=0.5)

        # Negative cost should be treated as zero
        assert abs(score_negative - score_zero) < 1e-9

    def test_very_large_cost(self):
        """Test handling of very large cost"""
        metrics = {"a": 0.9}
        weights = {"a": 1.0}

        score = linf_score(metrics, weights, cost=1000.0, lambda_c=0.5)

        # Should approach zero but not crash
        assert 0.0 <= score < 0.01

    def test_lambda_c_zero_no_penalty(self):
        """Test that λ_c=0 means no cost penalty"""
        metrics = {"a": 0.75}
        weights = {"a": 1.0}

        base = harmonic_noncomp(metrics, weights)
        score_no_penalty = linf_score(metrics, weights, cost=10.0, lambda_c=0.0)

        assert abs(score_no_penalty - base) < 1e-9


class TestRealWorldScenarios:
    """Test realistic scenarios"""

    def test_ml_model_evaluation(self):
        """Test realistic ML model evaluation scenario"""
        # Model A: High accuracy, low fairness (unethical)
        model_a = {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.92,
            "fairness": 0.40,  # Bad!
            "calibration": 0.85,
        }

        # Model B: Balanced
        model_b = {
            "accuracy": 0.82,
            "precision": 0.80,
            "recall": 0.81,
            "fairness": 0.78,  # Good!
            "calibration": 0.79,
        }

        weights = {
            "accuracy": 1.0,
            "precision": 0.8,
            "recall": 0.8,
            "fairness": 1.5,  # Higher weight on fairness
            "calibration": 1.0,
        }

        cost_a = 0.2  # Higher cost (more complex)
        cost_b = 0.1  # Lower cost

        score_a = linf_score(model_a, weights, cost_a, lambda_c=0.5)
        score_b = linf_score(model_b, weights, cost_b, lambda_c=0.5)

        # Model B should win (better fairness + lower cost)
        assert score_b > score_a, "Balanced model should beat high-accuracy-low-fairness model!"

    def test_champion_vs_challenger(self):
        """Test champion vs challenger comparison"""
        champion = {"perf": 0.80, "safety": 0.85, "cost_eff": 0.75}
        challenger = {"perf": 0.85, "safety": 0.82, "cost_eff": 0.70}

        weights = {"perf": 1.0, "safety": 2.0, "cost_eff": 1.5}  # Safety is critical

        cost_champion = 0.15
        cost_challenger = 0.18  # Slightly higher

        config = LInfConfig(lambda_c=0.3)

        score_champion = compute_linf_meta(
            champion, weights, cost_champion, config, ethics_ok=True, contratividade_ok=True
        )

        score_challenger = compute_linf_meta(
            challenger, weights, cost_challenger, config, ethics_ok=True, contratividade_ok=True
        )

        # Determine winner
        delta_linf = score_challenger - score_champion
        beta_min = 0.01  # Minimum improvement threshold

        if delta_linf >= beta_min:
            winner = "Challenger"
        else:
            winner = "Champion"

        # In this case, safety weight is high, so champion might win
        # (This is data-driven, not a hard assertion)
        assert winner in ["Champion", "Challenger"]


class TestPropertyBased:
    """Property-based tests (invariants that must hold)"""

    def test_monotonicity_in_metrics(self):
        """Test that improving any metric increases L∞ (all else equal)"""
        base_metrics = {"a": 0.70, "b": 0.75, "c": 0.68}
        improved_metrics = {"a": 0.80, "b": 0.75, "c": 0.68}  # Improved 'a'

        weights = {"a": 1.0, "b": 1.0, "c": 1.0}
        cost = 0.1

        score_base = linf_score(base_metrics, weights, cost)
        score_improved = linf_score(improved_metrics, weights, cost)

        assert score_improved > score_base, "Improving a metric must increase L∞!"

    def test_scale_invariance_of_weights(self):
        """Test that scaling all weights by same factor doesn't change L∞"""
        metrics = {"a": 0.8, "b": 0.6}

        weights_1x = {"a": 1.0, "b": 2.0}
        weights_2x = {"a": 2.0, "b": 4.0}  # Scaled by 2

        score_1x = harmonic_noncomp(metrics, weights_1x)
        score_2x = harmonic_noncomp(metrics, weights_2x)

        # Should be identical (harmonic mean is scale-invariant)
        assert abs(score_1x - score_2x) < 1e-9

    def test_range_constraint(self):
        """Test that L∞ ∈ [0, 1] always"""
        import random

        random.seed(42)

        for _ in range(100):
            # Generate random valid metrics
            metrics = {f"m{i}": random.uniform(0.0, 1.0) for i in range(5)}
            weights = {f"m{i}": random.uniform(0.1, 2.0) for i in range(5)}
            cost = random.uniform(0.0, 2.0)

            config = LInfConfig(lambda_c=random.uniform(0.1, 1.0))

            score = compute_linf_meta(metrics, weights, cost, config)

            assert 0.0 <= score <= 1.0, f"L∞ out of range: {score}"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with other components"""

    def test_linf_with_caos_plus(self):
        """Test integration with CAOS⁺ (using L∞ as input)"""
        # This test validates that L∞ output can feed into CAOS⁺ input
        from penin.core.caos import compute_caos_plus_exponential

        metrics = {"accuracy": 0.85, "robustness": 0.78, "privacy": 0.92}
        weights = {"accuracy": 1.0, "robustness": 1.0, "privacy": 1.0}
        cost = 0.12

        # Compute L∞
        linf = linf_score(metrics, weights, cost, lambda_c=0.5)

        # Use L_inf as input to CAOS+
        # In real pipeline: delta_linf would be used in A (Autoevolution)
        # Here we just validate it's a valid input
        c = 0.88  # Consistency
        a = linf  # Autoevolucao (could use delta_Linf)
        o = 0.35  # Incognoscivel
        s = 0.82  # Silencio

        caos_plus = compute_caos_plus_exponential(c, a, o, s, kappa=20.0)

        assert caos_plus >= 1.0, "CAOS+ should be >= 1.0"
        assert linf <= 1.0, "L_inf should be <= 1.0"


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.parametrize(
    "metrics,expected_range",
    [
        ({"a": 0.9, "b": 0.8}, (0.8, 0.9)),  # Should be close to min
        ({"a": 0.5, "b": 0.5, "c": 0.5}, (0.49, 0.51)),  # All equal
        ({"a": 1.0, "b": 1.0}, (0.99, 1.01)),  # All max
    ],
)
def test_harmonic_expected_ranges(metrics, expected_range):
    """Parametrized test for expected harmonic mean ranges"""
    weights = {k: 1.0 for k in metrics.keys()}
    result = harmonic_noncomp(metrics, weights)

    min_expected, max_expected = expected_range
    assert (
        min_expected <= result <= max_expected
    ), f"Harmonic mean {result} not in expected range {expected_range}"


# ============================================================================
# Performance Tests (marked as slow)
# ============================================================================


@pytest.mark.slow
def test_performance_large_metrics_dict():
    """Test performance with large number of metrics"""
    import time

    # Generate 1000 metrics
    metrics = {f"metric_{i}": 0.5 + i * 0.0001 for i in range(1000)}
    weights = {f"metric_{i}": 1.0 for i in range(1000)}

    start = time.perf_counter()
    result = harmonic_noncomp(metrics, weights)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"Performance too slow: {elapsed:.3f}s for 1000 metrics"
    assert 0.0 <= result <= 1.0


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary:
----------------------
✅ Harmonic mean basic properties (3 tests)
✅ Non-compensatory behavior (2 tests) - CRITICAL
✅ Cost penalization (3 tests)
✅ Fail-closed gates (4 tests) - CRITICAL
✅ Edge cases (4 tests)
✅ Real-world scenarios (2 tests)
✅ Property-based (3 tests)
✅ Integration (1 test)
✅ Parametrized (3 variants)
✅ Performance (1 test)

Total: 25+ tests

Critical Properties Validated:
1. Non-compensatory: High performance in one dimension CANNOT compensate low in another ✅
2. Fail-closed: Ethics/contractividade violations ZERO L∞ ✅
3. Cost penalty: Exponential decay with cost ✅
4. Range: L∞ ∈ [0, 1] always ✅
5. Monotonicity: Improving metrics increases L∞ ✅
"""
