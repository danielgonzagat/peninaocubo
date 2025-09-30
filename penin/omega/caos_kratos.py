"""
CAOS-KRATOS - Exploration Mode
==============================

Implements CAOS-KRATOS as an enhanced exploration mode that reinforces
the impact of (O×S) while maintaining saturation and stability.
"""

import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Import base CAOS
from .caos import phi_caos, clamp01


@dataclass
class KratosConfig:
    """Configuration for CAOS-KRATOS"""
    exploration_factor: float = 2.0
    max_exploration: float = 5.0
    saturation_threshold: float = 0.8
    stability_factor: float = 0.9


def phi_kratos(C: float, A: float, O: float, S: float, 
               exploration_factor: float = 2.0,
               kappa: float = 20.0,
               gamma: float = 0.7,
               kappa_max: float = 100.0,
               **kwargs) -> float:
    """
    CAOS-KRATOS: Enhanced exploration mode
    
    Reinforces impact of (O×S) while maintaining saturation:
    - O^exploration_factor and S^exploration_factor
    - Maintains numerical stability
    - Provides controlled exploration boost
    
    Args:
        C, A, O, S: CAOS components
        exploration_factor: Factor to boost O and S (≥1.0)
        kappa, gamma, kappa_max: Standard CAOS parameters
        
    Returns:
        Enhanced phi value
    """
    # Clamp inputs
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
    
    # Apply exploration factor to O and S
    O_enhanced = O ** exploration_factor
    S_enhanced = S ** exploration_factor
    
    # Clamp enhanced values to prevent explosion
    O_enhanced = clamp01(O_enhanced)
    S_enhanced = clamp01(S_enhanced)
    
    # Use enhanced values in standard CAOS formula
    return phi_caos(C, A, O_enhanced, S_enhanced, kappa, kappa_max, gamma)


def phi_kratos_adaptive(C: float, A: float, O: float, S: float,
                       base_exploration: float = 2.0,
                       adaptive_threshold: float = 0.5,
                       **kwargs) -> Tuple[float, Dict[str, Any]]:
    """
    Adaptive CAOS-KRATOS with dynamic exploration factor
    
    Args:
        C, A, O, S: CAOS components
        base_exploration: Base exploration factor
        adaptive_threshold: Threshold for adaptive scaling
        
    Returns:
        (phi_value, details_dict)
    """
    # Compute base phi for comparison
    phi_base = phi_caos(C, A, O, S)
    
    # Adaptive exploration factor based on current state
    if phi_base < adaptive_threshold:
        # Low phi: increase exploration
        exploration_factor = base_exploration * 1.5
    else:
        # High phi: moderate exploration
        exploration_factor = base_exploration
    
    # Apply KRATOS enhancement
    phi_kratos = phi_kratos(C, A, O, S, exploration_factor, **kwargs)
    
    # Compute enhancement ratio
    enhancement_ratio = phi_kratos / max(phi_base, 1e-9)
    
    details = {
        "phi_base": phi_base,
        "phi_kratos": phi_kratos,
        "exploration_factor": exploration_factor,
        "enhancement_ratio": enhancement_ratio,
        "O_enhanced": O ** exploration_factor,
        "S_enhanced": S ** exploration_factor,
        "adaptive_mode": phi_base < adaptive_threshold
    }
    
    return phi_kratos, details


class KratosEngine:
    """CAOS-KRATOS engine with exploration management"""
    
    def __init__(self, config: KratosConfig = None):
        self.config = config or KratosConfig()
        self.exploration_history = []
        self.stability_tracker = []
        
    def compute_kratos(self, C: float, A: float, O: float, S: float,
                       enable_exploration: bool = True) -> Tuple[float, Dict[str, Any]]:
        """
        Compute CAOS-KRATOS with exploration management
        
        Args:
            C, A, O, S: CAOS components
            enable_exploration: Whether to enable KRATOS enhancement
            
        Returns:
            (phi_value, computation_details)
        """
        if not enable_exploration:
            # Standard CAOS
            phi = phi_caos(C, A, O, S)
            return phi, {"mode": "standard", "phi": phi}
        
        # KRATOS exploration
        exploration_factor = self.config.exploration_factor
        
        # Check stability constraints
        if self._is_exploration_safe(C, A, O, S, exploration_factor):
            phi, details = phi_kratos_adaptive(C, A, O, S, exploration_factor)
            mode = "kratos"
        else:
            # Fall back to standard CAOS
            phi = phi_caos(C, A, O, S)
            details = {"mode": "standard_fallback", "phi": phi}
            mode = "standard"
        
        # Track exploration
        self.exploration_history.append({
            "timestamp": time.time(),
            "C": C, "A": A, "O": O, "S": S,
            "phi": phi,
            "mode": mode,
            "exploration_factor": exploration_factor
        })
        
        # Update stability tracker
        self.stability_tracker.append(phi)
        if len(self.stability_tracker) > 100:
            self.stability_tracker.pop(0)
        
        return phi, details
    
    def _is_exploration_safe(self, C: float, A: float, O: float, S: float,
                            exploration_factor: float) -> bool:
        """Check if exploration is safe (won't cause instability)"""
        # Check if O and S are high enough to benefit from exploration
        if O < 0.3 or S < 0.3:
            return False
        
        # Check if exploration factor is within bounds
        if exploration_factor > self.config.max_exploration:
            return False
        
        # Check recent stability
        if len(self.stability_tracker) >= 10:
            recent_phi = self.stability_tracker[-10:]
            phi_variance = self._compute_variance(recent_phi)
            if phi_variance > 0.1:  # High variance indicates instability
                return False
        
        return True
    
    def _compute_variance(self, values: list) -> float:
        """Compute variance of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get exploration statistics"""
        if not self.exploration_history:
            return {"count": 0, "avg_phi": 0.0, "exploration_rate": 0.0}
        
        kratos_count = sum(1 for h in self.exploration_history 
                          if h["mode"] == "kratos")
        total_count = len(self.exploration_history)
        
        phi_values = [h["phi"] for h in self.exploration_history]
        
        return {
            "count": total_count,
            "kratos_count": kratos_count,
            "exploration_rate": kratos_count / total_count if total_count > 0 else 0.0,
            "avg_phi": sum(phi_values) / len(phi_values),
            "max_phi": max(phi_values),
            "min_phi": min(phi_values),
            "stability_variance": self._compute_variance(self.stability_tracker)
        }
    
    def adjust_exploration_factor(self, performance_feedback: float):
        """Adjust exploration factor based on performance feedback"""
        # Simple adaptive adjustment
        if performance_feedback > 0.8:
            # Good performance: increase exploration slightly
            self.config.exploration_factor = min(
                self.config.exploration_factor * 1.1,
                self.config.max_exploration
            )
        elif performance_feedback < 0.5:
            # Poor performance: decrease exploration
            self.config.exploration_factor = max(
                self.config.exploration_factor * 0.9,
                1.0
            )


