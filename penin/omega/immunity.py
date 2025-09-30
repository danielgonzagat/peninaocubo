"""
Digital Immunity System
=======================

Implements anomaly detection and fail-closed behavior.
Detects invalid metrics and triggers rollback mechanisms.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AnomalyType(Enum):
    """Types of anomalies"""
    NUMERICAL_INVALID = "numerical_invalid"
    OUT_OF_RANGE = "out_of_range"
    NAN_VALUE = "nan_value"
    INFINITE_VALUE = "infinite_value"
    NEGATIVE_UNEXPECTED = "negative_unexpected"
    SPIKE_DETECTED = "spike_detected"
    TREND_ANOMALY = "trend_anomaly"


class ImmunityStatus(Enum):
    """Immunity system status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class Anomaly:
    """Anomaly detection result"""
    anomaly_type: AnomalyType
    metric_name: str
    value: Any
    expected_range: Tuple[float, float]
    severity: float  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "metric_name": self.metric_name,
            "value": self.value,
            "expected_range": self.expected_range,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "description": self.description
        }


class ImmunitySystem:
    """Digital immunity system"""
    
    def __init__(self, trigger_threshold: float = 1.0):
        self.trigger_threshold = trigger_threshold
        self.anomaly_history: List[Anomaly] = []
        self.metric_history: Dict[str, List[Tuple[float, float]]] = {}  # metric -> [(value, timestamp)]
        self.status = ImmunityStatus.HEALTHY
        self.last_check_time = 0
        
        # Metric ranges for validation
        self.metric_ranges = {
            "alpha_eff": (0.0, 1.0),
            "phi": (0.0, 1.0),
            "sr": (0.0, 1.0),
            "G": (0.0, 1.0),
            "L_inf": (0.0, 1.0),
            "dL_inf": (-1.0, 1.0),
            "rho": (0.0, 2.0),
            "ece": (0.0, 1.0),
            "rho_bias": (0.0, 10.0),
            "cost": (0.0, 1000.0),
            "latency_s": (0.0, 60.0),
            "memory_usage": (0.0, 1.0),
            "cpu_usage": (0.0, 1.0)
        }
    
    def anomaly_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate anomaly score for metrics
        
        Args:
            metrics: Dictionary of metrics
            
        Returns:
            Anomaly score (0.0 = no anomalies, 1.0+ = severe anomalies)
        """
        total_score = 0.0
        anomaly_count = 0
        
        for metric_name, value in metrics.items():
            score = self._check_metric_anomaly(metric_name, value)
            total_score += score
            if score > 0:
                anomaly_count += 1
        
        # Normalize by number of metrics
        if len(metrics) > 0:
            avg_score = total_score / len(metrics)
        else:
            avg_score = 0.0
        
        # Boost score if multiple anomalies
        if anomaly_count > 1:
            avg_score *= (1.0 + 0.1 * anomaly_count)
        
        return min(avg_score, 10.0)  # Cap at 10.0
    
    def _check_metric_anomaly(self, metric_name: str, value: Any) -> float:
        """Check individual metric for anomalies"""
        score = 0.0
        
        # Check for NaN
        if isinstance(value, float) and math.isnan(value):
            self._record_anomaly(AnomalyType.NAN_VALUE, metric_name, value, (0.0, 1.0), 1.0)
            return 1.0
        
        # Check for infinite values
        if isinstance(value, float) and math.isinf(value):
            self._record_anomaly(AnomalyType.INFINITE_VALUE, metric_name, value, (0.0, 1.0), 1.0)
            return 1.0
        
        # Check for negative values where not expected
        if isinstance(value, (int, float)) and value < 0:
            if metric_name in ["alpha_eff", "phi", "sr", "G", "L_inf", "ece", "memory_usage", "cpu_usage"]:
                self._record_anomaly(AnomalyType.NEGATIVE_UNEXPECTED, metric_name, value, (0.0, 1.0), 0.8)
                score += 0.8
        
        # Check for out-of-range values
        if metric_name in self.metric_ranges:
            min_val, max_val = self.metric_ranges[metric_name]
            if isinstance(value, (int, float)):
                if value < min_val or value > max_val:
                    severity = min(1.0, abs(value - min_val) / (max_val - min_val) if max_val > min_val else 1.0)
                    self._record_anomaly(AnomalyType.OUT_OF_RANGE, metric_name, value, (min_val, max_val), severity)
                    score += severity
        
        # Check for extreme values (beyond reasonable bounds)
        if isinstance(value, (int, float)):
            if abs(value) > 1e6:  # Very large numbers
                self._record_anomaly(AnomalyType.NUMERICAL_INVALID, metric_name, value, (-1e6, 1e6), 0.9)
                score += 0.9
        
        return score
    
    def _record_anomaly(self, anomaly_type: AnomalyType, metric_name: str, value: Any, 
                       expected_range: Tuple[float, float], severity: float) -> None:
        """Record anomaly"""
        anomaly = Anomaly(
            anomaly_type=anomaly_type,
            metric_name=metric_name,
            value=value,
            expected_range=expected_range,
            severity=severity,
            description=f"{anomaly_type.value} in {metric_name}: {value}"
        )
        
        self.anomaly_history.append(anomaly)
        
        # Keep only recent anomalies
        cutoff_time = time.time() - 3600  # 1 hour
        self.anomaly_history = [a for a in self.anomaly_history if a.timestamp > cutoff_time]
    
    def guard(self, metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
        """
        Guard function - returns True if OK, False if fail-closed
        
        Args:
            metrics: Metrics to check
            trigger: Trigger threshold
            
        Returns:
            True if OK, False if fail-closed
        """
        anomaly_score = self.anomaly_score(metrics)
        
        # Update status
        if anomaly_score < trigger * 0.5:
            self.status = ImmunityStatus.HEALTHY
        elif anomaly_score < trigger:
            self.status = ImmunityStatus.WARNING
        elif anomaly_score < trigger * 2:
            self.status = ImmunityStatus.CRITICAL
        else:
            self.status = ImmunityStatus.FAILED
        
        self.last_check_time = time.time()
        
        # Fail-closed if anomaly score exceeds trigger
        return anomaly_score < trigger
    
    def detect_spikes(self, metric_name: str, window_size: int = 10) -> List[Anomaly]:
        """Detect spikes in metric values"""
        if metric_name not in self.metric_history:
            return []
        
        history = self.metric_history[metric_name]
        if len(history) < window_size:
            return []
        
        recent_values = [value for value, _ in history[-window_size:]]
        spikes = []
        
        # Calculate moving average and standard deviation
        mean_val = sum(recent_values) / len(recent_values)
        variance = sum((v - mean_val) ** 2 for v in recent_values) / len(recent_values)
        std_dev = math.sqrt(variance)
        
        # Detect spikes (values > 3 standard deviations from mean)
        for i, value in enumerate(recent_values):
            if abs(value - mean_val) > 3 * std_dev and std_dev > 0:
                spike_anomaly = Anomaly(
                    anomaly_type=AnomalyType.SPIKE_DETECTED,
                    metric_name=metric_name,
                    value=value,
                    expected_range=(mean_val - 3 * std_dev, mean_val + 3 * std_dev),
                    severity=min(1.0, abs(value - mean_val) / (3 * std_dev)),
                    description=f"Spike detected in {metric_name}: {value} (mean: {mean_val:.3f}, std: {std_dev:.3f})"
                )
                spikes.append(spike_anomaly)
        
        return spikes
    
    def update_metric_history(self, metrics: Dict[str, Any]) -> None:
        """Update metric history for trend analysis"""
        current_time = time.time()
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and not math.isnan(value) and not math.isinf(value):
                if metric_name not in self.metric_history:
                    self.metric_history[metric_name] = []
                
                self.metric_history[metric_name].append((value, current_time))
                
                # Keep only recent history (1 hour)
                cutoff_time = current_time - 3600
                self.metric_history[metric_name] = [
                    (v, t) for v, t in self.metric_history[metric_name] if t > cutoff_time
                ]
    
    def get_immunity_stats(self) -> Dict[str, Any]:
        """Get immunity system statistics"""
        recent_anomalies = [a for a in self.anomaly_history if time.time() - a.timestamp < 3600]
        
        anomaly_counts = {}
        for anomaly in recent_anomalies:
            anomaly_type = anomaly.anomaly_type.value
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1
        
        return {
            "status": self.status.value,
            "total_anomalies": len(self.anomaly_history),
            "recent_anomalies": len(recent_anomalies),
            "anomaly_types": anomaly_counts,
            "last_check_time": self.last_check_time,
            "tracked_metrics": len(self.metric_history),
            "trigger_threshold": self.trigger_threshold
        }
    
    def get_anomaly_report(self, hours: int = 1) -> Dict[str, Any]:
        """Get detailed anomaly report"""
        cutoff_time = time.time() - (hours * 3600)
        recent_anomalies = [a for a in self.anomaly_history if a.timestamp > cutoff_time]
        
        if not recent_anomalies:
            return {
                "period_hours": hours,
                "anomaly_count": 0,
                "anomalies": [],
                "summary": "No anomalies detected"
            }
        
        # Group by metric
        by_metric = {}
        for anomaly in recent_anomalies:
            metric = anomaly.metric_name
            if metric not in by_metric:
                by_metric[metric] = []
            by_metric[metric].append(anomaly.to_dict())
        
        # Calculate severity distribution
        severity_dist = {"low": 0, "medium": 0, "high": 0}
        for anomaly in recent_anomalies:
            if anomaly.severity < 0.3:
                severity_dist["low"] += 1
            elif anomaly.severity < 0.7:
                severity_dist["medium"] += 1
            else:
                severity_dist["high"] += 1
        
        return {
            "period_hours": hours,
            "anomaly_count": len(recent_anomalies),
            "anomalies_by_metric": by_metric,
            "severity_distribution": severity_dist,
            "most_problematic_metric": max(by_metric.keys(), key=lambda k: len(by_metric[k])) if by_metric else None,
            "summary": f"{len(recent_anomalies)} anomalies detected in {hours} hour(s)"
        }
    
    def reset_immunity(self) -> None:
        """Reset immunity system"""
        self.anomaly_history.clear()
        self.metric_history.clear()
        self.status = ImmunityStatus.HEALTHY
        self.last_check_time = 0


# Global immunity instance
_global_immunity: Optional[ImmunitySystem] = None


def get_global_immunity() -> ImmunitySystem:
    """Get global immunity system instance"""
    global _global_immunity
    
    if _global_immunity is None:
        _global_immunity = ImmunitySystem()
    
    return _global_immunity


def anomaly_score(metrics: Dict[str, Any]) -> float:
    """Convenience function to calculate anomaly score"""
    immunity = get_global_immunity()
    return immunity.anomaly_score(metrics)


def guard(metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
    """Convenience function for immunity guard"""
    immunity = get_global_immunity()
    return immunity.guard(metrics, trigger)


def test_immunity_system() -> Dict[str, Any]:
    """Test immunity system functionality"""
    immunity = get_global_immunity()
    
    # Reset system
    immunity.reset_immunity()
    
    # Test with normal metrics
    normal_metrics = {
        "alpha_eff": 0.02,
        "phi": 0.7,
        "sr": 0.85,
        "G": 0.9,
        "L_inf": 0.8,
        "dL_inf": 0.01,
        "rho": 0.95,
        "ece": 0.005,
        "cost": 0.02
    }
    
    normal_score = immunity.anomaly_score(normal_metrics)
    normal_guard = immunity.guard(normal_metrics)
    
    # Test with anomalous metrics
    anomalous_metrics = {
        "alpha_eff": float('nan'),  # NaN
        "phi": 1.5,  # Out of range
        "sr": -0.1,  # Negative unexpected
        "G": float('inf'),  # Infinite
        "L_inf": 0.8,
        "dL_inf": 0.01,
        "rho": 0.95,
        "ece": 0.005,
        "cost": 0.02
    }
    
    anomalous_score = immunity.anomaly_score(anomalous_metrics)
    anomalous_guard = immunity.guard(anomalous_metrics)
    
    # Get stats
    stats = immunity.get_immunity_stats()
    report = immunity.get_anomaly_report()
    
    return {
        "normal_score": normal_score,
        "normal_guard": normal_guard,
        "anomalous_score": anomalous_score,
        "anomalous_guard": anomalous_guard,
        "immunity_stats": stats,
        "anomaly_report": report
    }