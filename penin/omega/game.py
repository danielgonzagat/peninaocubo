"""
GAME - Gradientes com Memória Exponencial
==========================================

Implements EMA-based gradient calculation with exponential memory.
Provides smooth gradient estimation for evolution parameters.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import numpy as np


@dataclass
class GradientPoint:
    """Single gradient measurement point"""
    timestamp: float
    value: float
    gradient: float
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "gradient": self.gradient,
            "weight": self.weight
        }


@dataclass
class EMAParams:
    """EMA parameters"""
    alpha: float  # Smoothing factor (0 < alpha <= 1)
    beta: float   # Gradient smoothing factor
    gamma: float  # Weight decay factor
    min_samples: int = 5  # Minimum samples for reliable gradient
    
    def __post_init__(self):
        # Ensure valid ranges
        self.alpha = max(0.001, min(1.0, self.alpha))
        self.beta = max(0.001, min(1.0, self.beta))
        self.gamma = max(0.001, min(1.0, self.gamma))
        self.min_samples = max(1, self.min_samples)


class GAMEEngine:
    """GAME - Gradientes com Memória Exponencial"""
    
    def __init__(self, params: Optional[EMAParams] = None):
        if params is None:
            params = EMAParams(
                alpha=0.1,    # Moderate smoothing
                beta=0.05,    # Gradient smoothing
                gamma=0.99,   # Weight decay
                min_samples=5
            )
        
        self.params = params
        
        # State variables
        self.ema_value: Optional[float] = None
        self.ema_gradient: Optional[float] = None
        self.ema_weight: float = 0.0
        
        # History for analysis
        self.history: List[GradientPoint] = []
        self.max_history = 1000
        
        # Gradient calculation
        self.last_value: Optional[float] = None
        self.last_timestamp: Optional[float] = None
        
        # Performance tracking
        self.total_updates = 0
        self.last_update_time = 0.0
    
    def update(self, value: float, timestamp: Optional[float] = None) -> Dict[str, float]:
        """
        Update GAME with new value
        
        Args:
            value: New measurement value
            timestamp: Timestamp (defaults to current time)
            
        Returns:
            Dictionary with updated metrics
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Calculate gradient
        gradient = self._calculate_gradient(value, timestamp)
        
        # Update EMA
        self._update_ema(value, gradient, timestamp)
        
        # Add to history
        point = GradientPoint(
            timestamp=timestamp,
            value=value,
            gradient=gradient,
            weight=self.ema_weight
        )
        self.history.append(point)
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Update tracking
        self.total_updates += 1
        self.last_update_time = timestamp
        
        return {
            "value": value,
            "ema_value": self.ema_value or 0.0,
            "ema_gradient": self.ema_gradient or 0.0,
            "ema_weight": self.ema_weight,
            "gradient": gradient,
            "timestamp": timestamp
        }
    
    def _calculate_gradient(self, value: float, timestamp: float) -> float:
        """Calculate gradient from current and previous values"""
        if self.last_value is None or self.last_timestamp is None:
            return 0.0
        
        # Time difference
        dt = timestamp - self.last_timestamp
        
        if dt <= 0:
            return 0.0
        
        # Value difference
        dv = value - self.last_value
        
        # Gradient (rate of change)
        gradient = dv / dt
        
        # Store for next iteration
        self.last_value = value
        self.last_timestamp = timestamp
        
        return gradient
    
    def _update_ema(self, value: float, gradient: float, timestamp: float) -> None:
        """Update exponential moving averages"""
        # Update weight (exponential decay)
        self.ema_weight = self.params.gamma * self.ema_weight + 1.0
        
        # Update EMA value
        if self.ema_value is None:
            self.ema_value = value
        else:
            # Weighted update
            weight = 1.0 / self.ema_weight
            self.ema_value = (1.0 - self.params.alpha * weight) * self.ema_value + \
                           self.params.alpha * weight * value
        
        # Update EMA gradient
        if self.ema_gradient is None:
            self.ema_gradient = gradient
        else:
            # Weighted update
            weight = 1.0 / self.ema_weight
            self.ema_gradient = (1.0 - self.params.beta * weight) * self.ema_gradient + \
                              self.params.beta * weight * gradient
    
    def get_current_gradient(self) -> Optional[float]:
        """Get current EMA gradient"""
        return self.ema_gradient
    
    def get_current_value(self) -> Optional[float]:
        """Get current EMA value"""
        return self.ema_value
    
    def get_gradient_trend(self, window: int = 10) -> Dict[str, float]:
        """Analyze gradient trend over recent window"""
        if len(self.history) < window:
            return {
                "trend": 0.0,
                "volatility": 0.0,
                "acceleration": 0.0,
                "confidence": 0.0
            }
        
        # Get recent points
        recent_points = self.history[-window:]
        
        # Calculate trend (linear regression slope)
        timestamps = [p.timestamp for p in recent_points]
        gradients = [p.gradient for p in recent_points]
        
        if len(timestamps) < 2:
            return {
                "trend": 0.0,
                "volatility": 0.0,
                "acceleration": 0.0,
                "confidence": 0.0
            }
        
        # Linear regression
        n = len(timestamps)
        sum_t = sum(timestamps)
        sum_g = sum(gradients)
        sum_tg = sum(t * g for t, g in zip(timestamps, gradients))
        sum_t2 = sum(t * t for t in timestamps)
        
        # Calculate slope (trend)
        denominator = n * sum_t2 - sum_t * sum_t
        if denominator != 0:
            trend = (n * sum_tg - sum_t * sum_g) / denominator
        else:
            trend = 0.0
        
        # Calculate volatility (standard deviation)
        mean_gradient = sum_g / n
        variance = sum((g - mean_gradient) ** 2 for g in gradients) / n
        volatility = math.sqrt(variance)
        
        # Calculate acceleration (second derivative approximation)
        if len(gradients) >= 3:
            acceleration = gradients[-1] - 2 * gradients[-2] + gradients[-3]
        else:
            acceleration = 0.0
        
        # Calculate confidence (based on consistency)
        confidence = 1.0 / (1.0 + volatility) if volatility > 0 else 1.0
        
        return {
            "trend": trend,
            "volatility": volatility,
            "acceleration": acceleration,
            "confidence": confidence
        }
    
    def predict_next_value(self, steps: int = 1) -> Optional[float]:
        """Predict next value based on current gradient"""
        if self.ema_value is None or self.ema_gradient is None:
            return None
        
        # Simple linear prediction
        predicted_value = self.ema_value + self.ema_gradient * steps
        
        return predicted_value
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get GAME performance metrics"""
        if not self.history:
            return {
                "total_updates": 0,
                "ema_value": None,
                "ema_gradient": None,
                "ema_weight": 0.0,
                "history_length": 0,
                "last_update_time": 0.0
            }
        
        # Calculate recent statistics
        recent_window = min(20, len(self.history))
        recent_points = self.history[-recent_window:]
        
        recent_values = [p.value for p in recent_points]
        recent_gradients = [p.gradient for p in recent_points]
        
        return {
            "total_updates": self.total_updates,
            "ema_value": self.ema_value,
            "ema_gradient": self.ema_gradient,
            "ema_weight": self.ema_weight,
            "history_length": len(self.history),
            "last_update_time": self.last_update_time,
            "recent_value_mean": sum(recent_values) / len(recent_values),
            "recent_value_std": math.sqrt(sum((v - sum(recent_values)/len(recent_values))**2 for v in recent_values) / len(recent_values)),
            "recent_gradient_mean": sum(recent_gradients) / len(recent_gradients),
            "recent_gradient_std": math.sqrt(sum((g - sum(recent_gradients)/len(recent_gradients))**2 for g in recent_gradients) / len(recent_gradients)),
            "params": {
                "alpha": self.params.alpha,
                "beta": self.params.beta,
                "gamma": self.params.gamma,
                "min_samples": self.params.min_samples
            }
        }
    
    def reset(self) -> None:
        """Reset GAME state"""
        self.ema_value = None
        self.ema_gradient = None
        self.ema_weight = 0.0
        self.history.clear()
        self.last_value = None
        self.last_timestamp = None
        self.total_updates = 0
        self.last_update_time = 0.0
    
    def export_history(self) -> List[Dict[str, Any]]:
        """Export gradient history"""
        return [point.to_dict() for point in self.history]


class GAMEManager:
    """Manages multiple GAME engines for different metrics"""
    
    def __init__(self):
        self.engines: Dict[str, GAMEEngine] = {}
        self.default_params = EMAParams(alpha=0.1, beta=0.05, gamma=0.99, min_samples=5)
    
    def get_engine(self, metric_name: str, params: Optional[EMAParams] = None) -> GAMEEngine:
        """Get or create GAME engine for metric"""
        if metric_name not in self.engines:
            engine_params = params or self.default_params
            self.engines[metric_name] = GAMEEngine(engine_params)
        
        return self.engines[metric_name]
    
    def update_metric(self, metric_name: str, value: float, 
                     timestamp: Optional[float] = None) -> Dict[str, float]:
        """Update metric in GAME engine"""
        engine = self.get_engine(metric_name)
        return engine.update(value, timestamp)
    
    def get_metric_gradient(self, metric_name: str) -> Optional[float]:
        """Get current gradient for metric"""
        if metric_name not in self.engines:
            return None
        
        return self.engines[metric_name].get_current_gradient()
    
    def get_all_gradients(self) -> Dict[str, Optional[float]]:
        """Get gradients for all tracked metrics"""
        return {
            metric_name: engine.get_current_gradient()
            for metric_name, engine in self.engines.items()
        }
    
    def get_metric_trend(self, metric_name: str, window: int = 10) -> Dict[str, float]:
        """Get trend analysis for metric"""
        if metric_name not in self.engines:
            return {"trend": 0.0, "volatility": 0.0, "acceleration": 0.0, "confidence": 0.0}
        
        return self.engines[metric_name].get_gradient_trend(window)
    
    def get_all_trends(self, window: int = 10) -> Dict[str, Dict[str, float]]:
        """Get trend analysis for all metrics"""
        return {
            metric_name: engine.get_gradient_trend(window)
            for metric_name, engine in self.engines.items()
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            "total_metrics": len(self.engines),
            "metric_names": list(self.engines.keys()),
            "engines_stats": {
                metric_name: engine.get_performance_metrics()
                for metric_name, engine in self.engines.items()
            }
        }


# Global GAME manager instance
_global_game_manager: Optional[GAMEManager] = None


def get_global_game_manager() -> GAMEManager:
    """Get global GAME manager instance"""
    global _global_game_manager
    
    if _global_game_manager is None:
        _global_game_manager = GAMEManager()
    
    return _global_game_manager


def update_gradient(metric_name: str, value: float, timestamp: Optional[float] = None) -> Dict[str, float]:
    """Convenience function to update gradient"""
    manager = get_global_game_manager()
    return manager.update_metric(metric_name, value, timestamp)


def get_gradient(metric_name: str) -> Optional[float]:
    """Convenience function to get gradient"""
    manager = get_global_game_manager()
    return manager.get_metric_gradient(metric_name)


def test_game_system() -> Dict[str, Any]:
    """Test GAME system functionality"""
    manager = get_global_game_manager()
    
    # Test with synthetic data
    test_values = [0.1, 0.15, 0.2, 0.18, 0.25, 0.3, 0.28, 0.35, 0.4, 0.38]
    
    # Update metrics
    for i, value in enumerate(test_values):
        manager.update_metric("test_metric", value, time.time() + i)
    
    # Get results
    gradient = manager.get_metric_gradient("test_metric")
    trend = manager.get_metric_trend("test_metric")
    all_gradients = manager.get_all_gradients()
    all_trends = manager.get_all_trends()
    stats = manager.get_manager_stats()
    
    return {
        "final_gradient": gradient,
        "trend_analysis": trend,
        "all_gradients": all_gradients,
        "all_trends": all_trends,
        "manager_stats": stats
    }