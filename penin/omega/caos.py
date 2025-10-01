from __future__ import annotations

import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

EPS = 1e-9


def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _clamp(x: float) -> float:
    """Alias for clamp01 - used by caos_kratos.py."""
    return clamp01(x)


def phi_caos(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = 0.7,
) -> float:
    """Calculate the phi_caos metric.

    Args:
        C, A, O, S: Input values (will be clamped to [0,1])
        kappa: Scaling factor (will be clamped to [1.0, kappa_max])
        kappa_max: Maximum kappa value
        gamma: Gamma parameter (will be clamped to [0.1, 2.0])

    Returns:
        float: The calculated phi_caos value in range [0,1)
    """
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
    kappa = max(1.0, min(kappa_max, kappa))
    base = 1.0 + kappa * C * A
    base = max(base, 1.0 + EPS)
    exp_term = max(0.0, min(1.0, O * S))
    log_caos = exp_term * math.log(base)
    return math.tanh(max(0.1, min(2.0, gamma)) * log_caos)


def quick_caos_phi(C: float, A: float, O: float, S: float) -> float:
    """Quick CAOS phi for testing."""
    return phi_caos(C, A, O, S)


def validate_caos_stability(C: float, A: float, O: float, S: float, **kwargs: Any) -> Dict[str, Any]:
    """Validate CAOS stability."""
    phi = phi_caos(C, A, O, S)

    return {"stable": phi < 0.8, "phi": phi, "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high"}


class CAOSComponents:
    """CAOS components for testing."""

    def __init__(self, C: float = 0.5, A: float = 0.5, O: float = 0.5, S: float = 0.5):
        # Validate and clamp CAOS components to [0, 1] range
        self.C = max(0.0, min(1.0, C))
        self.A = max(0.0, min(1.0, A))
        self.O = max(0.0, min(1.0, O))
        self.S = max(0.0, min(1.0, S))

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {"C": self.C, "A": self.A, "O": self.O, "S": self.S}


def compute_caos_plus(
    C: float, A: float, O: float, S: float, kappa: float = 2.0, config: Optional["CAOSConfig"] = None
) -> Tuple[float, Dict[str, Any]]:
    """Compute CAOS⁺ with details.
    
    This is the primary CAOS+ implementation. Returns tuple of (phi, details).
    For the alternative exponential formula CAOS⁺ = (1 + κ·C·A)^(O·S), use compute_caos_plus_exponential().
    """
    phi = phi_caos(C, A, O, S, kappa)
    details = {
        "C": C,
        "A": A,
        "O": O,
        "S": S,
        "kappa": kappa,
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
    }
    return phi, details


def compute_caos_plus_exponential(C: float, A: float, O: float, S: float, kappa: float = 20.0) -> float:
    """
    Alternative CAOS⁺ formula using pure exponential form:
    CAOS⁺ = (1 + κ·C·A)^(O·S)
    
    This is monotonic in C, A, O, S; κ shifts the base.
    Historically used in engine/caos_plus.py, now consolidated here.
    
    Args:
        C, A, O, S: CAOS components (0-1 range)
        kappa: Base amplification factor (default 20.0)
    
    Returns:
        CAOS+ score (unbounded, typically > 1.0)
    """
    expo = max(1e-6, O * S)
    return math.pow(1.0 + kappa * max(0.0, C) * max(0.0, A), expo)


def apply_saturation(value: float, gamma: float = 0.7) -> float:
    """Apply saturation function."""
    return math.tanh(gamma * value)


def compute_caos_harmony(C: float, A: float, O: float, S: float) -> float:
    """Compute CAOS harmony score."""
    # Geometric mean as harmony measure
    product = C * A * O * S
    if product <= 0:
        return 0.0
    return product**0.25


def caos_gradient(C: float, A: float, O: float, S: float, kappa: float) -> Dict[str, float]:
    """Compute CAOS gradients."""
    eps = 1e-6

    # Numerical gradients
    phi_base = phi_caos(C, A, O, S, kappa)

    dC = (phi_caos(C + eps, A, O, S, kappa) - phi_base) / eps
    dA = (phi_caos(C, A + eps, O, S, kappa) - phi_base) / eps
    dO = (phi_caos(C, A, O + eps, S, kappa) - phi_base) / eps
    dS = (phi_caos(C, A, O, S + eps, kappa) - phi_base) / eps

    return {"dC": dC, "dA": dA, "dO": dO, "dS": dS}


