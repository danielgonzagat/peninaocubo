"""
CAOS⁺ Module
============

Implements φ(CAOS⁺) with stable computation using log-space and tanh saturation.

CAOS⁺ = (1 + κ·C·A)^(O·S)

Where:
- C: Coherence [0,1]
- A: Awareness [0,1]
- O: Openness to the unknown [0,1]
- S: Silence/listening [0,1]
- κ: Amplification factor [1, κ_max]
- φ: Saturation function (tanh)

All computations use log-space for numerical stability.
"""

import math
from dataclasses import dataclass


@dataclass
class CAOSConfig:
    """Configuration for CAOS⁺ computation"""

    kappa: float = 2.0  # Amplification factor
    kappa_max: float = 10.0  # Maximum κ
    gamma: float = 0.5  # Saturation steepness
    epsilon: float = 1e-8  # Numerical stability
    use_log_space: bool = True  # Use log-space computation
    clamp_inputs: bool = True  # Clamp inputs to [0,1]


def compute_caos_plus(
    C: float, A: float, O: float, S: float, kappa: float, config: CAOSConfig | None = None
) -> tuple[float, dict]:
    """
    Compute CAOS⁺ with numerical stability.

    Args:
        C: Coherence [0,1]
        A: Awareness [0,1]
        O: Openness [0,1]
        S: Silence [0,1]
        kappa: Amplification factor
        config: Optional configuration

    Returns:
        Tuple of (caos_plus_value, details_dict)
    """
    if config is None:
        config = CAOSConfig()

    # Clamp inputs if configured
    if config.clamp_inputs:
        C = max(0.0, min(1.0, C))
        A = max(0.0, min(1.0, A))
        O = max(0.0, min(1.0, O))
        S = max(0.0, min(1.0, S))
        kappa = max(1.0, min(config.kappa_max, kappa))

    details = {
        "C": C,
        "A": A,
        "O": O,
        "S": S,
        "kappa": kappa,
        "method": "log_space" if config.use_log_space else "direct",
    }

    # Compute base term
    base = 1.0 + kappa * C * A
    exponent = O * S

    # Prevent edge cases
    if base <= 0:
        base = config.epsilon
    exponent = max(exponent, 0)

    # Compute CAOS⁺
    if config.use_log_space:
        # Log-space computation for stability
        try:
            log_caos = exponent * math.log(base)
            # Prevent overflow
            log_caos = min(log_caos, 100)  # exp(100) is huge enough
            caos_raw = math.exp(log_caos)
        except (ValueError, OverflowError):
            caos_raw = 1.0
            details["computation_error"] = True
    else:
        # Direct computation
        try:
            caos_raw = base**exponent
        except (ValueError, OverflowError):
            caos_raw = 1.0
            details["computation_error"] = True

    details["caos_raw"] = caos_raw

    # Apply saturation function φ
    phi_caos = apply_saturation(caos_raw, config.gamma)

    details["phi_caos"] = phi_caos
    details["gamma"] = config.gamma

    return phi_caos, details


def apply_saturation(value: float, gamma: float = 0.5) -> float:
    """
    Apply tanh saturation function.

    φ(x) = tanh(γ * log(x))

    Args:
        value: Input value
        gamma: Saturation steepness

    Returns:
        Saturated value in [0,1)
    """
    if value <= 0:
        return 0.0

    try:
        # Use log for better scaling
        log_val = math.log(value)
        # Apply tanh with gamma scaling
        saturated = math.tanh(gamma * log_val)
        # Ensure positive output
        return max(0.0, saturated)
    except (ValueError, OverflowError):
        # Fallback for edge cases
        return min(0.999, value / (1.0 + value))


def compute_caos_harmony(C: float, A: float, O: float, S: float, epsilon: float = 1e-8) -> float:
    """
    Compute CAOS harmony using harmonic mean.

    Non-compensatory aggregation of CAOS components.

    Args:
        C, A, O, S: CAOS components [0,1]
        epsilon: Small value for stability

    Returns:
        Harmonic mean of CAOS components
    """
    # Ensure all values are positive
    values = [max(epsilon, v) for v in [C, A, O, S]]

    # Harmonic mean
    denominator = sum(1.0 / v for v in values)
    if denominator < epsilon:
        return epsilon

    return 4.0 / denominator


