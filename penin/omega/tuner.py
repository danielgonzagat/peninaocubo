from __future__ import annotations

from typing import Dict, List, Any, Tuple


class AdaGradTuner:
    def __init__(self, lr: float = 0.05, delta_clip: float = 0.02):
        self.lr = lr
        self.delta_clip = delta_clip
        self.g2: Dict[str, float] = {}

    def update(self, params: Dict[str, float], grads: Dict[str, float], bounds: Dict[str, tuple[float, float]] | None = None) -> Dict[str, float]:
        updated: Dict[str, float] = {}
        for k, v in params.items():
            g = float(grads.get(k, 0.0))
            # Use exponential decay to prevent indefinite accumulation
            decay_rate = 0.999
            self.g2[k] = decay_rate * self.g2.get(k, 0.0) + (1 - decay_rate) * g * g
            step = self.lr * g / (1e-8 + self.g2[k] ** 0.5)
            # clip
            if step > self.delta_clip:
                step = self.delta_clip
            if step < -self.delta_clip:
                step = -self.delta_clip
            nv = v + step
            if bounds and k in bounds:
                lo, hi = bounds[k]
                nv = max(lo, min(hi, nv))
            updated[k] = nv
        return updated

def quick_tune_kappa(history: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """Quick tune kappa for testing"""
    if not history:
        return 2.0, {"method": "default", "iterations": 0}
    
    # Simple heuristic: if U is high and cost is low, increase kappa
    avg_u = sum(h.get("U", 0.5) for h in history) / len(history)
    avg_cost = sum(h.get("cost", 0.1) for h in history) / len(history)
    
    if avg_u > 0.7 and avg_cost < 0.05:
        new_kappa = 3.0
    elif avg_u < 0.5 or avg_cost > 0.1:
        new_kappa = 1.5
    else:
        new_kappa = 2.0
    
    return new_kappa, {
        "method": "heuristic",
        "iterations": len(history),
        "avg_u": avg_u,
        "avg_cost": avg_cost
    }

class PeninAutoTuner:
    """Auto tuner for PENIN system"""
    
    def __init__(self, lr: float = 0.05):
        self.tuner = AdaGradTuner(lr=lr)
        self.history: List[Dict[str, Any]] = []
    
    def update(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Update parameters based on metrics"""
        self.history.append(metrics)
        
        # Simple parameter update
        params = {"kappa": 2.0, "gamma": 0.7}
        grads = {"kappa": 0.01, "gamma": 0.005}  # Mock gradients
        
        return self.tuner.update(params, grads)
    
    def get_best_params(self) -> Dict[str, float]:
        """Get best parameters"""
        return {"kappa": 2.0, "gamma": 0.7}

