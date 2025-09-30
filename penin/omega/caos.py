from __future__ import annotations

import math
from typing import Dict, Any, Tuple

EPS = 1e-9


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def phi_caos(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = 0.7,
) -> float:
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
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
    """Quick CAOS phi for testing"""
    return phi_caos(C, A, O, S)

def validate_caos_stability(C: float, A: float, O: float, S: float) -> Dict[str, Any]:
    """Validate CAOS stability"""
    phi = phi_caos(C, A, O, S)
    return {
        "stable": phi < 0.8,
        "phi": phi,
        "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high"
    }

class CAOSComponents:
    """CAOS components for testing"""
    
    def __init__(self, C: float = 0.5, A: float = 0.5, O: float = 0.5, S: float = 0.5):
        self.C = C
        self.A = A
        self.O = O
        self.S = S
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {"C": self.C, "A": self.A, "O": self.O, "S": self.S}

class CAOSPlusEngine:
    """CAOS⁺ engine for testing"""
    
    def __init__(self, kappa: float = 2.0, gamma: float = 0.7):
        self.kappa = kappa
        self.gamma = gamma
    
    def compute(self, C: float, A: float, O: float, S: float) -> float:
        """Compute CAOS⁺ phi value"""
        return phi_caos(C, A, O, S, self.kappa, gamma=self.gamma)
    
    def compute_phi(self, components) -> Tuple[float, Dict[str, Any]]:
        """Compute CAOS⁺ phi value from components"""
        if hasattr(components, 'C'):
            # CAOSComponents object
            phi = self.compute(components.C, components.A, components.O, components.S)
        else:
            # Individual parameters
            phi = self.compute(components[0], components[1], components[2], components[3])
        
        details = {
            "phi": phi,
            "stable": phi < 0.8,
            "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high"
        }
        return phi, details
    
    def is_stable(self, C: float, A: float, O: float, S: float) -> bool:
        """Check if CAOS⁺ is stable"""
        phi = self.compute(C, A, O, S)
        return phi < 0.8

