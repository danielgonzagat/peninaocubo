from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence, Any

def ema_grad(values: Iterable[float], beta: float = 0.9, init: float = 0.0) -> float:
    m = float(init)
    for v in values:
        m = beta*m + (1.0 - beta)*float(v)
    return m

@dataclass
class GradientTracker:
    beta: float = 0.9
    value: float = 0.0
    def update(self, grad: float) -> float:
        self.value = self.beta*self.value + (1.0 - self.beta)*float(grad)
        return self.value

@dataclass
class AdaptiveGAME:
    lr: float = 1e-2
    beta: float = 0.9
    min_lr: float = 1e-5
    max_lr: float = 1.0
    _gt: GradientTracker | None = None

    def __post_init__(self):
        if self._gt is None:
            self._gt = GradientTracker(self.beta)

    def step(self, grad: float) -> float:
        m = self._gt.update(float(grad))
        # ajuste simples de LR: mais grad => reduz LR
        self.lr = max(self.min_lr, min(self.max_lr, self.lr * (1.0/(1.0 + abs(m)))))
        return self.lr

    # alias pra testes que esperem 'update'
    def update(self, grad: float) -> float:
        return self.step(grad)

    def state_dict(self) -> dict[str, Any]:
        return {"lr": self.lr, "beta": self.beta, "min_lr": self.min_lr, "max_lr": self.max_lr, "ema": self._gt.value}

    def load_state_dict(self, d: dict[str, Any]) -> None:
        self.lr = float(d.get("lr", self.lr))
        self.beta = float(d.get("beta", self.beta))
        self.min_lr = float(d.get("min_lr", self.min_lr))
        self.max_lr = float(d.get("max_lr", self.max_lr))
        if self._gt is None: self._gt = GradientTracker(self.beta)
        self._gt.value = float(d.get("ema", self._gt.value))

__all__ = ["ema_grad", "GradientTracker", "AdaptiveGAME"]
