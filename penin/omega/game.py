"""
GAME - Gradientes com Memória Exponencial
=========================================

Implements exponential moving average for gradients with fail-closed
protection and adaptive learning rates.
"""

import time
import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class GradientType(Enum):
    """Types of gradients"""
    ALPHA_EFF = "alpha_eff"
    PHI_CAOS = "phi_caos"
    SR_OMEGA = "sr_omega"
    G_COHERENCE = "g_coherence"
    L_INF = "l_inf"
    RHO_RISK = "rho_risk"


@dataclass
class GradientSnapshot:
    """Gradient snapshot"""
    timestamp: float
    gradient_type: GradientType
    value: float
    learning_rate: float
    momentum: float
    variance: float
    confidence: float


@dataclass
class GAMEConfig:
    """GAME configuration"""
    base_learning_rate: float = 0.01
    momentum_decay: float = 0.9
    variance_decay: float = 0.95
    confidence_threshold: float = 0.8
    max_learning_rate: float = 0.1
    min_learning_rate: float = 0.001
    gradient_clip_threshold: float = 1.0
    stability_window: int = 10


class GAMEEngine:
    """GAME engine for gradient management"""
    
    def __init__(self, config: GAMEConfig = None):
        self.config = config or GAMEConfig()
        
        # Gradient history for each type
        self.gradient_history: Dict[GradientType, List[GradientSnapshot]] = {}
        
        # Current state for each gradient type
        self.current_state: Dict[GradientType, Dict[str, float]] = {}
        
        # Initialize state
        for grad_type in GradientType:
            self.gradient_history[grad_type] = []
            self.current_state[grad_type] = {
                "value": 0.0,
                "learning_rate": self.config.base_learning_rate,
                "momentum": 0.0,
                "variance": 0.0,
                "confidence": 0.0
            }
    
    def _clip_gradient(self, gradient: float) -> float:
        """Clip gradient to prevent explosion"""
        return max(-self.config.gradient_clip_threshold, 
                  min(self.config.gradient_clip_threshold, gradient))
    
    def _calculate_confidence(self, variance: float, window_size: int) -> float:
        """Calculate confidence based on variance and window size"""
        if variance == 0:
            return 1.0
        
        # Confidence decreases with high variance
        confidence = 1.0 / (1.0 + variance)
        
        # Adjust for window size
        confidence *= min(1.0, window_size / 10.0)
        
        return confidence
    
    def _adaptive_learning_rate(self, gradient_type: GradientType, 
                               current_lr: float, variance: float,
                               confidence: float) -> float:
        """Calculate adaptive learning rate"""
        # Base learning rate
        new_lr = current_lr
        
        # Adjust based on variance
        if variance > 0.1:  # High variance - reduce learning rate
            new_lr *= 0.9
        elif variance < 0.01:  # Low variance - increase learning rate
            new_lr *= 1.1
        
        # Adjust based on confidence
        if confidence < self.config.confidence_threshold:
            new_lr *= 0.8  # Reduce learning rate for low confidence
        
        # Clip to bounds
        new_lr = max(self.config.min_learning_rate, 
                    min(self.config.max_learning_rate, new_lr))
        
        return new_lr
    
    def update_gradient(self, gradient_type: GradientType, 
                       new_value: float, target_value: float = None) -> Dict[str, float]:
        """
        Update gradient with exponential moving average
        
        Args:
            gradient_type: Type of gradient
            new_value: New gradient value
            target_value: Target value (for supervised learning)
            
        Returns:
            Updated gradient state
        """
        # Calculate gradient
        if target_value is not None:
            gradient = target_value - new_value
        else:
            gradient = new_value
        
        # Clip gradient
        gradient = self._clip_gradient(gradient)
        
        # Get current state
        current_state = self.current_state[gradient_type]
        
        # Update momentum (exponential moving average)
        momentum = self.config.momentum_decay * current_state["momentum"] + \
                  (1 - self.config.momentum_decay) * gradient
        
        # Update variance (exponential moving average)
        variance = self.config.variance_decay * current_state["variance"] + \
                  (1 - self.config.variance_decay) * (gradient - momentum) ** 2
        
        # Calculate confidence
        history_size = len(self.gradient_history[gradient_type])
        confidence = self._calculate_confidence(variance, history_size)
        
        # Adaptive learning rate
        learning_rate = self._adaptive_learning_rate(
            gradient_type, current_state["learning_rate"], variance, confidence
        )
        
        # Update value
        new_gradient_value = current_state["value"] + learning_rate * gradient
        
        # Update state
        self.current_state[gradient_type] = {
            "value": new_gradient_value,
            "learning_rate": learning_rate,
            "momentum": momentum,
            "variance": variance,
            "confidence": confidence
        }
        
        # Create snapshot
        snapshot = GradientSnapshot(
            timestamp=time.time(),
            gradient_type=gradient_type,
            value=new_gradient_value,
            learning_rate=learning_rate,
            momentum=momentum,
            variance=variance,
            confidence=confidence
        )
        
        # Add to history
        self.gradient_history[gradient_type].append(snapshot)
        
        # Keep only recent history
        if len(self.gradient_history[gradient_type]) > 100:
            self.gradient_history[gradient_type] = self.gradient_history[gradient_type][-100:]
        
        return self.current_state[gradient_type].copy()
    
    def get_gradient_state(self, gradient_type: GradientType) -> Dict[str, float]:
        """Get current gradient state"""
        return self.current_state[gradient_type].copy()
    
    def get_gradient_history(self, gradient_type: GradientType, 
                           window_size: int = None) -> List[GradientSnapshot]:
        """Get gradient history"""
        history = self.gradient_history[gradient_type]
        
        if window_size is None:
            return history.copy()
        
        return history[-window_size:] if window_size > 0 else []
    
    def calculate_gradient_trend(self, gradient_type: GradientType, 
                                window_size: int = 10) -> Dict[str, float]:
        """Calculate gradient trend"""
        history = self.get_gradient_history(gradient_type, window_size)
        
        if len(history) < 2:
            return {
                "trend": 0.0,
                "stability": 0.0,
                "acceleration": 0.0
            }
        
        # Calculate trend (slope)
        values = [snapshot.value for snapshot in history]
        timestamps = [snapshot.timestamp for snapshot in history]
        
        # Linear regression for trend
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(timestamps, values))
        sum_x2 = sum(x * x for x in timestamps)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            trend = 0.0
        else:
            trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Calculate stability (inverse of variance)
        variance = statistics.variance(values) if len(values) > 1 else 0.0
        stability = 1.0 / (1.0 + variance)
        
        # Calculate acceleration (second derivative)
        if len(values) >= 3:
            # Simple finite difference approximation
            acceleration = values[-1] - 2 * values[-2] + values[-3]
        else:
            acceleration = 0.0
        
        return {
            "trend": trend,
            "stability": stability,
            "acceleration": acceleration
        }
    
    def detect_gradient_anomalies(self, gradient_type: GradientType) -> List[Dict[str, Any]]:
        """Detect gradient anomalies"""
        history = self.get_gradient_history(gradient_type, 20)
        
        if len(history) < 5:
            return []
        
        anomalies = []
        values = [snapshot.value for snapshot in history]
        
        # Calculate statistics
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.0
        
        if std_val == 0:
            return []
        
        # Check for outliers
        for i, snapshot in enumerate(history):
            z_score = abs(snapshot.value - mean_val) / std_val
            
            if z_score > 3.0:  # 3-sigma rule
                anomalies.append({
                    "timestamp": snapshot.timestamp,
                    "value": snapshot.value,
                    "z_score": z_score,
                    "type": "outlier",
                    "severity": min(1.0, z_score / 5.0)
                })
        
        # Check for sudden changes
        for i in range(1, len(history)):
            prev_value = history[i-1].value
            curr_value = history[i].value
            
            change = abs(curr_value - prev_value)
            if change > 2 * std_val:
                anomalies.append({
                    "timestamp": history[i].timestamp,
                    "value": curr_value,
                    "change": change,
                    "type": "sudden_change",
                    "severity": min(1.0, change / (5 * std_val))
                })
        
        return anomalies
    
    def get_global_gradient_health(self) -> Dict[str, Any]:
        """Get global gradient health"""
        health_scores = {}
        total_confidence = 0.0
        total_stability = 0.0
        
        for grad_type in GradientType:
            state = self.current_state[grad_type]
            trend_info = self.calculate_gradient_trend(grad_type)
            anomalies = self.detect_gradient_anomalies(grad_type)
            
            # Calculate health score
            confidence = state["confidence"]
            stability = trend_info["stability"]
            anomaly_penalty = len(anomalies) * 0.1
            
            health_score = max(0.0, confidence * stability - anomaly_penalty)
            health_scores[grad_type.value] = health_score
            
            total_confidence += confidence
            total_stability += stability
        
        # Global health
        avg_confidence = total_confidence / len(GradientType)
        avg_stability = total_stability / len(GradientType)
        global_health = avg_confidence * avg_stability
        
        return {
            "global_health": global_health,
            "average_confidence": avg_confidence,
            "average_stability": avg_stability,
            "gradient_health": health_scores,
            "total_gradients": len(GradientType)
        }
    
    def reset_gradient(self, gradient_type: GradientType):
        """Reset gradient state"""
        self.gradient_history[gradient_type] = []
        self.current_state[gradient_type] = {
            "value": 0.0,
            "learning_rate": self.config.base_learning_rate,
            "momentum": 0.0,
            "variance": 0.0,
            "confidence": 0.0
        }
    
    def reset_all_gradients(self):
        """Reset all gradients"""
        for grad_type in GradientType:
            self.reset_gradient(grad_type)


