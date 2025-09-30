"""
Digital Immunity - Anomaly Detection and Fail-Closed Protection
==============================================================

Implements digital immunity system for detecting anomalies and triggering
fail-closed protection mechanisms.
"""

import time
import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AnomalyType(Enum):
    """Types of anomalies"""
    VALUE_OUT_OF_RANGE = "value_out_of_range"
    NAN_INF = "nan_inf"
    SUDDEN_SPIKE = "sudden_spike"
    PATTERN_DEVIATION = "pattern_deviation"
    SYSTEM_ERROR = "system_error"


@dataclass
class AnomalyAlert:
    """Anomaly alert"""
    timestamp: float
    anomaly_type: AnomalyType
    metric_name: str
    value: Any
    expected_range: Tuple[float, float]
    severity: float  # 0.0 to 1.0
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImmunityConfig:
    """Configuration for digital immunity"""
    anomaly_threshold: float = 1.0
    spike_threshold: float = 3.0  # Standard deviations
    pattern_window: int = 10
    max_anomalies_per_minute: int = 5
    auto_quarantine: bool = True
    quarantine_duration_s: float = 300.0  # 5 minutes


class DigitalImmunity:
    """Digital immunity system"""
    
    def __init__(self, config: ImmunityConfig = None):
        self.config = config or ImmunityConfig()
        self.anomaly_history: List[AnomalyAlert] = []
        self.metric_history: Dict[str, List[Tuple[float, Any]]] = {}
        self.quarantine_status: Dict[str, float] = {}  # metric_name -> quarantine_until
        self.immunity_score = 1.0  # Overall immunity score
        self.last_reset = time.time()
    
    def _is_value_valid(self, value: Any) -> bool:
        """Check if value is valid (not NaN, inf, etc.)"""
        if value is None:
            return False
        
        try:
            float_val = float(value)
            return math.isfinite(float_val)
        except (ValueError, TypeError):
            return False
    
    def _detect_value_anomaly(self, metric_name: str, value: Any, 
                             expected_range: Tuple[float, float]) -> Optional[AnomalyAlert]:
        """Detect value out of range anomaly"""
        if not self._is_value_valid(value):
            return AnomalyAlert(
                timestamp=time.time(),
                anomaly_type=AnomalyType.NAN_INF,
                metric_name=metric_name,
                value=value,
                expected_range=expected_range,
                severity=1.0,
                message=f"Invalid value detected: {value}"
            )
        
        try:
            float_val = float(value)
            min_val, max_val = expected_range
            
            if float_val < min_val or float_val > max_val:
                # Calculate severity based on deviation
                if float_val < min_val:
                    deviation = (min_val - float_val) / (max_val - min_val)
                else:
                    deviation = (float_val - max_val) / (max_val - min_val)
                
                severity = min(1.0, deviation)
                
                return AnomalyAlert(
                    timestamp=time.time(),
                    anomaly_type=AnomalyType.VALUE_OUT_OF_RANGE,
                    metric_name=metric_name,
                    value=value,
                    expected_range=expected_range,
                    severity=severity,
                    message=f"Value {float_val:.3f} outside range [{min_val:.3f}, {max_val:.3f}]"
                )
        except (ValueError, TypeError):
            return AnomalyAlert(
                timestamp=time.time(),
                anomaly_type=AnomalyType.SYSTEM_ERROR,
                metric_name=metric_name,
                value=value,
                expected_range=expected_range,
                severity=1.0,
                message=f"Error processing value: {value}"
            )
        
        return None
    
    def _detect_spike_anomaly(self, metric_name: str, value: Any) -> Optional[AnomalyAlert]:
        """Detect sudden spike anomaly"""
        if not self._is_value_valid(value):
            return None
        
        history = self.metric_history.get(metric_name, [])
        if len(history) < 3:
            return None
        
        try:
            float_val = float(value)
            recent_values = [float(h[1]) for h in history[-10:] if self._is_value_valid(h[1])]
            
            if len(recent_values) < 3:
                return None
            
            mean_val = statistics.mean(recent_values)
            std_val = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
            
            if std_val == 0:
                return None
            
            z_score = abs(float_val - mean_val) / std_val
            
            if z_score > self.config.spike_threshold:
                severity = min(1.0, z_score / self.config.spike_threshold)
                
                return AnomalyAlert(
                    timestamp=time.time(),
                    anomaly_type=AnomalyType.SUDDEN_SPIKE,
                    metric_name=metric_name,
                    value=value,
                    expected_range=(mean_val - 2*std_val, mean_val + 2*std_val),
                    severity=severity,
                    message=f"Sudden spike detected: z-score {z_score:.2f}"
                )
        except (ValueError, TypeError, statistics.StatisticsError):
            pass
        
        return None
    
    def _update_metric_history(self, metric_name: str, value: Any):
        """Update metric history"""
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = []
        
        self.metric_history[metric_name].append((time.time(), value))
        
        # Keep only recent history
        cutoff_time = time.time() - 3600  # 1 hour
        self.metric_history[metric_name] = [
            (t, v) for t, v in self.metric_history[metric_name]
            if t >= cutoff_time
        ]
    
    def _is_quarantined(self, metric_name: str) -> bool:
        """Check if metric is quarantined"""
        if metric_name not in self.quarantine_status:
            return False
        
        quarantine_until = self.quarantine_status[metric_name]
        if time.time() > quarantine_until:
            # Quarantine expired
            del self.quarantine_status[metric_name]
            return False
        
        return True
    
    def _quarantine_metric(self, metric_name: str):
        """Quarantine metric"""
        if self.config.auto_quarantine:
            self.quarantine_status[metric_name] = time.time() + self.config.quarantine_duration_s
    
    def _update_immunity_score(self):
        """Update overall immunity score"""
        if not self.anomaly_history:
            self.immunity_score = 1.0
            return
        
        # Recent anomalies (last hour)
        cutoff_time = time.time() - 3600
        recent_anomalies = [a for a in self.anomaly_history if a.timestamp >= cutoff_time]
        
        if not recent_anomalies:
            self.immunity_score = 1.0
            return
        
        # Calculate immunity based on anomaly frequency and severity
        total_severity = sum(a.severity for a in recent_anomalies)
        anomaly_rate = len(recent_anomalies) / 60  # per minute
        
        # Immunity decreases with anomalies
        immunity_factor = max(0.0, 1.0 - (total_severity * 0.1 + anomaly_rate * 0.2))
        self.immunity_score = immunity_factor
    
    def check_metrics(self, metrics: Dict[str, Any], 
                     expected_ranges: Dict[str, Tuple[float, float]] = None) -> Tuple[bool, List[AnomalyAlert]]:
        """
        Check metrics for anomalies
        
        Args:
            metrics: Dictionary of metric values
            expected_ranges: Expected ranges for metrics
            
        Returns:
            (all_ok, anomaly_alerts)
        """
        if expected_ranges is None:
            expected_ranges = {}
        
        anomalies = []
        
        for metric_name, value in metrics.items():
            # Skip quarantined metrics
            if self._is_quarantined(metric_name):
                continue
            
            # Update history
            self._update_metric_history(metric_name, value)
            
            # Check for value anomalies
            if metric_name in expected_ranges:
                anomaly = self._detect_value_anomaly(metric_name, value, expected_ranges[metric_name])
                if anomaly:
                    anomalies.append(anomaly)
            
            # Check for spike anomalies
            spike_anomaly = self._detect_spike_anomaly(metric_name, value)
            if spike_anomaly:
                anomalies.append(spike_anomaly)
        
        # Record anomalies
        for anomaly in anomalies:
            self.anomaly_history.append(anomaly)
            
            # Quarantine if severe
            if anomaly.severity > 0.8:
                self._quarantine_metric(anomaly.metric_name)
        
        # Update immunity score
        self._update_immunity_score()
        
        # Check if too many anomalies
        recent_anomalies = [a for a in self.anomaly_history 
                           if a.timestamp >= time.time() - 60]  # Last minute
        
        if len(recent_anomalies) > self.config.max_anomalies_per_minute:
            # System-wide anomaly
            system_anomaly = AnomalyAlert(
                timestamp=time.time(),
                anomaly_type=AnomalyType.SYSTEM_ERROR,
                metric_name="system",
                value=len(recent_anomalies),
                expected_range=(0, self.config.max_anomalies_per_minute),
                severity=1.0,
                message=f"Too many anomalies: {len(recent_anomalies)} in last minute"
            )
            anomalies.append(system_anomaly)
        
        all_ok = len(anomalies) == 0
        return all_ok, anomalies
    
    def guard(self, metrics: Dict[str, Any], 
              expected_ranges: Dict[str, Tuple[float, float]] = None,
              trigger: float = 1.0) -> bool:
        """
        Guard function for fail-closed protection
        
        Args:
            metrics: Dictionary of metric values
            expected_ranges: Expected ranges for metrics
            trigger: Threshold for triggering protection
            
        Returns:
            True if OK, False if protection triggered
        """
        all_ok, anomalies = self.check_metrics(metrics, expected_ranges)
        
        if not all_ok:
            # Check if any anomaly exceeds trigger threshold
            max_severity = max(a.severity for a in anomalies)
            if max_severity >= trigger:
                return False
        
        # Check immunity score
        if self.immunity_score < trigger:
            return False
        
        return True
    
    def get_immunity_status(self) -> Dict[str, Any]:
        """Get current immunity status"""
        recent_anomalies = [a for a in self.anomaly_history 
                           if a.timestamp >= time.time() - 3600]  # Last hour
        
        anomaly_counts = {}
        for anomaly in recent_anomalies:
            anomaly_type = anomaly.anomaly_type.value
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1
        
        return {
            "immunity_score": self.immunity_score,
            "quarantined_metrics": list(self.quarantine_status.keys()),
            "recent_anomalies": len(recent_anomalies),
            "anomaly_types": anomaly_counts,
            "total_metrics_tracked": len(self.metric_history),
            "last_reset": self.last_reset
        }
    
    def reset_immunity(self):
        """Reset immunity system"""
        self.anomaly_history.clear()
        self.metric_history.clear()
        self.quarantine_status.clear()
        self.immunity_score = 1.0
        self.last_reset = time.time()


