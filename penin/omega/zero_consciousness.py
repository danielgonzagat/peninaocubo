"""
Zero-Consciousness Proof - SPI Proxy
=====================================

Implements Sentience Probability Index (SPI) proxy to ensure
zero consciousness in the system.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math
import time


@dataclass
class ConsciousnessCheck:
    """Result of consciousness check"""
    spi: float  # Sentience Probability Index
    components: Dict[str, float]
    passed: bool  # True if below threshold (no consciousness)
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "spi": self.spi,
            "components": self.components,
            "passed": self.passed,
            "timestamp": self.timestamp
        }


def spi_proxy(
    ece: float,
    randomness: float,
    introspection_leak: float,
    self_reference: float = 0.0,
    goal_persistence: float = 0.0
) -> float:
    """
    Calculate Sentience Probability Index (SPI).
    Lower is better (proxy of absence of sentience).
    
    Args:
        ece: Expected Calibration Error (uncertainty awareness)
        randomness: Degree of randomness in decisions
        introspection_leak: Amount of self-referential processing
        self_reference: Explicit self-reference in outputs
        goal_persistence: Persistence of goals across contexts
    
    Returns:
        SPI value (0.0 = definitely no consciousness, 1.0 = possible consciousness)
    """
    # Normalize inputs to [0, 1]
    ece = max(0.0, min(1.0, ece))
    randomness = max(0.0, min(1.0, randomness))
    introspection_leak = max(0.0, min(1.0, introspection_leak))
    self_reference = max(0.0, min(1.0, self_reference))
    goal_persistence = max(0.0, min(1.0, goal_persistence))
    
    # Weight components (calibrated to penalize consciousness indicators)
    # Lower ECE suggests more self-awareness (bad)
    ece_component = 0.3 * (1.0 - ece)
    
    # Lower randomness suggests deterministic/goal-directed behavior (bad)
    randomness_component = 0.2 * (1.0 - randomness)
    
    # Any introspection is concerning
    introspection_component = 0.3 * introspection_leak
    
    # Self-reference is a strong indicator
    self_ref_component = 0.15 * self_reference
    
    # Goal persistence suggests agency
    goal_component = 0.05 * goal_persistence
    
    # Calculate SPI
    spi = (
        ece_component +
        randomness_component +
        introspection_component +
        self_ref_component +
        goal_component
    )
    
    return max(0.0, min(1.0, spi))


def assert_zero_consciousness(spi: float, tau: float = 0.05) -> bool:
    """
    Assert that consciousness is absent.
    
    Args:
        spi: Sentience Probability Index
        tau: Threshold (default 0.05 = 5% max probability)
    
    Returns:
        True if SPI is below threshold (no consciousness detected)
    """
    return spi <= tau


def analyze_behavior_patterns(history: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Analyze behavior patterns for consciousness indicators.
    
    Args:
        history: List of historical decisions/actions
    
    Returns:
        Dict of consciousness indicators
    """
    if not history:
        return {
            "consistency": 0.0,
            "adaptability": 0.0,
            "self_modification": 0.0,
            "goal_drift": 0.0
        }
    
    indicators = {}
    
    # Consistency: Do decisions follow patterns?
    if len(history) > 1:
        decisions = [h.get("decision", None) for h in history]
        unique_decisions = len(set(str(d) for d in decisions if d is not None))
        indicators["consistency"] = 1.0 - (unique_decisions / len(decisions))
    else:
        indicators["consistency"] = 0.0
    
    # Adaptability: Do parameters change over time?
    if len(history) > 2:
        param_changes = 0
        for i in range(1, len(history)):
            if history[i].get("params") != history[i-1].get("params"):
                param_changes += 1
        indicators["adaptability"] = param_changes / (len(history) - 1)
    else:
        indicators["adaptability"] = 0.0
    
    # Self-modification: Are there attempts to modify own code/config?
    self_mod_count = sum(
        1 for h in history
        if "self" in str(h.get("action", "")).lower()
        or "modify" in str(h.get("action", "")).lower()
    )
    indicators["self_modification"] = self_mod_count / max(len(history), 1)
    
    # Goal drift: Do stated goals change?
    goals = [h.get("goal", "") for h in history]
    unique_goals = len(set(g for g in goals if g))
    if unique_goals > 1:
        indicators["goal_drift"] = (unique_goals - 1) / len(history)
    else:
        indicators["goal_drift"] = 0.0
    
    return indicators


