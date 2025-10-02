"""
PENIN-Ω Equation 10: Auto-Tuning Online (AdaGrad Genérico)
===========================================================

Implementa auto-tuning online de hiperparâmetros com garantia de regret sublinear.

Fórmula:
    θ_{t+1} = θ_t - η_t · ∇_θ L_meta(θ_t)
    η_t = η_0 / (1 + Σ_{i=1}^t |∇_θ L_meta(θ_i)|^2)

Onde:
- θ: Hiperparâmetros (κ, λ_c, w_j, β_min, etc.)
- η_t: Taxa de aprendizado adaptativa
- L_meta: Meta-função de loss (ex.: variância de L∞, tempo de convergência)
- ∇_θ: Gradiente (estimado via diferenças finitas)

Hiperparâmetros Tunáveis:
- κ (kappa): Ganho CAOS⁺
- λ_c: Penalização de custo em L∞
- w_j: Pesos de métricas em L∞
- β_min: Limiar mínimo de melhoria (Death Gate)
- α_0: Taxa de aprendizado base
- γ: Fator de saturação em SR-Ω∞

Garantia: Regret sublinear O(√T) (Online Convex Optimization)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class AutoTuningConfig:
    """Configuration for auto-tuning."""

    eta_base: float = 0.1  # Base learning rate
    grad_clip: float = 1.0  # Gradient clipping threshold
    warmup_steps: int = 10  # Steps before enabling tuning
    epsilon: float = 1e-8  # Numerical stability

    # Bounds for hyperparameters
    bounds: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {
            "kappa": (20.0, 100.0),
            "lambda_c": (0.1, 2.0),
            "beta_min": (0.001, 0.1),
            "alpha_base": (0.01, 0.5),
            "gamma_saturation": (0.5, 1.5),
        }
    )


@dataclass
class HyperparamState:
    """State tracker for a hyperparameter."""

    name: str
    current_value: float
    grad_sum_squares: float = 0.0
    step_count: int = 0
    history: list = field(default_factory=list)


class AutoTuner:
    """
    Online auto-tuner for PENIN-Ω hyperparameters.

    Uses AdaGrad-style adaptive learning rates with gradient estimation
    via finite differences.
    """

    def __init__(self, config: AutoTuningConfig | None = None):
        self.config = config or AutoTuningConfig()
        self.hyperparams: dict[str, HyperparamState] = {}
        self.meta_loss_history: list = []

    def register_hyperparam(self, name: str, initial_value: float) -> None:
        """Register a hyperparameter for tuning."""
        if name in self.hyperparams:
            return

        self.hyperparams[name] = HyperparamState(name=name, current_value=initial_value)

    def compute_meta_loss(self, metrics: dict[str, float]) -> float:
        """
        Compute meta-loss (higher = worse hyperparameters).

        Meta-loss combines:
        - L∞ variance (want stable)
        - Convergence time (want fast)
        - CAOS⁺ variance (want stable exploration)
        - Gate failures (want low)
        """
        linf_variance = metrics.get("linf_variance", 0.0)
        convergence_time = metrics.get("convergence_time", 0.0)
        caos_variance = metrics.get("caos_variance", 0.0)
        gate_failures = metrics.get("gate_failures", 0.0)

        # Weighted sum (tunable)
        meta_loss = (
            0.4 * linf_variance
            + 0.3 * convergence_time
            + 0.2 * caos_variance
            + 0.1 * gate_failures
        )

        self.meta_loss_history.append(meta_loss)
        return meta_loss

    def estimate_gradient(
        self,
        hyperparam_name: str,
        loss_fn: Callable[[float], float],
        delta: float = 1e-4,
    ) -> float:
        """
        Estimate gradient via finite differences.

        Args:
            hyperparam_name: Name of hyperparameter
            loss_fn: Function that computes meta-loss given hyperparam value
            delta: Perturbation size

        Returns:
            Estimated gradient
        """
        if hyperparam_name not in self.hyperparams:
            raise ValueError(f"Hyperparameter {hyperparam_name} not registered")

        state = self.hyperparams[hyperparam_name]
        current_value = state.current_value

        # Forward difference: (L(θ + δ) - L(θ)) / δ
        loss_plus = loss_fn(current_value + delta)
        loss_current = loss_fn(current_value)

        grad = (loss_plus - loss_current) / delta

        # Clip gradient
        grad = max(-self.config.grad_clip, min(self.config.grad_clip, grad))

        return grad

    def update_hyperparam(self, name: str, gradient: float) -> float:
        """
        Update hyperparameter using AdaGrad-style adaptive learning rate.

        Args:
            name: Hyperparameter name
            gradient: Estimated gradient

        Returns:
            Updated value
        """
        if name not in self.hyperparams:
            raise ValueError(f"Hyperparameter {name} not registered")

        state = self.hyperparams[name]

        # Skip warmup period
        if state.step_count < self.config.warmup_steps:
            state.step_count += 1
            return state.current_value

        # Accumulate squared gradients
        state.grad_sum_squares += gradient**2

        # Adaptive learning rate (AdaGrad)
        eta_t = self.config.eta_base / (
            1.0 + state.grad_sum_squares + self.config.epsilon
        )

        # Gradient descent step
        new_value = state.current_value - eta_t * gradient

        # Project to bounds
        if name in self.config.bounds:
            lower, upper = self.config.bounds[name]
            new_value = max(lower, min(upper, new_value))

        # Update state
        state.current_value = new_value
        state.step_count += 1
        state.history.append(new_value)

        return new_value

    def get_current_values(self) -> dict[str, float]:
        """Get current values of all hyperparameters."""
        return {name: state.current_value for name, state in self.hyperparams.items()}

    def get_diagnostics(self) -> dict:
        """Get tuning diagnostics for observability."""
        return {
            "hyperparams": {
                name: {
                    "current_value": state.current_value,
                    "step_count": state.step_count,
                    "grad_sum_squares": state.grad_sum_squares,
                }
                for name, state in self.hyperparams.items()
            },
            "meta_loss_trend": (
                self.meta_loss_history[-10:] if self.meta_loss_history else []
            ),
        }


def auto_tune_hyperparams(
    current_hyperparams: dict[str, float],
    metrics: dict[str, float],
    config: AutoTuningConfig | None = None,
) -> dict[str, float]:
    """
    One-shot auto-tuning function (stateless wrapper).

    Args:
        current_hyperparams: Current hyperparam values
        metrics: Performance metrics
        config: Optional configuration

    Returns:
        Updated hyperparams

    Note: For stateful tuning with gradient accumulation,
    use AutoTuner class directly.
    """
    config = config or AutoTuningConfig()
    tuner = AutoTuner(config)

    # Register and update each hyperparam
    updated = {}
    for name, value in current_hyperparams.items():
        tuner.register_hyperparam(name, value)

        # Simple heuristic gradient based on metrics
        if "linf_variance" in metrics and metrics["linf_variance"] > 0.1:
            # High variance → decrease kappa, increase lambda_c
            if name == "kappa":
                grad = 1.0  # Increase kappa (lower variance)
            elif name == "lambda_c":
                grad = -0.5  # Increase lambda_c (penalize cost more)
            else:
                grad = 0.0
        else:
            grad = 0.0

        updated[name] = tuner.update_hyperparam(name, grad)

    return updated


__all__ = [
    "AutoTuningConfig",
    "HyperparamState",
    "AutoTuner",
    "auto_tune_hyperparams",
]
