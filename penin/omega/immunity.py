"""
Digital Immunity - Anomaly detection and fail-closed protection
Detects abnormal metrics and triggers protective responses
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class AnomalyReport:
    """Report of detected anomalies"""
    timestamp: float
    anomaly_score: float
    violations: List[str]
    metrics: Dict[str, Any]
    action: str  # "allow", "warn", "block"


def anomaly_score(metrics: dict) -> float:
    """
    Compute anomaly score for metrics
    
    Higher score = more anomalous
    Score > 1.0 typically indicates issues
    
    Parameters:
    -----------
    metrics: Dictionary of metric values
    
    Returns:
    --------
    Anomaly score (0 = normal, higher = more anomalous)
    """
    score = 0.0
    violations = []
    
    for key, value in metrics.items():
        try:
            val = float(value)
            
            # Check for NaN
            if math.isnan(val):
                score += 2.0
                violations.append(f"{key}: NaN")
                continue
            
            # Check for infinity
            if math.isinf(val):
                score += 2.0
                violations.append(f"{key}: Infinity")
                continue
            
            # Check for negative values where unexpected
            if key in ["accuracy", "precision", "recall", "f1", "phi", "sr", "G"]:
                if val < 0.0:
                    score += 1.0
                    violations.append(f"{key}: Negative ({val})")
            
            # Check for values outside [0, 1] for probabilities
            if key in ["accuracy", "precision", "recall", "f1", "confidence", "probability"]:
                if val < 0.0 or val > 1.0:
                    score += 0.5
                    violations.append(f"{key}: Out of bounds ({val})")
            
            # Check for absurdly large values
            if val > 1e6:
                score += 0.5
                violations.append(f"{key}: Too large ({val:.2e})")
            
            # Check for suspiciously perfect values
            if key in ["accuracy", "precision", "recall"] and val == 1.0:
                score += 0.2  # Mild concern
                
        except (ValueError, TypeError):
            # Non-numeric value where numeric expected
            score += 0.5
            violations.append(f"{key}: Non-numeric")
    
    return score


def guard(metrics: dict, trigger: float = 1.0) -> bool:
    """
    Immunity guard - fail-closed protection
    
    Parameters:
    -----------
    metrics: Metrics to check
    trigger: Anomaly score threshold for blocking
    
    Returns:
    --------
    True if OK to proceed, False to block (fail-closed)
    """
    score = anomaly_score(metrics)
    return score < trigger


def detect_anomalies(
    metrics: dict,
    history: Optional[List[dict]] = None,
    thresholds: Optional[Dict[str, Tuple[float, float]]] = None
) -> AnomalyReport:
    """
    Comprehensive anomaly detection with history comparison
    
    Parameters:
    -----------
    metrics: Current metrics
    history: Optional historical metrics for comparison
    thresholds: Optional per-metric (min, max) thresholds
    
    Returns:
    --------
    Anomaly report with score, violations, and recommended action
    """
    violations = []
    base_score = anomaly_score(metrics)
    
    # Check against explicit thresholds
    if thresholds:
        for key, (min_val, max_val) in thresholds.items():
            if key in metrics:
                try:
                    val = float(metrics[key])
                    if val < min_val:
                        violations.append(f"{key} < {min_val} (got {val})")
                        base_score += 0.5
                    elif val > max_val:
                        violations.append(f"{key} > {max_val} (got {val})")
                        base_score += 0.5
                except (ValueError, TypeError):
                    pass
    
    # Check against history (detect sudden changes)
    if history and len(history) >= 3:
        for key in metrics:
            if key in history[-1]:
                try:
                    current = float(metrics[key])
                    historical_values = [float(h.get(key, 0)) for h in history[-3:]]
                    
                    if historical_values:
                        mean_historical = sum(historical_values) / len(historical_values)
                        
                        # Check for sudden jumps
                        if mean_historical != 0:
                            change_ratio = abs(current - mean_historical) / abs(mean_historical)
                            if change_ratio > 2.0:  # More than 200% change
                                violations.append(f"{key}: Sudden change ({change_ratio:.1f}x)")
                                base_score += 0.3
                                
                except (ValueError, TypeError):
                    pass
    
    # Determine action based on score
    if base_score >= 2.0:
        action = "block"
    elif base_score >= 1.0:
        action = "warn"
    else:
        action = "allow"
    
    return AnomalyReport(
        timestamp=time.time(),
        anomaly_score=base_score,
        violations=violations,
        metrics=metrics,
        action=action
    )


def immune_response(report: AnomalyReport) -> Dict[str, Any]:
    """
    Generate immune response based on anomaly report
    
    Parameters:
    -----------
    report: Anomaly report
    
    Returns:
    --------
    Response dictionary with actions to take
    """
    response = {
        "timestamp": report.timestamp,
        "severity": "normal",
        "actions": [],
        "rollback": False,
        "throttle": 1.0,  # Multiplier for alpha/learning rate
        "alert": False
    }
    
    if report.action == "block":
        response["severity"] = "critical"
        response["actions"] = [
            "halt_evolution",
            "rollback_to_checkpoint",
            "alert_operator"
        ]
        response["rollback"] = True
        response["throttle"] = 0.0  # Stop all learning
        response["alert"] = True
        
    elif report.action == "warn":
        response["severity"] = "warning"
        response["actions"] = [
            "reduce_learning_rate",
            "increase_monitoring",
            "save_checkpoint"
        ]
        response["throttle"] = 0.5  # Reduce learning rate by half
        response["alert"] = False
    
    return response


def pattern_detection(history: List[dict], window: int = 10) -> Dict[str, Any]:
    """
    Detect patterns in metric history that might indicate issues
    
    Parameters:
    -----------
    history: Metric history
    window: Window size for pattern detection
    
    Returns:
    --------
    Dictionary of detected patterns
    """
    if len(history) < window:
        return {"insufficient_data": True}
    
    recent = history[-window:]
    patterns = {
        "oscillation": False,
        "degradation": False,
        "plateau": False,
        "explosion": False
    }
    
    # Check each metric for patterns
    metrics_to_check = set()
    for h in recent:
        metrics_to_check.update(h.keys())
    
    for metric in metrics_to_check:
        try:
            values = [float(h.get(metric, 0)) for h in recent]
            
            if len(values) < 3:
                continue
            
            # Oscillation: values alternating up and down
            direction_changes = 0
            for i in range(2, len(values)):
                if (values[i] - values[i-1]) * (values[i-1] - values[i-2]) < 0:
                    direction_changes += 1
            
            if direction_changes > len(values) * 0.6:
                patterns["oscillation"] = True
            
            # Degradation: consistent downward trend
            if all(values[i] <= values[i-1] for i in range(1, len(values))):
                if values[-1] < values[0] * 0.8:  # 20% degradation
                    patterns["degradation"] = True
            
            # Plateau: no significant change
            if values:
                mean_val = sum(values) / len(values)
                if mean_val != 0:
                    variance = sum((v - mean_val)**2 for v in values) / len(values)
                    if variance / (mean_val**2) < 0.001:  # Very low relative variance
                        patterns["plateau"] = True
            
            # Explosion: rapid growth
            if len(values) >= 2:
                if values[-1] > values[0] * 10:  # 10x growth
                    patterns["explosion"] = True
                    
        except (ValueError, TypeError):
            continue
    
    return patterns


def adaptive_thresholds(history: List[dict], confidence: float = 0.95) -> Dict[str, Tuple[float, float]]:
    """
    Compute adaptive thresholds based on historical data
    
    Parameters:
    -----------
    history: Historical metrics
    confidence: Confidence level for thresholds
    
    Returns:
    --------
    Dictionary of (min, max) thresholds per metric
    """
    if len(history) < 10:
        return {}
    
    thresholds = {}
    
    # Collect all metrics
    metrics_to_analyze = set()
    for h in history:
        metrics_to_analyze.update(h.keys())
    
    for metric in metrics_to_analyze:
        try:
            values = [float(h.get(metric, 0)) for h in history if metric in h]
            
            if len(values) < 5:
                continue
            
            # Simple statistical bounds
            mean_val = sum(values) / len(values)
            variance = sum((v - mean_val)**2 for v in values) / len(values)
            std_dev = variance ** 0.5
            
            # Use z-score for confidence interval
            z_score = 2.58 if confidence >= 0.99 else 1.96 if confidence >= 0.95 else 1.645
            
            min_threshold = mean_val - z_score * std_dev
            max_threshold = mean_val + z_score * std_dev
            
            thresholds[metric] = (min_threshold, max_threshold)
            
        except (ValueError, TypeError):
            continue
    
    return thresholds


def quick_test():
    """Quick test of immunity system"""
    # Test normal metrics
    normal_metrics = {
        "accuracy": 0.85,
        "loss": 0.15,
        "phi": 0.7,
        "sr": 0.8
    }
    
    # Test anomalous metrics
    anomalous_metrics = {
        "accuracy": 1.5,  # Out of bounds
        "loss": float('nan'),  # NaN
        "phi": -0.3,  # Negative
        "sr": 1e9  # Too large
    }
    
    # Test with history
    history = [
        {"accuracy": 0.80, "loss": 0.20},
        {"accuracy": 0.82, "loss": 0.18},
        {"accuracy": 0.84, "loss": 0.16}
    ]
    
    sudden_change_metrics = {
        "accuracy": 0.2,  # Sudden drop
        "loss": 0.8  # Sudden increase
    }
    
    # Run tests
    normal_score = anomaly_score(normal_metrics)
    anomalous_score = anomaly_score(anomalous_metrics)
    
    normal_guard = guard(normal_metrics)
    anomalous_guard = guard(anomalous_metrics)
    
    sudden_report = detect_anomalies(sudden_change_metrics, history)
    response = immune_response(sudden_report)
    
    patterns = pattern_detection(history + [sudden_change_metrics])
    adaptive = adaptive_thresholds(history)
    
    return {
        "normal_score": normal_score,
        "anomalous_score": anomalous_score,
        "normal_guard": normal_guard,
        "anomalous_guard": anomalous_guard,
        "sudden_action": sudden_report.action,
        "response_severity": response["severity"],
        "patterns_detected": [k for k, v in patterns.items() if v],
        "adaptive_thresholds": len(adaptive)
    }


if __name__ == "__main__":
    result = quick_test()
    print("Digital Immunity Test:")
    print(f"  Normal score: {result['normal_score']:.2f} (guard: {result['normal_guard']})")
    print(f"  Anomalous score: {result['anomalous_score']:.2f} (guard: {result['anomalous_guard']})")
    print(f"  Sudden change action: {result['sudden_action']}")
    print(f"  Response severity: {result['response_severity']}")
    print(f"  Patterns detected: {result['patterns_detected']}")
    print(f"  Adaptive thresholds computed: {result['adaptive_thresholds']}")