"""
SR-Ω∞ Module
============

Self-Reflexive Score with non-compensatory aggregation.

SR combines:
- Autoconsciência (self-awareness)
- Ética (ethics via Σ-Guard)
- Autocorreção (self-correction)
- Metacognição (metacognition)

Uses harmonic mean or min-soft p-norm for non-compensatory behavior.
"""

import math
from dataclasses import dataclass


@dataclass
class SRConfig:
    """Configuration for SR-Ω∞ computation"""

    aggregation: str = "harmonic"  # "harmonic", "min_soft", "geometric"
    p_norm: float = -5.0  # For min-soft (negative for min behavior)
    epsilon: float = 1e-8
    weights: dict[str, float] | None = None  # Component weights
    ethics_veto: bool = True  # Ethics can veto (SR→0)


def compute_sr_omega(
    awareness: float,
    ethics_ok: bool,
    autocorrection: float,
    metacognition: float,
    config: SRConfig | None = None,
) -> tuple[float, dict]:
    """
    Compute SR-Ω∞ score with non-compensatory aggregation.

    Args:
        awareness: Self-awareness score [0,1]
        ethics_ok: Whether Σ-Guard passed
        autocorrection: Self-correction capability [0,1]
        metacognition: Metacognitive ability [0,1]
        config: Optional configuration

    Returns:
        Tuple of (sr_score, details)
    """
    if config is None:
        config = SRConfig()

    details = {
        "awareness": awareness,
        "ethics_ok": ethics_ok,
        "autocorrection": autocorrection,
        "metacognition": metacognition,
        "aggregation": config.aggregation,
    }

    # Ethics veto: if ethics failed, SR is near-zero
    if config.ethics_veto and not ethics_ok:
        details["ethics_veto"] = True
        return config.epsilon, details

    # Convert ethics to numeric
    ethics_score = 1.0 if ethics_ok else 0.5

    # Collect components
    components = {
        "awareness": max(config.epsilon, awareness),
        "ethics": ethics_score,
        "autocorrection": max(config.epsilon, autocorrection),
        "metacognition": max(config.epsilon, metacognition),
    }

    # Apply weights if provided
    if config.weights:
        for key in components:
            if key in config.weights:
                components[key] *= config.weights[key]

    # Aggregate based on method
    if config.aggregation == "harmonic":
        sr_score = harmonic_mean(list(components.values()), config.epsilon)
    elif config.aggregation == "min_soft":
        sr_score = min_soft_pnorm(list(components.values()), config.p_norm, config.epsilon)
    elif config.aggregation == "geometric":
        sr_score = geometric_mean(list(components.values()), config.epsilon)
    else:
        # Default to minimum (most conservative)
        sr_score = min(components.values())

    details["components"] = components
    details["sr_score"] = sr_score

    return sr_score, details


def harmonic_mean(values: list[float], epsilon: float = 1e-8) -> float:
    """
    Compute harmonic mean (non-compensatory).

    Args:
        values: List of values
        epsilon: Small value for stability

    Returns:
        Harmonic mean
    """
    if not values:
        return 0.0

    # Ensure all positive
    values = [max(epsilon, v) for v in values]

    # Harmonic mean
    n = len(values)
    denominator = sum(1.0 / v for v in values)

    if denominator < epsilon:
        return epsilon

    return n / denominator


def geometric_mean(values: list[float], epsilon: float = 1e-8) -> float:
    """
    Compute geometric mean.

    Args:
        values: List of values
        epsilon: Small value for stability

    Returns:
        Geometric mean
    """
    if not values:
        return 0.0

    # Ensure all positive
    values = [max(epsilon, v) for v in values]

    # Geometric mean via log-space for stability
    n = len(values)
    log_sum = sum(math.log(v) for v in values)

    return math.exp(log_sum / n)


def min_soft_pnorm(values: list[float], p: float = -5.0, epsilon: float = 1e-8) -> float:
    """
    Compute soft minimum using p-norm (p < 0).

    For p → -∞, this approaches min(values).
    For finite negative p, it's a differentiable approximation.

    Args:
        values: List of values
        p: Norm parameter (negative for min behavior)
        epsilon: Small value for stability

    Returns:
        Soft minimum
    """
    if not values:
        return 0.0

    if p >= 0:
        raise ValueError("p must be negative for min-soft behavior")

    # Ensure all positive
    values = [max(epsilon, v) for v in values]

    # Compute p-norm
    n = len(values)

    # For numerical stability with negative p
    if p < -10:
        # Close to true minimum
        return min(values)

    # p-norm computation
    sum_term = sum(v**p for v in values)

    if sum_term <= 0:
        return epsilon

    return (sum_term / n) ** (1.0 / p)


