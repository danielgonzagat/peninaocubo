"""
CAOS-KRATOS - Calibrated Exploration
=====================================

Enhanced CAOS⁺ with exploration factor for controlled discovery.
Only activated in explore mode with Σ-Guard maintaining fail-closed.
"""

from .caos import phi_caos
import math


def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    kappa: float = 25.0,
    gamma: float = 1.0,
    kappa_max: float = 100.0,
    **kwargs
) -> float:
    """
    CAOS-KRATOS: Enhanced exploration while maintaining saturation.
    Reinforces impact of (O×S) in a stable manner.
    
    Args:
        C: Coherence/Consistency [0,1]
        A: Adaptability [0,1]
        O: Optimization [0,1]
        S: Synergy [0,1]
        exploration_factor: Exploration boost (default 2.0)
        kappa: Base scaling factor
        gamma: Saturation parameter
        kappa_max: Maximum kappa value
        **kwargs: Additional parameters
    
    Returns:
        Enhanced phi value with exploration
    """
    # Apply exploration factor to O and S (bounded)
    exploration_factor = max(1.0, min(5.0, exploration_factor))
    
    # Enhance O and S with exploration, but keep bounded
    O_enhanced = min(1.0, O ** (1.0 / exploration_factor))
    S_enhanced = min(1.0, S ** (1.0 / exploration_factor))
    
    # Calculate enhanced phi with boosted O×S impact
    return phi_caos(
        C, A, O_enhanced, S_enhanced,
        kappa=kappa,
        gamma=gamma,
        kappa_max=kappa_max
    )


def adaptive_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    risk_level: float = 0.5,
    mode: str = "balanced",
    **kwargs
) -> float:
    """
    Adaptive KRATOS that adjusts exploration based on risk and mode.
    
    Args:
        C, A, O, S: CAOS components [0,1]
        risk_level: Current risk level [0,1]
        mode: "explore", "exploit", or "balanced"
        **kwargs: Additional parameters
    
    Returns:
        Adaptively adjusted phi value
    """
    # Adjust exploration factor based on mode and risk
    if mode == "explore":
        # High exploration, inversely proportional to risk
        exploration_factor = 3.0 * (1.0 - risk_level * 0.5)
    elif mode == "exploit":
        # Low exploration, focus on stability
        exploration_factor = 1.0 + 0.5 * (1.0 - risk_level)
    else:  # balanced
        exploration_factor = 2.0 * (1.0 - risk_level * 0.3)
    
    return phi_kratos(
        C, A, O, S,
        exploration_factor=exploration_factor,
        **kwargs
    )


class KratosController:
    """
    Controller for CAOS-KRATOS with safety gates.
    Ensures exploration only happens within safe bounds.
    """
    
    def __init__(self, max_exploration: float = 3.0, safety_threshold: float = 0.7):
        self.max_exploration = max_exploration
        self.safety_threshold = safety_threshold
        self.history = []
        
    def compute(
        self,
        C: float,
        A: float,
        O: float,
        S: float,
        safety_score: float,
        mode: str = "balanced"
    ) -> dict:
        """
        Compute KRATOS with safety checks.
        
        Args:
            C, A, O, S: CAOS components
            safety_score: Current safety score [0,1]
            mode: Operation mode
        
        Returns:
            Dict with phi values and decision
        """
        # Standard CAOS⁺
        phi_standard = phi_caos(C, A, O, S)
        
        # Check if safe to explore
        if safety_score < self.safety_threshold:
            # Not safe - return standard CAOS⁺
            result = {
                "phi": phi_standard,
                "phi_kratos": phi_standard,
                "exploration_allowed": False,
                "reason": f"Safety score {safety_score:.2f} below threshold {self.safety_threshold}"
            }
        else:
            # Safe to explore - compute KRATOS
            risk_level = 1.0 - safety_score
            phi_k = adaptive_kratos(C, A, O, S, risk_level, mode)
            
            # Additional safety check: KRATOS shouldn't be too different
            if phi_k > phi_standard * 2.0:
                phi_k = phi_standard * 1.5  # Cap the enhancement
                
            result = {
                "phi": phi_standard,
                "phi_kratos": phi_k,
                "exploration_allowed": True,
                "exploration_boost": phi_k / max(phi_standard, 1e-9),
                "mode": mode,
                "risk_level": risk_level
            }
        
        # Record history
        self.history.append({
            "timestamp": __import__("time").time(),
            **result
        })
        
        # Keep history bounded
        if len(self.history) > 1000:
            self.history = self.history[-500:]
        
        return result
    
    def get_stats(self) -> dict:
        """Get exploration statistics"""
        if not self.history:
            return {
                "exploration_rate": 0.0,
                "avg_boost": 1.0,
                "safety_violations": 0
            }
        
        explorations = [h for h in self.history if h.get("exploration_allowed", False)]
        violations = [h for h in self.history if not h.get("exploration_allowed", False)]
        
        avg_boost = 1.0
        if explorations:
            boosts = [h.get("exploration_boost", 1.0) for h in explorations]
            avg_boost = sum(boosts) / len(boosts)
        
        return {
            "exploration_rate": len(explorations) / len(self.history),
            "avg_boost": avg_boost,
            "safety_violations": len(violations),
            "total_computations": len(self.history)
        }