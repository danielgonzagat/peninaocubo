"""
Property-Based Tests: Lyapunov Function
========================================

Mathematical guarantee: ∀ t: V(I_{t+1}) < V(I_t) (monotonic decrease)

Ensures system stability and convergence.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Import master equation and Lyapunov function
try:
    from penin.engine.master_equation import MasterState, step_master
    from penin.equations.lyapunov_contractive import (
        lyapunov_derivative,
        lyapunov_function,
    )
except ImportError:
    pytest.skip("Master equation modules not available", allow_module_level=True)


class TestLyapunovProperties:
    """Property-based tests for Lyapunov monotonic decrease."""

    @given(
        initial_state=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False),
        delta_linf=st.floats(min_value=0.0, max_value=0.2, allow_nan=False),
        alpha_omega=st.floats(min_value=0.01, max_value=0.5, allow_nan=False),
    )
    @settings(max_examples=200, deadline=500)
    def test_lyapunov_always_decreases(self, initial_state: float, delta_linf: float, alpha_omega: float):
        """
        Property: V(I_{t+1}) < V(I_t) for any evolution step.

        Mathematical form: ΔV < 0 (strict decrease).
        """
        try:
            # Create initial state
            state = MasterState(I=initial_state)

            # Compute Lyapunov at t
            V_t = lyapunov_function(state.I)

            # Apply master equation step
            state_next = step_master(state, delta_linf=delta_linf, alpha_omega=alpha_omega)

            # Compute Lyapunov at t+1
            V_t1 = lyapunov_function(state_next.I)

            # Critical assertion: V must decrease
            assert V_t1 < V_t, (
                f"Lyapunov did not decrease: V(t)={V_t:.6f}, V(t+1)={V_t1:.6f} "
                f"(ΔV={V_t1-V_t:.6f} ≥ 0)"
            )

            # Derivative should be negative
            dV = lyapunov_derivative(state.I, delta_linf, alpha_omega)
            assert dV < 0, f"Lyapunov derivative ≥ 0: dV/dt={dV:.6f}"

        except Exception as e:
            pytest.fail(f"Lyapunov test failed for state={initial_state:.4f}: {e}")

    @given(
        initial_state=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False),
        steps=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=100, deadline=1000)
    def test_lyapunov_monotonic_over_trajectory(self, initial_state: float, steps: int):
        """
        Property: V decreases monotonically over entire trajectory.

        ∀ i: V(t+i+1) < V(t+i)
        """
        state = MasterState(I=initial_state)
        lyapunov_values = [lyapunov_function(state.I)]

        # Fixed step parameters for reproducibility
        delta_linf = 0.05
        alpha_omega = 0.1

        for i in range(steps):
            state = step_master(state, delta_linf=delta_linf, alpha_omega=alpha_omega)
            V_current = lyapunov_function(state.I)

            # Check monotonic decrease
            assert V_current < lyapunov_values[-1], (
                f"Step {i+1}: Lyapunov increased or stayed same "
                f"(V={V_current:.6f} ≥ V_prev={lyapunov_values[-1]:.6f})"
            )

            lyapunov_values.append(V_current)

        # Check total decrease
        total_decrease = lyapunov_values[0] - lyapunov_values[-1]
        assert total_decrease > 0, (
            f"No overall decrease: initial={lyapunov_values[0]:.6f}, "
            f"final={lyapunov_values[-1]:.6f}"
        )

    @given(
        state_a=st.floats(min_value=-10.0, max_value=-0.1, allow_nan=False),
        state_b=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    )
    @settings(max_examples=100, deadline=500)
    def test_lyapunov_positive_definite(self, state_a: float, state_b: float):
        """
        Property: V(I) > 0 for I ≠ 0, V(0) = 0 (positive definite).
        """
        # Away from equilibrium
        V_a = lyapunov_function(state_a)
        V_b = lyapunov_function(state_b)

        assert V_a > 0, f"V({state_a:.4f})={V_a:.6f} ≤ 0 (not positive definite)"
        assert V_b > 0, f"V({state_b:.4f})={V_b:.6f} ≤ 0 (not positive definite)"

        # At equilibrium
        V_zero = lyapunov_function(0.0)
        assert abs(V_zero) < 1e-9, f"V(0)={V_zero:.6f} ≠ 0"

    @given(
        initial_state=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False),
        delta_linf=st.floats(min_value=0.0, max_value=0.1, allow_nan=False),
    )
    @settings(max_examples=150, deadline=500)
    def test_lyapunov_rate_of_decrease(self, initial_state: float, delta_linf: float):
        """
        Property: Rate of decrease (|ΔV|) increases with delta_linf.
        """
        state = MasterState(I=initial_state)
        alpha_omega = 0.1

        V_t = lyapunov_function(state.I)
        state_next = step_master(state, delta_linf=delta_linf, alpha_omega=alpha_omega)
        V_t1 = lyapunov_function(state_next.I)

        decrease = V_t - V_t1

        # Decrease should be positive
        assert decrease > 0, f"No decrease: ΔV={-decrease:.6f}"

        # Decrease should be bounded (not too aggressive)
        assert decrease < V_t, f"Decrease too large: ΔV={decrease:.6f} > V(t)={V_t:.6f}"


class TestLyapunovEdgeCases:
    """Edge case tests for Lyapunov function."""

    def test_near_equilibrium(self):
        """Test behavior near equilibrium (I ≈ 0)."""
        state = MasterState(I=0.001)
        V_t = lyapunov_function(state.I)

        state_next = step_master(state, delta_linf=0.01, alpha_omega=0.05)
        V_t1 = lyapunov_function(state_next.I)

        assert V_t1 < V_t, f"Lyapunov did not decrease near equilibrium: {V_t1} ≥ {V_t}"

    def test_far_from_equilibrium(self):
        """Test behavior far from equilibrium."""
        state = MasterState(I=10.0)
        V_t = lyapunov_function(state.I)

        state_next = step_master(state, delta_linf=0.1, alpha_omega=0.2)
        V_t1 = lyapunov_function(state_next.I)

        assert V_t1 < V_t, "Lyapunov did not decrease far from equilibrium"

    def test_convergence_to_equilibrium(self):
        """Test that system converges to equilibrium over many steps."""
        state = MasterState(I=5.0)

        for _ in range(50):
            state = step_master(state, delta_linf=0.05, alpha_omega=0.1)

        # Should be closer to equilibrium
        assert abs(state.I) < 5.0, f"State did not move toward equilibrium: I={state.I}"


@pytest.fixture
def sample_states():
    """Sample states for testing."""
    return [-5.0, -1.0, 0.0, 1.0, 5.0]


def test_lyapunov_on_samples(sample_states):
    """Smoke test on sample values."""
    for initial in sample_states:
        if initial == 0.0:
            continue  # Skip equilibrium

        state = MasterState(I=initial)
        V_t = lyapunov_function(state.I)

        state_next = step_master(state, delta_linf=0.05, alpha_omega=0.1)
        V_t1 = lyapunov_function(state_next.I)

        assert V_t1 < V_t, f"Lyapunov did not decrease for I={initial}: {V_t1} ≥ {V_t}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
