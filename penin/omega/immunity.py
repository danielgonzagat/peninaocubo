"""
Digital Immunity - Anomaly Detection and Fail-Closed Protection
================================================================

Detects anomalies in metrics and triggers fail-closed protection.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math
import time


@dataclass
class AnomalyReport:
    """Anomaly detection report"""
    metric: str
    value: Any
    reason: str
    severity: str  # "critical", "high", "medium", "low"
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "reason": self.reason,
            "severity": self.severity,
            "timestamp": self.timestamp
        }


def anomaly_score(metrics: Dict[str, Any]) -> float:
    """
    Calculate anomaly score for metrics.
    Higher score = more anomalous.
    
    Args:
        metrics: Dictionary of metric values
    
    Returns:
        Anomaly score (0.0 = normal, higher = more anomalous)
    """
    score = 0.0
    
    for key, value in metrics.items():
        try:
            # Check for invalid types
            if value is None:
                score += 1.0
                continue
            
            # Check numeric values
            if isinstance(value, (int, float)):
                fval = float(value)
                
                # Check for NaN or Inf
                if math.isnan(fval) or math.isinf(fval):
                    score += 2.0
                    continue
                
                # Check for negative values in typically positive metrics
                positive_metrics = ["accuracy", "score", "health", "confidence", "phi", "sr"]
                if any(pm in key.lower() for pm in positive_metrics):
                    if fval < 0.0:
                        score += 1.5
                
                # Check for out-of-range probabilities
                prob_metrics = ["prob", "confidence", "rate", "ratio"]
                if any(pm in key.lower() for pm in prob_metrics):
                    if not (0.0 <= fval <= 1.0):
                        score += 1.0
                
                # Check for absurdly large values
                if fval > 1e6:
                    score += 0.5
            
            # Check string values
            elif isinstance(value, str):
                # Check for error indicators
                error_terms = ["error", "fail", "exception", "crash", "abort"]
                if any(term in value.lower() for term in error_terms):
                    score += 1.0
        
        except Exception:
            # Any exception in processing is itself an anomaly
            score += 0.5
    
    return score


def guard(metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
    """
    Guard against anomalies with fail-closed behavior.
    
    Args:
        metrics: Metrics to check
        trigger: Anomaly score threshold
    
    Returns:
        True if safe (proceed), False if anomaly detected (block)
    """
    score = anomaly_score(metrics)
    return score < trigger


def detect_anomalies(metrics: Dict[str, Any], history: List[Dict[str, Any]] = None) -> List[AnomalyReport]:
    """
    Detect specific anomalies in metrics.
    
    Args:
        metrics: Current metrics
        history: Optional historical metrics for comparison
    
    Returns:
        List of anomaly reports
    """
    anomalies = []
    
    # Check each metric
    for key, value in metrics.items():
        # Null check
        if value is None:
            anomalies.append(AnomalyReport(
                metric=key,
                value=value,
                reason="Null value",
                severity="high"
            ))
            continue
        
        # Numeric checks
        if isinstance(value, (int, float)):
            fval = float(value)
            
            # NaN/Inf check
            if math.isnan(fval):
                anomalies.append(AnomalyReport(
                    metric=key,
                    value=value,
                    reason="NaN value",
                    severity="critical"
                ))
            elif math.isinf(fval):
                anomalies.append(AnomalyReport(
                    metric=key,
                    value=value,
                    reason="Infinite value",
                    severity="critical"
                ))
            
            # Domain-specific checks
            if "ece" in key.lower() and fval > 0.01:
                anomalies.append(AnomalyReport(
                    metric=key,
                    value=value,
                    reason=f"ECE {fval:.4f} exceeds threshold 0.01",
                    severity="high"
                ))
            
            if "rho" in key.lower() and "bias" not in key.lower() and fval >= 1.0:
                anomalies.append(AnomalyReport(
                    metric=key,
                    value=value,
                    reason=f"Contractivity ρ={fval:.4f} >= 1.0",
                    severity="critical"
                ))
            
            if "bias" in key.lower() and fval > 1.05:
                anomalies.append(AnomalyReport(
                    metric=key,
                    value=value,
                    reason=f"Bias {fval:.4f} exceeds threshold 1.05",
                    severity="high"
                ))
    
    # Historical comparison if available
    if history and len(history) >= 5:
        # Calculate statistics from history
        for key in metrics.keys():
            historical_values = [h.get(key) for h in history if key in h]
            
            if len(historical_values) < 3:
                continue
            
            # Filter numeric values
            numeric_vals = []
            for v in historical_values:
                try:
                    numeric_vals.append(float(v))
                except:
                    continue
            
            if len(numeric_vals) < 3:
                continue
            
            # Calculate mean and std
            mean = sum(numeric_vals) / len(numeric_vals)
            variance = sum((x - mean) ** 2 for x in numeric_vals) / len(numeric_vals)
            std = math.sqrt(variance)
            
            # Check current value
            try:
                current = float(metrics[key])
                
                # Z-score check
                if std > 0:
                    z_score = abs(current - mean) / std
                    if z_score > 3.0:
                        anomalies.append(AnomalyReport(
                            metric=key,
                            value=current,
                            reason=f"Z-score {z_score:.2f} exceeds 3.0 (mean={mean:.4f}, std={std:.4f})",
                            severity="medium"
                        ))
            except:
                continue
    
    return anomalies


class ImmunitySystem:
    """Digital immunity system with memory and learning"""
    
    def __init__(self, trigger_threshold: float = 1.0):
        self.trigger_threshold = trigger_threshold
        self.history = []
        self.anomaly_history = []
        self.blocked_count = 0
        self.passed_count = 0
        
    def check(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check metrics for anomalies.
        
        Args:
            metrics: Metrics to check
        
        Returns:
            Dict with decision and details
        """
        # Calculate anomaly score
        score = anomaly_score(metrics)
        
        # Detect specific anomalies
        anomalies = detect_anomalies(metrics, self.history[-10:] if self.history else None)
        
        # Make decision
        safe = score < self.trigger_threshold
        
        # Critical anomalies override
        critical_anomalies = [a for a in anomalies if a.severity == "critical"]
        if critical_anomalies:
            safe = False
        
        # Update history
        self.history.append(metrics.copy())
        if len(self.history) > 100:
            self.history = self.history[-50:]
        
        # Update anomaly history
        for anomaly in anomalies:
            self.anomaly_history.append(anomaly.to_dict())
        if len(self.anomaly_history) > 1000:
            self.anomaly_history = self.anomaly_history[-500:]
        
        # Update counters
        if safe:
            self.passed_count += 1
        else:
            self.blocked_count += 1
        
        return {
            "safe": safe,
            "score": score,
            "threshold": self.trigger_threshold,
            "anomalies": [a.to_dict() for a in anomalies],
            "critical_count": len(critical_anomalies),
            "action": "proceed" if safe else "block"
        }
    
    def adapt_threshold(self, false_positive_rate: float = 0.05):
        """
        Adapt threshold based on history.
        
        Args:
            false_positive_rate: Target false positive rate
        """
        if len(self.history) < 20:
            return  # Not enough data
        
        # Calculate scores for recent history
        scores = [anomaly_score(h) for h in self.history[-50:]]
        
        if not scores:
            return
        
        # Sort scores
        scores.sort()
        
        # Find threshold for target false positive rate
        idx = int(len(scores) * (1 - false_positive_rate))
        idx = min(idx, len(scores) - 1)
        
        new_threshold = scores[idx]
        
        # Apply smoothing
        self.trigger_threshold = 0.7 * self.trigger_threshold + 0.3 * new_threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """Get immunity system statistics"""
        total = self.blocked_count + self.passed_count
        
        # Count anomaly types
        anomaly_types = {}
        for a in self.anomaly_history:
            reason = a.get("reason", "unknown")
            anomaly_types[reason] = anomaly_types.get(reason, 0) + 1
        
        return {
            "total_checks": total,
            "blocked": self.blocked_count,
            "passed": self.passed_count,
            "block_rate": self.blocked_count / max(total, 1),
            "current_threshold": self.trigger_threshold,
            "anomaly_types": anomaly_types,
            "recent_anomalies": self.anomaly_history[-10:]
        }
    
    def reset(self):
        """Reset immunity system"""
        self.history = []
        self.anomaly_history = []
        self.blocked_count = 0
        self.passed_count = 0