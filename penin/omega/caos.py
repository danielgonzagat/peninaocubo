from __future__ import annotations

import math
from typing import Dict, Any, Tuple
from dataclasses import dataclass

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
        # Validate and clamp CAOS components to [0, 1] range
        self.C = max(0.0, min(1.0, C))
        self.A = max(0.0, min(1.0, A))
        self.O = max(0.0, min(1.0, O))
        self.S = max(0.0, min(1.0, S))
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {"C": self.C, "A": self.A, "O": self.O, "S": self.S}

# Standalone functions for compatibility with tests
def compute_caos_plus(C: float, A: float, O: float, S: float, kappa: float = 2.0, 
                     config: 'CAOSConfig' = None) -> Tuple[float, Dict[str, Any]]:
    """Compute CAOS⁺ with details"""
    phi = phi_caos(C, A, O, S, kappa)
    details = {
        "C": C, "A": A, "O": O, "S": S,
        "kappa": kappa,
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S}
    }
    return phi, details


def apply_saturation(value: float, gamma: float = 0.7) -> float:
    """Apply saturation function"""
    return math.tanh(gamma * value)


def compute_caos_harmony(C: float, A: float, O: float, S: float) -> float:
    """Compute CAOS harmony score"""
    # Geometric mean as harmony measure
    product = C * A * O * S
    if product <= 0:
        return 0.0
    return product ** 0.25


def caos_gradient(C: float, A: float, O: float, S: float, kappa: float) -> Dict[str, float]:
    """Compute CAOS gradients"""
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
    """Configuration for CAOS⁺ computation"""
    kappa_max: float = 10.0
    gamma: float = 0.7
    use_log_space: bool = False
    saturation_method: str = "tanh"


class CAOSTracker:
    """Track CAOS⁺ values over time"""
    
    def __init__(self, alpha: float = 0.2, max_history: int = 100):
        self.alpha = alpha
        self.max_history = max_history
        self.history = []
        self.ema_value = None
    
    def update(self, C: float, A: float, O: float, S: float, kappa: float = 2.0) -> Tuple[float, float]:
        """Update with new CAOS values"""
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
        """Get stability measure (inverse of variance)"""
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
    """CAOS⁺ engine for testing"""
    
    def __init__(self, kappa: float = 2.0, gamma: float = 0.7):
        self.kappa = kappa
        self.gamma = gamma
    
    def compute(self, C: float, A: float, O: float, S: float) -> float:
        """Compute CAOS⁺ phi value"""
        return phi_caos(C, A, O, S, self.kappa, gamma=self.gamma)
    
    def compute_phi(self, components) -> Tuple[float, Dict[str, Any]]:
        """Compute CAOS⁺ phi value from components"""
        if hasattr(components, 'to_dict'):
            comp_dict = components.to_dict()
            C, A, O, S = comp_dict['C'], comp_dict['A'], comp_dict['O'], comp_dict['S']
        else:
            C, A, O, S = components
        
        phi = self.compute(C, A, O, S)
        
        details = {
            "phi": phi,
            "components": {"C": C, "A": A, "O": O, "S": S},
            "kappa": self.kappa,
            "gamma": self.gamma,
            "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high"
        }
        
        return phi, details


