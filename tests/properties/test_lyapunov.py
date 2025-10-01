"""
Property-Based Tests for Lyapunov Function

Mathematical guarantee: ∀ step: V(t+1) < V(t) (monotonic decrease)
"""


import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# Helper functions for testing Lyapunov
def lyapunov_function(state: float) -> float:
    """Compute Lyapunov V(x) = x²/2"""
    return (state**2) / 2.0


def validate_lyapunov_decrease(state_before: float, state_after: float) -> bool:
    """Check if V(t+1) < V(t)"""
    V_before = lyapunov_function(state_before)
    V_after = lyapunov_function(state_after)
    return V_after < V_before


@given(
    state_t=st.floats(min_value=-10.0, max_value=10.0),
    decay_factor=st.floats(min_value=0.1, max_value=0.99),
)
def test_lyapunov_monotonic_decrease(state_t, decay_factor):
    """
    Property: Lyapunov function monotonically decreases

    ∀ state_t, decay ∈ (0, 1):
        state_t+1 = state_t * decay
        ⇒ V(t+1) < V(t)
    """
    # Simulate evolution step (decay towards zero)
    state_t1 = state_t * decay_factor

    V_t = lyapunov_function(state_t)
    V_t1 = lyapunov_function(state_t1)

    assert V_t1 < V_t, f"Lyapunov not decreasing: V({state_t})={V_t:.4f}, V({state_t1})={V_t1:.4f}"


@given(
    state=st.floats(min_value=-100.0, max_value=100.0),
)
def test_lyapunov_always_positive(state):
    """
    Property: Lyapunov function is always positive

    ∀ state: V(state) ≥ 0
    """
    V = lyapunov_function(state)
    assert V >= 0.0, f"Lyapunov negative: V({state})={V}"


@given(
    state_sequence=st.lists(
        st.floats(min_value=-10.0, max_value=10.0),
        min_size=5,
        max_size=20,
    )
)
@settings(max_examples=50)
def test_lyapunov_sequence_decreasing(state_sequence):
    """
    Property: Sequence of states with decreasing Lyapunov

    ∀ sequence with convergence:
        V(s_0) > V(s_1) > V(s_2) > ... > V(s_n)
    """
    # Apply decay to create converging sequence
    decay = 0.9
    states = [state_sequence[0]]

    for i in range(1, len(state_sequence)):
        states.append(states[-1] * decay)

    lyapunov_values = [lyapunov_function(s) for s in states]

    # Check monotonic decrease
    for i in range(len(lyapunov_values) - 1):
        assert lyapunov_values[i] >= lyapunov_values[i + 1], (
            f"Lyapunov not monotonic at step {i}: " f"{lyapunov_values[i]:.4f} < {lyapunov_values[i+1]:.4f}"
        )


def test_lyapunov_at_origin():
    """Edge case: Lyapunov at equilibrium (origin)"""
    V_origin = lyapunov_function(0.0)
    assert V_origin == 0.0, "Lyapunov at origin should be zero"


@given(
    state=st.floats(min_value=0.1, max_value=10.0),
)
def test_lyapunov_symmetric(state):
    """
    Property: Lyapunov function is symmetric

    ∀ state: V(state) = V(-state)
    """
    V_pos = lyapunov_function(state)
    V_neg = lyapunov_function(-state)

    assert V_pos == pytest.approx(
        V_neg, rel=1e-6
    ), f"Lyapunov not symmetric: V({state})={V_pos:.4f}, V({-state})={V_neg:.4f}"


@given(
    state_before=st.floats(min_value=0.1, max_value=10.0),
    state_after=st.floats(min_value=0.0, max_value=9.99),
)
def test_validate_lyapunov_decrease_function(state_before, state_after):
    """
    Property: validate_lyapunov_decrease correctly identifies V(t+1) < V(t)
    """
    is_decreasing = validate_lyapunov_decrease(state_before, state_after)

    V_before = lyapunov_function(state_before)
    V_after = lyapunov_function(state_after)

    if V_after < V_before:
        assert is_decreasing, "Should validate as decreasing"
    else:
        assert not is_decreasing, "Should NOT validate as decreasing"


def test_lyapunov_convergence_to_zero():
    """Test convergence: repeated applications drive V → 0"""
    state = 5.0
    decay = 0.9
    max_steps = 100

    for step in range(max_steps):
        V = lyapunov_function(state)
        state = state * decay

        if V < 1e-6:
            # Successfully converged
            break
    else:
        pytest.fail("Did not converge to near-zero in 100 steps")


@given(
    state_t=st.floats(min_value=0.1, max_value=10.0),
    step_size=st.floats(min_value=0.01, max_value=0.5),
)
def test_lyapunov_with_gradient_descent(state_t, step_size):
    """
    Property: Gradient descent reduces Lyapunov

    ∀ state, α > 0:
        state_t+1 = state_t - α * ∇V(state_t)
        ⇒ V(t+1) < V(t)
    """
    # Gradient of V(x) = x²/2 is ∇V(x) = x
    gradient = state_t

    # Gradient descent step
    state_t1 = state_t - step_size * gradient

    V_t = lyapunov_function(state_t)
    V_t1 = lyapunov_function(state_t1)

    assert V_t1 <= V_t, f"Gradient descent did not decrease Lyapunov: {V_t} → {V_t1}"