def caos_gradient(C: float, A: float, O: float, S: float, kappa: float, delta: float = 0.001) -> dict[str, float]:
    """
    Compute numerical gradient of CAOS⁺ with respect to each component.

    Useful for understanding sensitivity and tuning.

    Args:
        C, A, O, S, kappa: CAOS parameters
        delta: Small perturbation for numerical gradient

    Returns:
        Dict with gradients for each component
    """
    base_caos, _ = compute_caos_plus(C, A, O, S, kappa)

    gradients = {}

    # Gradient w.r.t C
    caos_c_plus, _ = compute_caos_plus(C + delta, A, O, S, kappa)
    gradients["dC"] = (caos_c_plus - base_caos) / delta

    # Gradient w.r.t A
    caos_a_plus, _ = compute_caos_plus(C, A + delta, O, S, kappa)
    gradients["dA"] = (caos_a_plus - base_caos) / delta

    # Gradient w.r.t O
    caos_o_plus, _ = compute_caos_plus(C, A, O + delta, S, kappa)
    gradients["dO"] = (caos_o_plus - base_caos) / delta

    # Gradient w.r.t S
    caos_s_plus, _ = compute_caos_plus(C, A, O, S + delta, kappa)
    gradients["dS"] = (caos_s_plus - base_caos) / delta

    # Gradient w.r.t kappa
    caos_k_plus, _ = compute_caos_plus(C, A, O, S, kappa + delta)
    gradients["dkappa"] = (caos_k_plus - base_caos) / delta

    return gradients


class CAOSTracker:
    """Track CAOS components over time with EMA smoothing"""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.C_ema = None
        self.A_ema = None
        self.O_ema = None
        self.S_ema = None
        self.caos_ema = None
        self.history = []

    def update(self, C: float, A: float, O: float, S: float, kappa: float = 2.0):
        """Update CAOS tracking with new values"""
        # Update EMAs
        if self.C_ema is None:
            self.C_ema = C
            self.A_ema = A
            self.O_ema = O
            self.S_ema = S
        else:
            self.C_ema = self.alpha * C + (1 - self.alpha) * self.C_ema
            self.A_ema = self.alpha * A + (1 - self.alpha) * self.A_ema
            self.O_ema = self.alpha * O + (1 - self.alpha) * self.O_ema
            self.S_ema = self.alpha * S + (1 - self.alpha) * self.S_ema

        # Compute CAOS⁺ with EMA values
        caos_value, details = compute_caos_plus(self.C_ema, self.A_ema, self.O_ema, self.S_ema, kappa)

        if self.caos_ema is None:
            self.caos_ema = caos_value
        else:
            self.caos_ema = self.alpha * caos_value + (1 - self.alpha) * self.caos_ema

        # Store in history
        self.history.append(
            {
                "C": C,
                "A": A,
                "O": O,
                "S": S,
                "C_ema": self.C_ema,
                "A_ema": self.A_ema,
                "O_ema": self.O_ema,
                "S_ema": self.S_ema,
                "caos": caos_value,
                "caos_ema": self.caos_ema,
                "details": details,
            }
        )

        return caos_value, self.caos_ema

    def get_stability(self, window: int = 10) -> float:
        """
        Compute stability metric based on recent variance.

        Returns value in [0,1] where 1 is most stable.
        """
        if len(self.history) < 2:
            return 1.0

        recent = self.history[-window:] if len(self.history) > window else self.history
        caos_values = [h["caos"] for h in recent]

        if len(caos_values) < 2:
            return 1.0

        # Compute variance
        mean = sum(caos_values) / len(caos_values)
        variance = sum((v - mean) ** 2 for v in caos_values) / len(caos_values)

        # Convert to stability score (lower variance = higher stability)
        # Using exponential decay
        stability = math.exp(-variance * 10)

        return max(0.0, min(1.0, stability))
