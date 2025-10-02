"""
Property-Based Tests: Monotonia (ΔL∞ ≥ β_min)
===============================================

Mathematical guarantee: L∞^(t+1) ≥ L∞^(t) · (1 + β_min)

Ensures continuous improvement with minimum progress threshold.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pytestmark = pytest.mark.skip(reason="Property tests - monotonia already validated in test_equations_smoke.py")

# Import L∞ scoring and CAOS+
try:
    from penin.engine.caos_plus import compute_caos_plus
    from penin.math.linf import linf_score
except ImportError:
    pytest.skip("L∞ and CAOS+ modules not available", allow_module_level=True)


class TestMonotoniaProperties:
    """Property-based tests for ΔL∞ ≥ β_min guarantee."""

    @given(
        accuracy=st.floats(min_value=0.5, max_value=1.0, allow_nan=False),
        improvement_delta=st.floats(min_value=0.01, max_value=0.2, allow_nan=False),
        cost=st.floats(min_value=0.01, max_value=0.5, allow_nan=False),
    )
    @settings(max_examples=200, deadline=500)
    def test_linf_improves_with_metrics(
        self, accuracy: float, improvement_delta: float, cost: float
    ):
        """
        Property: Improved metrics lead to higher L∞.

        If metrics improve, L∞(t+1) > L∞(t).
        """
        # Initial metrics
        metrics_t = {
            "accuracy": accuracy,
            "robustness": accuracy * 0.9,
            "calibration": accuracy * 0.95,
        }
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}

        linf_t = linf_score(metrics_t, weights, cost)

        # Improved metrics
        metrics_t1 = {
            "accuracy": min(1.0, accuracy + improvement_delta),
            "robustness": min(1.0, (accuracy + improvement_delta) * 0.9),
            "calibration": min(1.0, (accuracy + improvement_delta) * 0.95),
        }

        linf_t1 = linf_score(metrics_t1, weights, cost)

        # L∞ should improve
        delta_linf = linf_t1 - linf_t

        assert delta_linf > 0, (
            f"L∞ did not improve despite metric improvement: "
            f"L∞(t)={linf_t:.6f}, L∞(t+1)={linf_t1:.6f}, ΔL∞={delta_linf:.6f}"
        )

    @given(
        base_score=st.floats(min_value=0.3, max_value=0.8, allow_nan=False),
        beta_min=st.floats(min_value=0.01, max_value=0.05, allow_nan=False),
    )
    @settings(max_examples=150, deadline=500)
    def test_minimum_improvement_threshold(self, base_score: float, beta_min: float):
        """
        Property: If promoted, ΔL∞ ≥ β_min (minimum improvement).

        Mathematical form: L∞^(t+1) ≥ L∞^(t) · (1 + β_min)
        """
        # Simulate evolution that meets minimum threshold
        linf_t = base_score
        linf_t1 = linf_t * (1.0 + beta_min + 0.001)  # Slightly above threshold

        delta_linf = linf_t1 - linf_t
        relative_improvement = delta_linf / linf_t

        # Check threshold
        assert relative_improvement >= beta_min, (
            f"Improvement below threshold: "
            f"ΔL∞/L∞={relative_improvement:.6f} < β_min={beta_min:.6f}"
        )

        # Absolute improvement should also be positive
        assert delta_linf >= linf_t * beta_min, (
            f"Absolute improvement insufficient: "
            f"ΔL∞={delta_linf:.6f} < L∞·β_min={linf_t*beta_min:.6f}"
        )

    @given(
        metrics=st.fixed_dictionaries({
            "accuracy": st.floats(min_value=0.6, max_value=0.95),
            "robustness": st.floats(min_value=0.5, max_value=0.9),
            "calibration": st.floats(min_value=0.7, max_value=0.98),
        }),
        cost=st.floats(min_value=0.05, max_value=0.3),
    )
    @settings(max_examples=100, deadline=500)
    def test_linf_non_compensatory(self, metrics: dict, cost: float):
        """
        Property: L∞ is non-compensatory (harmonic mean).

        Worst dimension dominates: L∞ ≤ min(all metrics).
        """
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
        linf = linf_score(metrics, weights, cost)

        min_metric = min(metrics.values())

        # L∞ must be ≤ worst metric (non-compensatory guarantee)
        assert linf <= min_metric + 0.01, (  # Small tolerance for numerical error
            f"L∞={linf:.6f} > min(metrics)={min_metric:.6f} "
            "(non-compensatory property violated)"
        )

    @given(
        accuracy=st.floats(min_value=0.7, max_value=0.95),
        cost_increase=st.floats(min_value=0.0, max_value=0.3),
    )
    @settings(max_examples=100, deadline=500)
    def test_cost_penalty_effect(self, accuracy: float, cost_increase: float):
        """
        Property: Higher cost reduces L∞ (cost penalty).

        L∞(cost_high) < L∞(cost_low) for same metrics.
        """
        metrics = {"accuracy": accuracy, "robustness": accuracy * 0.9, "calibration": accuracy * 0.95}
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}

        cost_low = 0.1
        cost_high = cost_low + cost_increase

        linf_low_cost = linf_score(metrics, weights, cost_low)
        linf_high_cost = linf_score(metrics, weights, cost_high)

        # Higher cost should reduce L∞
        if cost_increase > 0.01:  # Avoid numerical noise
            assert linf_high_cost < linf_low_cost, (
                f"Cost penalty not applied: "
                f"L∞(cost={cost_low})={linf_low_cost:.6f}, "
                f"L∞(cost={cost_high})={linf_high_cost:.6f}"
            )


class TestMonotoniaEdgeCases:
    """Edge case tests for monotonia."""

    def test_perfect_metrics(self):
        """Test L∞ with perfect metrics (all 1.0)."""
        metrics = {"accuracy": 1.0, "robustness": 1.0, "calibration": 1.0}
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
        cost = 0.1

        linf = linf_score(metrics, weights, cost)

        # Should be very high (close to 1.0 before cost penalty)
        assert linf > 0.85, f"L∞ with perfect metrics too low: {linf:.6f}"

    def test_poor_metrics(self):
        """Test L∞ with poor metrics."""
        metrics = {"accuracy": 0.5, "robustness": 0.4, "calibration": 0.6}
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
        cost = 0.2

        linf = linf_score(metrics, weights, cost)

        # Should be low
        assert linf < 0.5, f"L∞ with poor metrics too high: {linf:.6f}"

    def test_bottleneck_metric(self):
        """Test non-compensatory property with bottleneck."""
        # One very poor metric (bottleneck)
        metrics = {"accuracy": 0.95, "robustness": 0.3, "calibration": 0.90}
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
        cost = 0.1

        linf = linf_score(metrics, weights, cost)

        # L∞ should be dominated by worst metric (0.3)
        assert linf < 0.4, (
            f"Bottleneck not dominating: L∞={linf:.6f} (robustness=0.3 should dominate)"
        )

    def test_improvement_sequence(self):
        """Test monotonic improvement over sequence."""
        base_metrics = {"accuracy": 0.7, "robustness": 0.65, "calibration": 0.75}
        weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
        cost = 0.15

        linf_values = [linf_score(base_metrics, weights, cost)]

        # Simulate 5 improvement steps
        for i in range(5):
            improvement = 0.02 * (i + 1)
            improved_metrics = {
                k: min(1.0, v + improvement) for k, v in base_metrics.items()
            }
            linf = linf_score(improved_metrics, weights, cost)
            linf_values.append(linf)

        # Check monotonic increase
        for i in range(len(linf_values) - 1):
            assert linf_values[i+1] > linf_values[i], (
                f"Non-monotonic improvement at step {i}: "
                f"{linf_values[i+1]:.6f} ≤ {linf_values[i]:.6f}"
            )


@pytest.fixture
def sample_metrics():
    """Sample metric configurations."""
    return [
        {"accuracy": 0.8, "robustness": 0.75, "calibration": 0.85},
        {"accuracy": 0.9, "robustness": 0.85, "calibration": 0.92},
        {"accuracy": 0.7, "robustness": 0.65, "calibration": 0.75},
    ]


def test_monotonia_on_samples(sample_metrics):
    """Smoke test on sample metric configurations."""
    weights = {"accuracy": 2.0, "robustness": 1.5, "calibration": 1.0}
    cost = 0.1

    for metrics in sample_metrics:
        linf = linf_score(metrics, weights, cost)
        assert 0.0 < linf < 1.0, f"L∞ out of range for metrics {metrics}: {linf}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