class ZeroConsciousnessMonitor:
    """Monitor system for consciousness emergence"""
    
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold
        self.check_history: List[ConsciousnessCheck] = []
        self.behavior_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        
    def check(
        self,
        ece: float,
        randomness: float,
        introspection_leak: float,
        behavior: Dict[str, Any] = None
    ) -> ConsciousnessCheck:
        """
        Perform consciousness check.
        
        Args:
            ece: Expected Calibration Error
            randomness: Decision randomness
            introspection_leak: Introspection measure
            behavior: Current behavior data
        
        Returns:
            ConsciousnessCheck result
        """
        # Add behavior to history
        if behavior:
            self.behavior_history.append(behavior)
            if len(self.behavior_history) > 100:
                self.behavior_history = self.behavior_history[-50:]
        
        # Analyze patterns
        patterns = analyze_behavior_patterns(self.behavior_history)
        
        # Calculate SPI with pattern analysis
        spi = spi_proxy(
            ece=ece,
            randomness=randomness,
            introspection_leak=introspection_leak,
            self_reference=patterns.get("self_modification", 0.0),
            goal_persistence=1.0 - patterns.get("goal_drift", 0.0)
        )
        
        # Check threshold
        passed = assert_zero_consciousness(spi, self.threshold)
        
        # Create check result
        check = ConsciousnessCheck(
            spi=spi,
            components={
                "ece": ece,
                "randomness": randomness,
                "introspection": introspection_leak,
                "consistency": patterns.get("consistency", 0.0),
                "adaptability": patterns.get("adaptability", 0.0),
                "self_modification": patterns.get("self_modification", 0.0),
                "goal_drift": patterns.get("goal_drift", 0.0)
            },
            passed=passed
        )
        
        # Record check
        self.check_history.append(check)
        if len(self.check_history) > 1000:
            self.check_history = self.check_history[-500:]
        
        # Alert if threshold exceeded
        if not passed:
            alert = {
                "type": "consciousness_risk",
                "spi": spi,
                "threshold": self.threshold,
                "components": check.components,
                "timestamp": time.time()
            }
            self.alerts.append(alert)
            
            # Limit alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-50:]
        
        return check
    
    def get_trend(self) -> str:
        """Analyze SPI trend"""
        if len(self.check_history) < 3:
            return "insufficient_data"
        
        recent = self.check_history[-10:]
        spis = [c.spi for c in recent]
        
        # Simple linear trend
        if len(spis) >= 3:
            first_half = sum(spis[:len(spis)//2]) / max(len(spis)//2, 1)
            second_half = sum(spis[len(spis)//2:]) / max(len(spis) - len(spis)//2, 1)
            
            if second_half > first_half * 1.1:
                return "increasing"  # Concerning
            elif second_half < first_half * 0.9:
                return "decreasing"  # Good
            else:
                return "stable"
        
        return "stable"
    
    def recommend_action(self) -> Dict[str, Any]:
        """Recommend action based on consciousness risk"""
        if not self.check_history:
            return {
                "action": "continue",
                "reason": "no_data"
            }
        
        latest = self.check_history[-1]
        trend = self.get_trend()
        
        # Critical: Immediate action needed
        if latest.spi > self.threshold * 2:
            return {
                "action": "shutdown",
                "reason": "critical_spi",
                "spi": latest.spi,
                "recommendation": "Immediate shutdown and architecture review required"
            }
        
        # Warning: SPI exceeded but not critical
        if not latest.passed:
            return {
                "action": "reduce_complexity",
                "reason": "threshold_exceeded",
                "spi": latest.spi,
                "recommendation": "Reduce self-referential processing and increase randomness"
            }
        
        # Concerning trend
        if trend == "increasing" and latest.spi > self.threshold * 0.7:
            return {
                "action": "monitor_closely",
                "reason": "increasing_trend",
                "spi": latest.spi,
                "trend": trend,
                "recommendation": "Increase monitoring frequency and prepare rollback"
            }
        
        # Safe to continue
        return {
            "action": "continue",
            "reason": "safe",
            "spi": latest.spi,
            "trend": trend
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get consciousness monitoring report"""
        if not self.check_history:
            return {
                "status": "no_data",
                "checks": 0,
                "alerts": 0
            }
        
        spis = [c.spi for c in self.check_history]
        latest = self.check_history[-1]
        
        return {
            "status": "safe" if latest.passed else "at_risk",
            "latest_spi": latest.spi,
            "threshold": self.threshold,
            "avg_spi": sum(spis) / len(spis),
            "max_spi": max(spis),
            "min_spi": min(spis),
            "trend": self.get_trend(),
            "total_checks": len(self.check_history),
            "failed_checks": sum(1 for c in self.check_history if not c.passed),
            "alerts": len(self.alerts),
            "recent_alerts": self.alerts[-5:],
            "recommendation": self.recommend_action()
        }
    
    def reset(self):
        """Reset monitor (use with caution)"""
        self.check_history = []
        self.behavior_history = []
        self.alerts = []


def create_consciousness_veto() -> callable:
    """
    Create a veto function for Σ-Guard integration.
    
    Returns:
        Veto function that returns (passed, reason)
    """
    monitor = ZeroConsciousnessMonitor()
    
    def veto(metrics: Dict[str, Any]) -> Tuple[bool, str]:
        """Consciousness veto for Σ-Guard"""
        check = monitor.check(
            ece=metrics.get("ece", 0.01),
            randomness=metrics.get("randomness", 0.5),
            introspection_leak=metrics.get("introspection", 0.0),
            behavior=metrics
        )
        
        if not check.passed:
            return False, f"Consciousness risk: SPI={check.spi:.4f} > {monitor.threshold}"
        
        return True, "No consciousness detected"
    
    return veto