"""
CAOS-KRATOS - Exploration Mode
==============================

Enhanced CAOS+ with exploration factor for controlled chaos.
Reinforces impact of (O×S) while maintaining saturation.
"""

import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Import base CAOS
from .caos import phi_caos, CAOSComponents


class ExplorationMode(Enum):
    """Exploration modes"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CHAOTIC = "chaotic"


@dataclass
class KratosConfig:
    """Configuration for CAOS-KRATOS"""
    exploration_factor: float = 2.0
    mode: ExplorationMode = ExplorationMode.MODERATE
    max_exploration: float = 5.0
    saturation_threshold: float = 0.95
    adaptive_factor: bool = True


def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    kappa: float = 20.0,
    gamma: float = 0.7,
    kappa_max: float = 100.0,
    **kwargs
) -> float:
    """
    CAOS-KRATOS phi calculation with exploration enhancement
    
    Reinforces impact of (O×S) while maintaining saturation:
    - O^exploration_factor and S^exploration_factor
    - Maintains numerical stability
    - Provides controlled exploration boost
    
    Args:
        C: Complexity
        A: Adaptability
        O: Openness
        S: Stability
        exploration_factor: Factor to enhance O×S impact
        kappa: Base CAOS kappa
        gamma: Base CAOS gamma
        kappa_max: Maximum kappa
        
    Returns:
        Enhanced CAOS+ phi value
    """
    # Clamp inputs
    C = max(0.0, min(1.0, C))
    A = max(0.0, min(1.0, A))
    O = max(0.0, min(1.0, O))
    S = max(0.0, min(1.0, S))
    
    # Apply exploration factor to O and S
    # Use power function but ensure it doesn't explode
    O_enhanced = O ** min(exploration_factor, 3.0)  # Cap at 3.0 to prevent explosion
    S_enhanced = S ** min(exploration_factor, 3.0)
    
    # Call base phi_caos with enhanced O and S
    return phi_caos(C, A, O_enhanced, S_enhanced, kappa, kappa_max, gamma)


def adaptive_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    recent_performance: List[float],
    exploration_factor: float = 2.0,
    **kwargs
) -> Tuple[float, Dict[str, Any]]:
    """
    Adaptive CAOS-KRATOS that adjusts exploration based on recent performance
    
    Args:
        C, A, O, S: CAOS components
        recent_performance: List of recent performance scores
        exploration_factor: Base exploration factor
        
    Returns:
        (phi_value, details)
    """
    # Analyze recent performance trend
    if len(recent_performance) >= 3:
        # Calculate trend
        recent_avg = sum(recent_performance[-3:]) / 3
        earlier_avg = sum(recent_performance[:-3]) / len(recent_performance[:-3]) if len(recent_performance) > 3 else recent_avg
        
        trend = recent_avg - earlier_avg
        
        # Adjust exploration factor based on trend
        if trend > 0.1:  # Improving
            adaptive_factor = min(exploration_factor * 1.2, 5.0)
        elif trend < -0.1:  # Declining
            adaptive_factor = max(exploration_factor * 0.8, 1.0)
        else:  # Stable
            adaptive_factor = exploration_factor
    else:
        adaptive_factor = exploration_factor
    
    # Calculate phi with adaptive factor
    phi = phi_kratos(C, A, O, S, exploration_factor=adaptive_factor, **kwargs)
    
    details = {
        "exploration_factor": adaptive_factor,
        "trend": trend if len(recent_performance) >= 3 else 0.0,
        "recent_performance": recent_performance[-3:] if recent_performance else [],
        "base_phi": phi_caos(C, A, O, S, **kwargs),
        "enhanced_phi": phi
    }
    
    return phi, details


def kratos_mode_phi(
    C: float,
    A: float,
    O: float,
    S: float,
    mode: ExplorationMode = ExplorationMode.MODERATE,
    **kwargs
) -> Tuple[float, Dict[str, Any]]:
    """
    CAOS-KRATOS with predefined exploration modes
    
    Args:
        C, A, O, S: CAOS components
        mode: Exploration mode
        **kwargs: Additional parameters
        
    Returns:
        (phi_value, details)
    """
    mode_factors = {
        ExplorationMode.CONSERVATIVE: 1.2,
        ExplorationMode.MODERATE: 2.0,
        ExplorationMode.AGGRESSIVE: 3.0,
        ExplorationMode.CHAOTIC: 4.0
    }
    
    exploration_factor = mode_factors[mode]
    phi = phi_kratos(C, A, O, S, exploration_factor=exploration_factor, **kwargs)
    
    details = {
        "mode": mode.value,
        "exploration_factor": exploration_factor,
        "base_phi": phi_caos(C, A, O, S, **kwargs),
        "enhanced_phi": phi,
        "enhancement_ratio": phi / max(phi_caos(C, A, O, S, **kwargs), 1e-9)
    }
    
    return phi, details


class KratosTracker:
    """Track CAOS-KRATOS values over time"""
    
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.history: List[Dict[str, Any]] = []
        self.performance_history: List[float] = []
    
    def update(
        self,
        C: float,
        A: float,
        O: float,
        S: float,
        performance: float,
        exploration_factor: float = 2.0,
        mode: ExplorationMode = ExplorationMode.MODERATE
    ) -> Tuple[float, Dict[str, Any]]:
        """Update tracker with new values"""
        
        # Calculate phi
        phi, details = kratos_mode_phi(C, A, O, S, mode, exploration_factor=exploration_factor)
        
        # Record performance
        self.performance_history.append(performance)
        if len(self.performance_history) > self.window_size:
            self.performance_history.pop(0)
        
        # Record history
        record = {
            "timestamp": time.time(),
            "C": C, "A": A, "O": O, "S": S,
            "performance": performance,
            "phi": phi,
            "exploration_factor": exploration_factor,
            "mode": mode.value,
            **details
        }
        
        self.history.append(record)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        
        return phi, details
    
    def get_optimal_exploration_factor(self) -> float:
        """Determine optimal exploration factor based on history"""
        if len(self.performance_history) < 5:
            return 2.0  # Default
        
        # Analyze correlation between exploration factor and performance
        recent_performance = self.performance_history[-10:]
        recent_factors = [record["exploration_factor"] for record in self.history[-10:]]
        
        if len(recent_performance) != len(recent_factors):
            return 2.0
        
        # Simple correlation analysis
        perf_mean = sum(recent_performance) / len(recent_performance)
        factor_mean = sum(recent_factors) / len(recent_factors)
        
        numerator = sum((p - perf_mean) * (f - factor_mean) for p, f in zip(recent_performance, recent_factors))
        denominator = sum((f - factor_mean) ** 2 for f in recent_factors)
        
        if denominator == 0:
            return 2.0
        
        correlation = numerator / denominator
        
        # Adjust factor based on correlation
        if correlation > 0.1:  # Positive correlation
            return min(3.0, factor_mean * 1.1)
        elif correlation < -0.1:  # Negative correlation
            return max(1.0, factor_mean * 0.9)
        else:
            return 2.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        if not self.history:
            return {"count": 0, "avg_phi": 0.0, "avg_performance": 0.0}
        
        avg_phi = sum(record["phi"] for record in self.history) / len(self.history)
        avg_performance = sum(self.performance_history) / len(self.performance_history)
        avg_exploration_factor = sum(record["exploration_factor"] for record in self.history) / len(self.history)
        
        return {
            "count": len(self.history),
            "avg_phi": avg_phi,
            "avg_performance": avg_performance,
            "avg_exploration_factor": avg_exploration_factor,
            "optimal_exploration_factor": self.get_optimal_exploration_factor(),
            "latest_phi": self.history[-1]["phi"] if self.history else 0.0
        }


def compare_caos_vs_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0
) -> Dict[str, Any]:
    """Compare base CAOS+ vs CAOS-KRATOS"""
    
    base_phi = phi_caos(C, A, O, S)
    kratos_phi = phi_kratos(C, A, O, S, exploration_factor)
    
    enhancement_ratio = kratos_phi / max(base_phi, 1e-9)
    
    return {
        "base_phi": base_phi,
        "kratos_phi": kratos_phi,
        "enhancement_ratio": enhancement_ratio,
        "enhancement_percent": (enhancement_ratio - 1.0) * 100,
        "components": {"C": C, "A": A, "O": O, "S": S},
        "exploration_factor": exploration_factor
    }


def test_kratos_modes() -> Dict[str, Any]:
    """Test different Kratos modes"""
    C, A, O, S = 0.8, 0.7, 0.6, 0.9
    
    results = {}
    for mode in ExplorationMode:
        phi, details = kratos_mode_phi(C, A, O, S, mode)
        results[mode.value] = {
            "phi": phi,
            "details": details
        }
    
    return {
        "components": {"C": C, "A": A, "O": O, "S": S},
        "modes": results,
        "base_phi": phi_caos(C, A, O, S)
    }


# Import time for tracker
import time