@dataclass
class CAOSConfig:
    """Configuration for CAOS⁺ computation."""

    kappa_max: float = 10.0
    gamma: float = 0.7
    use_log_space: bool = False
    saturation_method: str = "tanh"


class CAOSTracker:
    """Track CAOS⁺ values over time."""

    def __init__(self, alpha: float = 0.2, max_history: int = 100):
        self.alpha = alpha
        self.max_history = max_history
        self.history = []
        self.ema_value = None

    def update(self, C: float, A: float, O: float, S: float, kappa: float = 2.0) -> Tuple[float, float]:
        """Update with new CAOS values."""
        caos_val = phi_caos(C, A, O, S, kappa)

        # Update EMA
        if self.ema_value is None:
            self.ema_value = caos_val
        else:
            self.ema_value = (1.0 - self.alpha) * self.ema_value + self.alpha * caos_val

        # Update history
        self.history.append(caos_val)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return caos_val, self.ema_value

    def get_stability(self) -> float:
        """Get stability measure (inverse of variance)."""
        if len(self.history) < 2:
            return 1.0

        mean_val = sum(self.history) / len(self.history)
        variance = sum((v - mean_val) ** 2 for v in self.history) / len(self.history)

        # Return inverse of coefficient of variation
        if mean_val <= 1e-9:
            return 0.0

        cv = math.sqrt(variance) / mean_val
        return 1.0 / (1.0 + cv)


class CAOSPlusEngine:
    """CAOS⁺ engine for testing."""

    def __init__(self, kappa: float = 2.0, gamma: float = 0.7):
        self.kappa = kappa
        self.gamma = gamma

    def compute(self, C: float, A: float, O: float, S: float) -> float:
        """Compute CAOS⁺ phi value."""
        return phi_caos(C, A, O, S, self.kappa, gamma=self.gamma)

    def compute_phi(self, components) -> Tuple[float, Dict[str, Any]]:
        """Compute CAOS⁺ phi value from components."""
        if hasattr(components, "to_dict"):
            comp_dict = components.to_dict()
            C, A, O, S = comp_dict["C"], comp_dict["A"], comp_dict["O"], comp_dict["S"]
        else:
            C, A, O, S = components

        phi = self.compute(C, A, O, S)

        details = {
            "phi": phi,
            "components": {"C": C, "A": A, "O": O, "S": S},
            "kappa": self.kappa,
            "gamma": self.gamma,
            "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high",
        }

        return phi, details


def caos_plus(
    C: float | None = None,
    A: float | None = None,
    O: float | None = None,
    S: float | None = None,
    kappa: float = 2.0,
    gamma: float = 0.7,
    kappa_max: float = 10.0,
    **kwargs,
) -> Dict[str, Any]:
    """
    Computa CAOS⁺ com saturação log-space

    Args:
        C: Complexity (0-1)
        A: Adaptability (0-1)
        O: Openness (0-1)
        S: Stability (0-1)
        kappa: Chaos amplification factor (0-1)
        gamma: Saturation parameter (0-1)
        kappa_max: Maximum kappa for saturation

    Returns:
        Dict com phi, components e detalhes
    """
    # Accept alternative keyword names (coherence, awareness, openness, stability)
    if C is None and "coherence" in kwargs:
        C = kwargs["coherence"]
    if A is None and "awareness" in kwargs:
        A = kwargs["awareness"]
    if O is None and "openness" in kwargs:
        O = kwargs["openness"]
    if S is None and "stability" in kwargs:
        S = kwargs["stability"]

    # Default values if still None
    C = C if C is not None else 0.5
    A = A if A is not None else 0.5
    O = O if O is not None else 0.5
    S = S if S is not None else 0.5

    phi = phi_caos(C, A, O, S, kappa=kappa, kappa_max=kappa_max, gamma=gamma)

    return {
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
        "caos_product": C * A,
        "openness_stability": O * S,
        "kappa": kappa,
        "gamma": gamma,
        "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high",
    }