def compare_caos_vs_kratos(C: float, A: float, O: float, S: float,
                          exploration_factor: float = 2.0) -> Dict[str, Any]:
    """
    Compare standard CAOS vs CAOS-KRATOS
    
    Returns:
        Comparison results
    """
    phi_standard = phi_caos(C, A, O, S)
    phi_kratos = phi_kratos(C, A, O, S, exploration_factor)
    
    enhancement = phi_kratos / max(phi_standard, 1e-9)
    
    return {
        "phi_standard": phi_standard,
        "phi_kratos": phi_kratos,
        "enhancement_ratio": enhancement,
        "enhancement_percent": (enhancement - 1.0) * 100,
        "exploration_factor": exploration_factor,
        "components": {"C": C, "A": A, "O": O, "S": S}
    }


# Integration with Life Equation
def integrate_kratos_in_life_equation(
    life_verdict: Dict[str, Any],
    enable_exploration: bool = True
) -> Tuple[float, Dict[str, Any]]:
    """
    Integrate CAOS-KRATOS into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        enable_exploration: Whether to enable KRATOS
        
    Returns:
        (enhanced_alpha_eff, kratos_details)
    """
    if not life_verdict.get("ok", False):
        return 0.0, {"mode": "life_failed", "kratos_disabled": True}
    
    # Extract CAOS components from life verdict
    metrics = life_verdict.get("metrics", {})
    phi = metrics.get("phi", 0.0)
    
    # If phi is low, try KRATOS enhancement
    if phi < 0.3 and enable_exploration:
        # Extract components (would need to be passed from life_equation)
        C, A, O, S = 0.8, 0.7, 0.6, 0.9  # Placeholder - should come from life_equation
        
        kratos_engine = KratosEngine()
        enhanced_phi, kratos_details = kratos_engine.compute_kratos(C, A, O, S, True)
        
        # Recompute alpha_eff with enhanced phi
        base_alpha = 1e-3  # Should come from life_equation
        sr = metrics.get("sr", 0.8)
        G = metrics.get("G", 0.9)
        
        # Simple acceleration function
        accel = (1.0 + 20.0 * enhanced_phi) / (1.0 + 20.0)
        enhanced_alpha_eff = base_alpha * enhanced_phi * sr * G * accel
        
        return enhanced_alpha_eff, kratos_details
    else:
        return life_verdict.get("alpha_eff", 0.0), {"mode": "standard", "kratos_disabled": False}


# Example usage
if __name__ == "__main__":
    import time
    
    # Test CAOS-KRATOS
    C, A, O, S = 0.8, 0.7, 0.6, 0.9
    
    print("CAOS vs CAOS-KRATOS Comparison:")
    comparison = compare_caos_vs_kratos(C, A, O, S, 2.0)
    print(f"Standard CAOS: {comparison['phi_standard']:.4f}")
    print(f"CAOS-KRATOS: {comparison['phi_kratos']:.4f}")
    print(f"Enhancement: {comparison['enhancement_percent']:.1f}%")
    
    # Test KratosEngine
    engine = KratosEngine()
    
    for i in range(5):
        phi, details = engine.compute_kratos(C, A, O, S, True)
        print(f"Iteration {i+1}: phi={phi:.4f}, mode={details['mode']}")
    
    stats = engine.get_exploration_stats()
    print(f"Exploration stats: {stats}")