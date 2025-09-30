from __future__ import annotations

from typing import Dict


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

