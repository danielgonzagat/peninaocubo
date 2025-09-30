"""
GAME - Gradient Accumulation with Memory Exponential
====================================================

Implements exponential moving average for gradients and
evolutionary selection mechanisms.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math
import time


def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    """
    Exponential moving average for gradients.
    
    Args:
        g_prev: Previous gradient value
        g_now: Current gradient value
        beta: EMA coefficient (0 < beta < 1)
    
    Returns:
        Updated gradient estimate
    """
    beta = max(0.0, min(1.0, beta))  # Clamp to valid range
    return beta * g_prev + (1.0 - beta) * g_now


@dataclass
class GradientHistory:
    """Tracks gradient history with EMA"""
    values: List[float]
    ema: float
    beta: float = 0.9
    max_history: int = 100
    
    def update(self, gradient: float) -> float:
        """Update with new gradient value"""
        self.ema = ema_grad(self.ema, gradient, self.beta)
        self.values.append(gradient)
        
        # Keep history bounded
        if len(self.values) > self.max_history:
            self.values = self.values[-self.max_history:]
        
        return self.ema
    
    def get_variance(self) -> float:
        """Calculate variance of recent gradients"""
        if len(self.values) < 2:
            return 0.0
        
        mean = sum(self.values) / len(self.values)
        variance = sum((x - mean) ** 2 for x in self.values) / len(self.values)
        return variance
    
    def get_trend(self) -> str:
        """Determine gradient trend"""
        if len(self.values) < 3:
            return "stable"
        
        recent = self.values[-10:]
        if len(recent) < 3:
            return "stable"
        
        # Simple trend detection
        first_half = sum(recent[:len(recent)//2]) / max(len(recent)//2, 1)
        second_half = sum(recent[len(recent)//2:]) / max(len(recent) - len(recent)//2, 1)
        
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        else:
            return "stable"


class AdaptiveOptimizer:
    """Adaptive optimizer using GAME principles"""
    
    def __init__(self, learning_rate: float = 0.01, beta: float = 0.9):
        self.learning_rate = learning_rate
        self.beta = beta
        self.param_history: Dict[str, GradientHistory] = {}
        self.step_count = 0
        
    def step(self, gradients: Dict[str, float]) -> Dict[str, float]:
        """
        Compute parameter updates using GAME.
        
        Args:
            gradients: Dict of parameter gradients
        
        Returns:
            Dict of parameter updates
        """
        updates = {}
        
        for param_name, grad in gradients.items():
            # Initialize history if needed
            if param_name not in self.param_history:
                self.param_history[param_name] = GradientHistory(
                    values=[],
                    ema=grad,
                    beta=self.beta
                )
            
            # Update EMA
            history = self.param_history[param_name]
            ema = history.update(grad)
            
            # Adaptive learning rate based on gradient variance
            variance = history.get_variance()
            adaptive_lr = self.learning_rate / (1.0 + math.sqrt(variance))
            
            # Compute update
            updates[param_name] = -adaptive_lr * ema
        
        self.step_count += 1
        return updates
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        stats = {
            "step_count": self.step_count,
            "learning_rate": self.learning_rate,
            "beta": self.beta,
            "parameters": {}
        }
        
        for param_name, history in self.param_history.items():
            stats["parameters"][param_name] = {
                "ema": history.ema,
                "variance": history.get_variance(),
                "trend": history.get_trend(),
                "history_size": len(history.values)
            }
        
        return stats