# Integration with Life Equation
def integrate_immunity_in_life_equation(
    life_verdict: Dict[str, Any],
    immunity: DigitalImmunity = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Integrate digital immunity into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        immunity: Digital immunity instance
        
    Returns:
        (immunity_ok, immunity_details)
    """
    if immunity is None:
        immunity = DigitalImmunity()
    
    # Extract metrics from life verdict
    metrics = life_verdict.get("metrics", {})
    
    # Define expected ranges for key metrics
    expected_ranges = {
        "alpha_eff": (0.0, 1.0),
        "phi": (0.0, 1.0),
        "sr": (0.0, 1.0),
        "G": (0.0, 1.0),
        "L_inf": (0.0, 1.0),
        "dL_inf": (-1.0, 1.0),
        "rho": (0.0, 2.0)
    }
    
    # Check immunity
    immunity_ok = immunity.guard(metrics, expected_ranges, trigger=0.8)
    
    # Get immunity status
    immunity_status = immunity.get_immunity_status()
    
    immunity_details = {
        "immunity_ok": immunity_ok,
        "immunity_score": immunity_status["immunity_score"],
        "quarantined_metrics": immunity_status["quarantined_metrics"],
        "recent_anomalies": immunity_status["recent_anomalies"],
        "anomaly_types": immunity_status["anomaly_types"]
    }
    
    return immunity_ok, immunity_details


# Example usage
if __name__ == "__main__":
    # Create immunity system
    immunity = DigitalImmunity()
    
    # Test with normal metrics
    normal_metrics = {
        "alpha_eff": 0.5,
        "phi": 0.7,
        "sr": 0.8,
        "G": 0.9
    }
    
    expected_ranges = {
        "alpha_eff": (0.0, 1.0),
        "phi": (0.0, 1.0),
        "sr": (0.0, 1.0),
        "G": (0.0, 1.0)
    }
    
    ok, anomalies = immunity.check_metrics(normal_metrics, expected_ranges)
    print(f"Normal metrics: OK={ok}, anomalies={len(anomalies)}")
    
    # Test with anomalous metrics
    anomalous_metrics = {
        "alpha_eff": 2.0,  # Out of range
        "phi": float('inf'),  # Invalid
        "sr": 0.8,
        "G": 0.9
    }
    
    ok, anomalies = immunity.check_metrics(anomalous_metrics, expected_ranges)
    print(f"Anomalous metrics: OK={ok}, anomalies={len(anomalies)}")
    
    for anomaly in anomalies:
        print(f"  - {anomaly.anomaly_type.value}: {anomaly.message}")
    
    # Get immunity status
    status = immunity.get_immunity_status()
    print(f"Immunity status: {status}")