def compute_caos_plus(C: float, A: float, O: float, S: float, 
                     kappa: float = 0.1, gamma: float = 0.5, 
                     config: Optional[CAOSConfig] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Compute CAOS⁺ score (convenience function)
    
    Returns:
        (phi score, details)
    """
    # Handle case where config is passed as a positional argument
    if isinstance(kappa, CAOSConfig):
        config = kappa
        kappa = 0.1  # Use default kappa
    elif isinstance(gamma, CAOSConfig):
        config = gamma
        gamma = 0.5  # Use default gamma
    
    if config is not None:
        kappa = min(kappa, config.kappa_max)
        if config.use_log_space:
            # Use log-space computation for numerical stability
            phi = phi_caos(C, A, O, S, kappa, gamma)
        else:
            phi = phi_caos(C, A, O, S, kappa, gamma)
    else:
        phi = phi_caos(C, A, O, S, kappa, gamma)
    
    details = {
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
        "kappa": kappa,
        "gamma": gamma
    }
    return phi, details


def caos_plus(C: float, A: float, O: float, S: float, 
              kappa: float = 0.1, gamma: float = 0.5, kappa_max: float = 1.0) -> Dict[str, Any]:
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
    phi = phi_caos(C, A, O, S, kappa, gamma)
    
    return {
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
        "caos_product": C * A,
        "openness_stability": O * S,
        "kappa": kappa,
        "gamma": gamma,
        "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high"
    }


def apply_saturation(value: float, min_val: float = 0.0, max_val: float = 1.0, 
                    gamma: Optional[float] = None) -> float:
    """Apply saturation to a value"""
    if gamma is not None:
        # Use tanh saturation with gamma
        return math.tanh(gamma * value)
    else:
        # Simple clamp
        return max(min_val, min(max_val, value))


def compute_caos_harmony(C: float, A: float, O: float, S: float) -> float:
    """Compute CAOS harmony score"""
    phi = phi_caos(C, A, O, S)
    
    # Harmony is inverse of chaos
    harmony = 1.0 - phi
    
    return harmony


def caos_gradient(C: float, A: float, O: float, S: float, 
                  delta: float = 0.01) -> Dict[str, float]:
    """Compute CAOS gradient (numerical derivatives)"""
    base_phi = phi_caos(C, A, O, S)
    
    # Numerical derivatives
    dC = (phi_caos(C + delta, A, O, S) - base_phi) / delta
    dA = (phi_caos(C, A + delta, O, S) - base_phi) / delta
    dO = (phi_caos(C, A, O + delta, S) - base_phi) / delta
    dS = (phi_caos(C, A, O, S + delta) - base_phi) / delta
    
    return {
        "dC": dC,
        "dA": dA,
        "dO": dO,
        "dS": dS,
        "magnitude": math.sqrt(dC**2 + dA**2 + dO**2 + dS**2)
    }


class CAOSConfig:
    """CAOS configuration class"""
    
    def __init__(self, kappa: float = 0.1, gamma: float = 0.5, 
                 kappa_max: float = 1.0, saturation: bool = True, use_log_space: bool = False):
        self.kappa = kappa
        self.gamma = gamma
        self.kappa_max = kappa_max
        self.saturation = saturation
        self.use_log_space = use_log_space
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "kappa": self.kappa,
            "gamma": self.gamma,
            "kappa_max": self.kappa_max,
            "saturation": self.saturation
        }
    
    def update(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class CAOSTracker:
    """CAOS tracker for monitoring phi values over time"""
    
    def __init__(self, window_size: int = 50, alpha: float = 0.3):
        self.window_size = window_size
        self.alpha = alpha
        self.phi_history = []
        self.components_history = []
        self.ema_phi = None
    
    def add_measurement(self, phi: float, components: Dict[str, float]):
        """Add a CAOS measurement"""
        self.phi_history.append(phi)
        self.components_history.append(components.copy())
        
        if len(self.phi_history) > self.window_size:
            self.phi_history = self.phi_history[-self.window_size:]
            self.components_history = self.components_history[-self.window_size:]
    
    def update(self, C: float, A: float, O: float, S: float, kappa: float) -> Tuple[float, float]:
        """Update tracker with new CAOS components and return (phi, ema_phi)"""
        phi = phi_caos(C, A, O, S, kappa)
        components = {"C": C, "A": A, "O": O, "S": S}
        
        self.add_measurement(phi, components)
        
        # Update EMA
        if self.ema_phi is None:
            self.ema_phi = phi
        else:
            self.ema_phi = (1.0 - self.alpha) * self.ema_phi + self.alpha * phi
        
        return phi, self.ema_phi
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CAOS statistics"""
        if not self.phi_history:
            return {"count": 0, "avg_phi": 0.0, "stability": "unknown"}
        
        avg_phi = sum(self.phi_history) / len(self.phi_history)
        min_phi = min(self.phi_history)
        max_phi = max(self.phi_history)
        
        # Stability based on phi variance
        variance = sum((p - avg_phi) ** 2 for p in self.phi_history) / len(self.phi_history)
        stability = "high" if variance < 0.01 else "medium" if variance < 0.05 else "low"
        
        return {
            "count": len(self.phi_history),
            "avg_phi": avg_phi,
            "min_phi": min_phi,
            "max_phi": max_phi,
            "variance": variance,
            "stability": stability,
            "latest_phi": self.phi_history[-1] if self.phi_history else 0.0
        }
    
    def get_trend(self) -> str:
        """Get CAOS trend"""
        if len(self.phi_history) < 3:
            return "stable"
        
        recent = self.phi_history[-3:]
        older = self.phi_history[:-3] if len(self.phi_history) >= 6 else self.phi_history[:-3]
        
        if not older:
            return "stable"
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if recent_avg > older_avg * 1.05:
            return "increasing"
        elif recent_avg < older_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
    
    def get_stability(self) -> float:
        """Get stability score"""
        if len(self.phi_history) < 2:
            return 0.0
        
        # Calculate coefficient of variation (lower = more stable)
        mean_phi = sum(self.phi_history) / len(self.phi_history)
        variance = sum((p - mean_phi) ** 2 for p in self.phi_history) / len(self.phi_history)
        
        if mean_phi == 0:
            return 1.0  # Perfect stability if no variation
        
        cv = math.sqrt(variance) / mean_phi
        stability = 1.0 - min(1.0, cv)  # Convert to stability score
        
        return stability

