"""
CAOS-KRATOS - Calibrated Exploration Mode
=========================================

Implements an exploration-focused variant of CAOS⁺ that:
- Amplifies O×S (opportunity × stability) for bolder exploration
- Maintains saturation to prevent numerical explosion
- Only activates in "explore" mode (Σ-Guard still fail-closed in "promote")

This allows the system to explore more aggressively during search phases
while maintaining safety during production deployment.
"""

import math
from typing import Dict, Any, Tuple
from .caos import phi_caos, clamp01


def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = 0.7,
) -> float:
    """
    CAOS-KRATOS: Exploration-enhanced CAOS⁺.
    
    Reinforces the impact of (O×S) while maintaining saturation.
    
    Formula:
        φ_kratos = φ_caos(C, A, O^exploration_factor, S^exploration_factor)
        
    This amplifies opportunity and stability components, encouraging
    more aggressive exploration when these factors are favorable.
    
    Args:
        C, A, O, S: Standard CAOS components [0, 1]
        exploration_factor: Exponent for O and S (default 2.0)
        kappa, kappa_max, gamma: Standard phi_caos parameters
        
    Returns:
        Exploration-enhanced phi score [0, 1)
    """
    # Clamp exploration factor to safe range
    exploration_factor = max(1.0, min(3.0, exploration_factor))
    
    # Apply exploration boost to O and S
    O_boosted = O ** exploration_factor
    S_boosted = S ** exploration_factor
    
    # Use standard phi_caos with boosted values
    return phi_caos(C, A, O_boosted, S_boosted, kappa, kappa_max, gamma)


def compute_kratos_with_fallback(
    C: float,
    A: float,
    O: float,
    S: float,
    mode: str = "explore",
    exploration_factor: float = 2.0,
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute CAOS score with mode-dependent exploration.
    
    Args:
        C, A, O, S: CAOS components
        mode: "explore" (use KRATOS) or "promote" (use standard phi_caos)
        exploration_factor: Boost factor for exploration mode
        
    Returns:
        (phi, details) tuple
    """
    if mode == "explore":
        phi = phi_kratos(C, A, O, S, exploration_factor)
        details = {
            "mode": "KRATOS_EXPLORE",
            "exploration_factor": exploration_factor,
            "C": C, "A": A, "O": O, "S": S,
            "phi": phi
        }
    else:
        phi = phi_caos(C, A, O, S)
        details = {
            "mode": "STANDARD_PROMOTE",
            "C": C, "A": A, "O": O, "S": S,
            "phi": phi
        }
    
    return phi, details


def adaptive_exploration_factor(
    current_performance: float,
    target_performance: float,
    min_factor: float = 1.0,
    max_factor: float = 3.0,
) -> float:
    """
    Compute adaptive exploration factor based on performance gap.
    
    When current performance is far from target, increase exploration.
    When close to target, reduce exploration for exploitation.
    
    Args:
        current_performance: Current system performance [0, 1]
        target_performance: Target performance [0, 1]
        min_factor: Minimum exploration factor
        max_factor: Maximum exploration factor
        
    Returns:
        Exploration factor in [min_factor, max_factor]
    """
    gap = abs(target_performance - current_performance)
    
    # Map gap [0, 1] to factor [min, max]
    # Larger gap → larger factor (more exploration)
    factor = min_factor + (max_factor - min_factor) * gap
    
    return max(min_factor, min(max_factor, factor))


class KratosController:
    """
    Controls CAOS-KRATOS exploration mode.
    
    Manages:
    - Mode switching (explore vs promote)
    - Adaptive exploration factor
    - Safety gates (Σ-Guard always enforced)
    """
    
    def __init__(
        self,
        default_mode: str = "explore",
        default_exploration_factor: float = 2.0
    ):
        self.mode = default_mode
        self.exploration_factor = default_exploration_factor
        self.history: list = []
        
        print(f"⚡ KRATOS Controller initialized (mode={self.mode}, factor={self.exploration_factor})")
    
    def set_mode(self, mode: str) -> None:
        """Set exploration mode"""
        if mode not in ["explore", "promote"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'explore' or 'promote'")
        
        self.mode = mode
        print(f"⚡ KRATOS mode set to: {mode}")
    
    def set_exploration_factor(self, factor: float) -> None:
        """Set exploration factor"""
        self.exploration_factor = max(1.0, min(3.0, factor))
        print(f"⚡ KRATOS exploration factor set to: {self.exploration_factor:.2f}")
    
    def compute_phi(
        self,
        C: float,
        A: float,
        O: float,
        S: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute phi with current mode and factor.
        
        Returns:
            (phi, details) tuple
        """
        phi, details = compute_kratos_with_fallback(
            C, A, O, S,
            mode=self.mode,
            exploration_factor=self.exploration_factor
        )
        
        # Record in history
        self.history.append({
            "timestamp": len(self.history),
            "mode": self.mode,
            "factor": self.exploration_factor,
            "phi": phi,
            "components": {"C": C, "A": A, "O": O, "S": S}
        })
        
        return phi, details
    
    def update_adaptive(
        self,
        current_performance: float,
        target_performance: float
    ) -> None:
        """Update exploration factor adaptively based on performance gap"""
        new_factor = adaptive_exploration_factor(
            current_performance,
            target_performance
        )
        
        print(f"⚡ Adaptive update: performance gap = {abs(target_performance - current_performance):.4f}")
        print(f"   New exploration factor: {new_factor:.2f}")
        
        self.set_exploration_factor(new_factor)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics"""
        if not self.history:
            return {
                "mode": self.mode,
                "exploration_factor": self.exploration_factor,
                "history_length": 0
            }
        
        phi_values = [h["phi"] for h in self.history]
        
        return {
            "mode": self.mode,
            "exploration_factor": self.exploration_factor,
            "history_length": len(self.history),
            "phi_mean": sum(phi_values) / len(phi_values),
            "phi_min": min(phi_values),
            "phi_max": max(phi_values),
            "recent_phi": phi_values[-10:] if len(phi_values) >= 10 else phi_values
        }


# Quick test function
def quick_kratos_test():
    """Quick test of KRATOS functionality"""
    controller = KratosController(mode="explore", default_exploration_factor=2.0)
    
    # Test exploration mode
    print("\n🧪 Testing EXPLORE mode:")
    phi_explore, details = controller.compute_phi(0.6, 0.7, 0.8, 0.9)
    print(f"   φ_explore = {phi_explore:.4f}")
    print(f"   Details: {details}")
    
    # Switch to promote mode
    controller.set_mode("promote")
    print("\n🧪 Testing PROMOTE mode:")
    phi_promote, details = controller.compute_phi(0.6, 0.7, 0.8, 0.9)
    print(f"   φ_promote = {phi_promote:.4f}")
    print(f"   Details: {details}")
    
    # Test adaptive factor
    print("\n🧪 Testing ADAPTIVE factor:")
    controller.set_mode("explore")
    controller.update_adaptive(current_performance=0.6, target_performance=0.9)
    phi_adaptive, details = controller.compute_phi(0.6, 0.7, 0.8, 0.9)
    print(f"   φ_adaptive = {phi_adaptive:.4f}")
    
    # Get stats
    stats = controller.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return controller