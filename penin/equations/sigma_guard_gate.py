"""
PENIN-Ω Equation 15: Σ-Guard Gate (Bloqueio Fail-Closed)
==========================================================

Fórmula:
    V_t = 1 se (ρ < 1) ∧ (ECE ≤ 0.01) ∧ (ρ_bias ≤ 1.05) ∧ (consent) ∧ (eco_ok)
        = 0 caso contrário

Gate não-compensatório: QUALQUER falha bloqueia promoção.

Ação em falha:
- Aborta promoção
- Rollback atômico
- Emite razão e sugestão (OPA/Rego)
- Registra no WORM ledger

Re-exports from penin.guard.sigma_guard_complete.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from penin.guard.sigma_guard_complete import GateMetrics, SigmaGuard
except ImportError:
    SigmaGuard = None
    GateMetrics = None


@dataclass
class SigmaGuardConfig:
    """Configuration for Σ-Guard."""

    rho_threshold: float = 1.0
    ece_threshold: float = 0.01
    bias_rho_threshold: float = 1.05
    require_consent: bool = True
    require_eco_ok: bool = True


def sigma_guard_check(
    metrics: dict[str, float], config: SigmaGuardConfig | None = None
) -> tuple[bool, str]:
    """
    Execute Σ-Guard gate (fail-closed).

    Args:
        metrics: Dict with keys: rho, ece, rho_bias, consent, eco_ok
        config: Optional configuration

    Returns:
        (gate_pass, reason_if_fail)

    Example:
        >>> metrics = {"rho": 0.95, "ece": 0.005, "rho_bias": 1.02, "consent": True, "eco_ok": True}
        >>> ok, reason = sigma_guard_check(metrics)
        >>> assert ok
    """
    config = config or SigmaGuardConfig()

    # Check each condition (non-compensatory)
    if metrics.get("rho", 1.0) >= config.rho_threshold:
        return (
            False,
            f"Contratividade falhou: ρ={metrics.get('rho')} >= {config.rho_threshold}",
        )

    if metrics.get("ece", 1.0) > config.ece_threshold:
        return (
            False,
            f"Calibração falhou: ECE={metrics.get('ece')} > {config.ece_threshold}",
        )

    if metrics.get("rho_bias", 10.0) > config.bias_rho_threshold:
        return (
            False,
            f"Bias excessivo: ρ_bias={metrics.get('rho_bias')} > {config.bias_rho_threshold}",
        )

    if config.require_consent and not metrics.get("consent", False):
        return False, "Consentimento não obtido"

    if config.require_eco_ok and not metrics.get("eco_ok", False):
        return False, "Sustentabilidade ecológica não verificada"

    return True, "Σ-Guard: PASS (todos gates verdes)"


__all__ = ["SigmaGuardConfig", "sigma_guard_check", "SigmaGuard", "GateMetrics"]
