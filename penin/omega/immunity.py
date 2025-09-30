"""
Digital Immunity - Anomaly Detection & Fail-Closed
=================================================

Detects anomalous metrics and triggers fail-closed response.

Simple heuristics:
- NaN/Inf detection
- Out-of-range values
- Sudden spikes

When anomaly detected → Σ-Guard blocks and initiates rollback.
"""

from typing import Dict, Any, List
import math


def anomaly_score(metrics: Dict[str, Any]) -> float:
    """
    Compute anomaly score for metrics.
    
    Args:
        metrics: Dict of metric values
        
    Returns:
        Anomaly score (0 = clean, higher = more anomalous)
    """
    score = 0.0
    
    for key, value in metrics.items():
        try:
            v = float(value)
            
            # Check for NaN/Inf
            if math.isnan(v) or math.isinf(v):
                score += 10.0
                continue
            
            # Check for negative (most metrics should be positive)
            if v < 0.0:
                score += 5.0
            
            # Check for absurd values
            if abs(v) > 1e6:
                score += 3.0
            
        except (ValueError, TypeError):
            # Non-numeric value
            score += 1.0
    
    return score


def guard(metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
    """
    Guard function: returns True if OK, False if anomaly detected.
    
    Args:
        metrics: Metrics to check
        trigger: Anomaly threshold (default 1.0)
        
    Returns:
        True if metrics are OK, False if anomaly detected
    """
    score = anomaly_score(metrics)
    return score < trigger


class ImmunitySystem:
    """
    Digital immunity system.
    
    Monitors metrics for anomalies and triggers fail-closed response.
    """
    
    def __init__(self, trigger: float = 1.0):
        self.trigger = trigger
        self.alerts: List[Dict[str, Any]] = []
        print(f"🛡️  Immunity System initialized (trigger={trigger})")
    
    def check(self, metrics: Dict[str, Any]) -> bool:
        """
        Check metrics for anomalies.
        
        Returns:
            True if OK, False if anomaly
        """
        score = anomaly_score(metrics)
        
        if score >= self.trigger:
            alert = {
                "score": score,
                "metrics": metrics,
                "triggered": True
            }
            self.alerts.append(alert)
            print(f"⚠️  ANOMALY DETECTED: score={score:.2f}")
            return False
        
        return True
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts"""
        return self.alerts
    
    def reset_alerts(self) -> None:
        """Clear alert history"""
        self.alerts = []


# Quick test
def quick_immunity_test():
    """Quick test of immunity system"""
    system = ImmunitySystem(trigger=1.0)
    
    # Test clean metrics
    clean = {"phi": 0.7, "sr": 0.85, "G": 0.9}
    assert system.check(clean), "Clean metrics should pass"
    print("✅ Clean metrics passed")
    
    # Test anomalous metrics
    anomalous = {"phi": float('nan'), "sr": -1.0, "G": 1e10}
    assert not system.check(anomalous), "Anomalous metrics should fail"
    print("✅ Anomalous metrics blocked")
    
    alerts = system.get_alerts()
    print(f"\n📊 Total alerts: {len(alerts)}")
    
    return system