def compute_awareness_score(
    internal_state: dict[str, float],
    observation_accuracy: float = 0.8,
    introspection_depth: int = 3,
) -> float:
    """
    Compute self-awareness score based on internal state monitoring.

    Args:
        internal_state: Dict of internal metrics
        observation_accuracy: How well the system observes itself
        introspection_depth: Levels of self-reflection

    Returns:
        Awareness score [0,1]
    """
    if not internal_state:
        return 0.0

    # Base awareness from having internal metrics
    base_awareness = min(1.0, len(internal_state) / 10.0)

    # Accuracy factor
    accuracy_factor = max(0.0, min(1.0, observation_accuracy))

    # Depth factor (logarithmic)
    depth_factor = min(1.0, math.log(1 + introspection_depth) / math.log(10))

    # Combine factors (multiplicative for conservative estimate)
    awareness = base_awareness * accuracy_factor * depth_factor

    return max(0.0, min(1.0, awareness))


def compute_autocorrection_score(error_history: list[float], correction_rate: float = 0.7, window: int = 10) -> float:
    """
    Compute self-correction capability based on error reduction.

    Args:
        error_history: List of error values over time
        correction_rate: Rate of error correction
        window: Window for trend analysis

    Returns:
        Autocorrection score [0,1]
    """
    if len(error_history) < 2:
        return correction_rate  # Use base rate if no history

    # Use recent window
    recent = error_history[-window:] if len(error_history) > window else error_history

    if len(recent) < 2:
        return correction_rate

    # Check if errors are decreasing
    improvements = 0
    for i in range(1, len(recent)):
        if recent[i] < recent[i - 1]:
            improvements += 1

    # Improvement rate
    improvement_rate = improvements / (len(recent) - 1)

    # Combine with base correction rate
    score = 0.5 * correction_rate + 0.5 * improvement_rate

    return max(0.0, min(1.0, score))


def compute_metacognition_score(reasoning_depth: int, abstraction_level: float, pattern_recognition: float) -> float:
    """
    Compute metacognition score based on higher-order thinking.

    Args:
        reasoning_depth: Depth of reasoning chains
        abstraction_level: Level of abstraction [0,1]
        pattern_recognition: Pattern recognition ability [0,1]

    Returns:
        Metacognition score [0,1]
    """
    # Depth factor (logarithmic scaling)
    depth_score = min(1.0, math.log(1 + reasoning_depth) / math.log(5))

    # Abstraction (direct)
    abstraction_score = max(0.0, min(1.0, abstraction_level))

    # Pattern recognition (direct)
    pattern_score = max(0.0, min(1.0, pattern_recognition))

    # Harmonic mean for non-compensatory aggregation
    scores = [max(0.01, s) for s in [depth_score, abstraction_score, pattern_score]]
    metacognition = 3.0 / sum(1.0 / s for s in scores)

    return max(0.0, min(1.0, metacognition))


class SRTracker:
    """Track SR components over time"""

    def __init__(self, config: SRConfig | None = None):
        self.config = config or SRConfig()
        self.history = []
        self.awareness_ema = None
        self.autocorrection_ema = None
        self.metacognition_ema = None
        self.sr_ema = None
        self.alpha = 0.3  # EMA smoothing

    def update(
        self, awareness: float, ethics_ok: bool, autocorrection: float, metacognition: float
    ) -> tuple[float, float]:
        """
        Update SR tracking with new values.

        Returns:
            Tuple of (current_sr, ema_sr)
        """
        # Compute current SR
        sr_score, details = compute_sr_omega(awareness, ethics_ok, autocorrection, metacognition, self.config)

        # Update EMAs
        if self.awareness_ema is None:
            self.awareness_ema = awareness
            self.autocorrection_ema = autocorrection
            self.metacognition_ema = metacognition
            self.sr_ema = sr_score
        else:
            self.awareness_ema = self.alpha * awareness + (1 - self.alpha) * self.awareness_ema
            self.autocorrection_ema = self.alpha * autocorrection + (1 - self.alpha) * self.autocorrection_ema
            self.metacognition_ema = self.alpha * metacognition + (1 - self.alpha) * self.metacognition_ema
            self.sr_ema = self.alpha * sr_score + (1 - self.alpha) * self.sr_ema

        # Store history
        self.history.append(
            {
                "awareness": awareness,
                "ethics_ok": ethics_ok,
                "autocorrection": autocorrection,
                "metacognition": metacognition,
                "sr_score": sr_score,
                "sr_ema": self.sr_ema,
                "details": details,
            }
        )

        return sr_score, self.sr_ema

    def get_trend(self, window: int = 10) -> str:
        """Get recent trend in SR score"""
        if len(self.history) < 2:
            return "insufficient_data"

        recent = self.history[-window:] if len(self.history) > window else self.history
        sr_values = [h["sr_score"] for h in recent]

        if len(sr_values) < 2:
            return "insufficient_data"

        # Simple trend analysis
        first_half = sr_values[: len(sr_values) // 2]
        second_half = sr_values[len(sr_values) // 2 :]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first * 1.05:
            return "improving"
        elif avg_second < avg_first * 0.95:
            return "degrading"
        else:
            return "stable"