# Integration with Life Equation
def integrate_game_in_life_equation(
    life_verdict: Dict[str, Any],
    game_engine: GAMEEngine = None
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Integrate GAME engine with Life Equation
    
    Args:
        life_verdict: Result from life_equation()
        game_engine: GAME engine instance
        
    Returns:
        (updated_gradients, game_metrics)
    """
    if game_engine is None:
        game_engine = GAMEEngine()
    
    metrics = life_verdict.get("metrics", {})
    updated_gradients = {}
    
    # Update gradients based on Life Equation metrics
    if "alpha_eff" in metrics:
        updated_gradients["alpha_eff"] = game_engine.update_gradient(
            GradientType.ALPHA_EFF, metrics["alpha_eff"]
        )
    
    if "phi" in metrics:
        updated_gradients["phi"] = game_engine.update_gradient(
            GradientType.PHI_CAOS, metrics["phi"]
        )
    
    if "sr" in metrics:
        updated_gradients["sr"] = game_engine.update_gradient(
            GradientType.SR_OMEGA, metrics["sr"]
        )
    
    if "G" in metrics:
        updated_gradients["G"] = game_engine.update_gradient(
            GradientType.G_COHERENCE, metrics["G"]
        )
    
    if "L_inf" in metrics:
        updated_gradients["L_inf"] = game_engine.update_gradient(
            GradientType.L_INF, metrics["L_inf"]
        )
    
    if "rho" in metrics:
        updated_gradients["rho"] = game_engine.update_gradient(
            GradientType.RHO_RISK, metrics["rho"]
        )
    
    # Get game metrics
    game_metrics = game_engine.get_global_gradient_health()
    
    return updated_gradients, game_metrics


# Example usage
if __name__ == "__main__":
    # Create GAME engine
    game = GAMEEngine()
    
    # Simulate gradient updates
    for i in range(20):
        # Simulate alpha_eff gradient
        alpha_eff = 0.5 + 0.1 * math.sin(i * 0.5) + 0.05 * (i % 3 - 1)
        game.update_gradient(GradientType.ALPHA_EFF, alpha_eff)
        
        # Simulate phi gradient
        phi = 0.7 + 0.05 * math.cos(i * 0.3)
        game.update_gradient(GradientType.PHI_CAOS, phi)
        
        time.sleep(0.1)  # Simulate time passing
    
    # Get gradient states
    alpha_state = game.get_gradient_state(GradientType.ALPHA_EFF)
    print(f"Alpha gradient state: {alpha_state}")
    
    # Calculate trends
    alpha_trend = game.calculate_gradient_trend(GradientType.ALPHA_EFF)
    print(f"Alpha gradient trend: {alpha_trend}")
    
    # Detect anomalies
    anomalies = game.detect_gradient_anomalies(GradientType.ALPHA_EFF)
    print(f"Alpha gradient anomalies: {len(anomalies)}")
    
    # Get global health
    health = game.get_global_gradient_health()
    print(f"Global gradient health: {health}")