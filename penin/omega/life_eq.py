"""
Life Equation (+) - Non-Compensatory Gate and Alpha_eff Orchestrator
====================================================================

Implements the Life Equation (+) as the counterpart to the Death Equation.
Non-compensatory gate: if ANY condition fails, alpha_eff = 0 (fail-closed).

alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)

Where:
- base_alpha: Base learning rate
- φ(CAOS⁺): CAOS+ phi value (complexity, adaptability, openness, stability)
- SR: Self-Reflection score (awareness, ethics, autocorrection, metacognition)
- G: Global coherence (Ω-ΣEA harmonic mean of 8 modules)
- accel(φ): Acceleration function based on CAOS+ phi
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List
from enum import Enum

# Import existing modules
from .guards import sigma_guard, ir_to_ic_contractive, GuardResult
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega


class LifeVerdictType(Enum):
    """Life Equation verdict types"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class LifeVerdict:
    """Result from Life Equation evaluation"""
    ok: bool
    alpha_eff: float
    verdict_type: LifeVerdictType
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_eff": self.alpha_eff,
            "verdict_type": self.verdict_type.value,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "timestamp": self.timestamp
        }


def _accel(phi: float, kappa: float = 20.0) -> float:
    """
    Acceleration function: smooth, monotonic, saturated (fail-closed-friendly)
    
    α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    
    Args:
        phi: CAOS+ phi value
        kappa: Acceleration factor
        
    Returns:
        Acceleration factor in (0, 1]
    """
    phi_clamped = max(0.0, min(1.0, phi))
    return (1.0 + kappa * phi_clamped) / (1.0 + kappa)


def _compute_global_coherence(modules_health: Dict[str, float]) -> float:
    """
    Compute global coherence G as harmonic mean of 8 modules
    
    Args:
        modules_health: Dict with module health scores
        
    Returns:
        Global coherence G ∈ [0, 1]
    """
    if not modules_health:
        return 0.0
    
    # Ensure all values are positive
    safe_values = [max(1e-9, v) for v in modules_health.values()]
    
    # Harmonic mean
    return len(safe_values) / sum(1.0 / v for v in safe_values)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float],
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, float, float, float],    # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float],
    linf_metrics: Dict[str, float],  # {metric_name: value}
    cost: float,
    ethical_ok_flag: bool,
    G: float,    # Coerência global (Ω-ΣEA)
    dL_inf: float,  # ΔL∞ no ciclo
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
    modules_health: Optional[Dict[str, float]] = None
) -> LifeVerdict:
    """
    Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
    Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).
    
    Args:
        base_alpha: Taxa de aprendizado base
        ethics_input: Entrada para Σ-Guard (ece, rho_bias, fairness, consent, eco_ok)
        risk_series: Série temporal de risco para IR→IC
        caos_components: Componentes CAOS⁺ (C, A, O, S)
        sr_components: Componentes SR (awareness, ethics_ok, autocorr, metacog)
        linf_weights: Pesos para L∞
        linf_metrics: Métricas para L∞
        cost: Custo do ciclo
        ethical_ok_flag: Flag de ética OK
        G: Coerência global
        dL_inf: ΔL∞ no ciclo
        thresholds: Limiares (beta_min, theta_caos, tau_sr, theta_G)
        modules_health: Saúde dos módulos para calcular G
        
    Returns:
        LifeVerdict com resultado completo
    """
    start_time = time.time()
    reasons = {}
    
    try:
        # 1) Σ-Guard (ética) – não compensatório
        sigma_result = sigma_guard(ethics_input)
        reasons["sigma_ok"] = sigma_result.passed
        reasons["sigma_details"] = sigma_result.details
        
        if not (sigma_result.passed and ethical_ok_flag):
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={},
                thresholds=thresholds,
                timestamp=start_time
            )

        # 2) IR→IC (contratividade de risco)
        risk_list = list(risk_series.values()) if isinstance(risk_series, dict) else list(risk_series)
        iric_result = ir_to_ic_contractive(risk_list, rho_threshold=1.0)
        reasons["risk_contractive"] = iric_result.passed
        reasons["risk_rho"] = iric_result.details.get("avg_ratio", 1.0)
        
        if not iric_result.passed:
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={},
                thresholds=thresholds,
                timestamp=start_time
            )

        # 3) CAOS⁺ e SR
        C, A, O, S = caos_components
        phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)
        reasons["caos_phi"] = phi
        
        if phi < thresholds.get("theta_caos", 0.25):
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={"phi": phi},
                thresholds=thresholds,
                timestamp=start_time
            )

        awr, eth_ok, autoc, meta = sr_components
        sr = sr_omega(awr, eth_ok, autoc, meta)
        reasons["sr"] = sr
        
        if sr < thresholds.get("tau_sr", 0.80):
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={"phi": phi, "sr": sr},
                thresholds=thresholds,
                timestamp=start_time
            )

        # 4) L∞ e ΔL∞ (anti-Goodhart)
        L_inf = linf_harmonic(
            list(linf_weights.keys()),
            list(linf_metrics.values()),
            cost=cost,
            lambda_c=linf_weights.get("lambda_c", 0.0),
            ethical_ok=True,
        )
        reasons["L_inf"] = L_inf
        reasons["dL_inf"] = dL_inf
        
        if dL_inf < thresholds.get("beta_min", 0.01):
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={"L_inf": L_inf, "dL_inf": dL_inf},
                thresholds=thresholds,
                timestamp=start_time
            )

        # 5) Coerência global Ω-ΣEA (média harmônica dos 8 módulos)
        if modules_health:
            G = _compute_global_coherence(modules_health)
        
        reasons["G"] = G
        if G < thresholds.get("theta_G", 0.85):
            return LifeVerdict(
                ok=False,
                alpha_eff=0.0,
                verdict_type=LifeVerdictType.FAIL,
                reasons=reasons,
                metrics={"L_inf": L_inf, "dL_inf": dL_inf, "G": G},
                thresholds=thresholds,
                timestamp=start_time
            )

        # 6) α_eff – aceleração por CAOS⁺, SR e G (fail-closed)
        alpha_eff = base_alpha * phi * sr * G * _accel(phi, kappa=20.0)

        metrics = {
            "alpha_eff": float(alpha_eff),
            "phi": float(phi),
            "sr": float(sr),
            "G": float(G),
            "L_inf": float(L_inf),
            "dL_inf": float(dL_inf),
            "rho": float(reasons["risk_rho"]),
        }
        
        return LifeVerdict(
            ok=True,
            alpha_eff=float(alpha_eff),
            verdict_type=LifeVerdictType.PASS,
            reasons=reasons,
            metrics=metrics,
            thresholds=thresholds,
            timestamp=start_time
        )
        
    except Exception as e:
        # Fail-closed: erro vira falha
        reasons["error"] = str(e)
        return LifeVerdict(
            ok=False,
            alpha_eff=0.0,
            verdict_type=LifeVerdictType.ERROR,
            reasons=reasons,
            metrics={},
            thresholds=thresholds,
            timestamp=start_time
        )


def quick_life_equation_check(
    base_alpha: float = 1e-3,
    ece: float = 0.005,
    rho_bias: float = 1.01,
    caos_components: Tuple[float, float, float, float] = (0.8, 0.7, 0.6, 0.9),
    sr_components: Tuple[float, bool, float, float] = (0.85, True, 0.80, 0.82),
    G: float = 0.90,
    dL_inf: float = 0.02
) -> Tuple[bool, float]:
    """
    Quick Life Equation check for testing
    
    Returns:
        (passed, alpha_eff)
    """
    ethics_input = {
        "ece": ece,
        "rho_bias": rho_bias,
        "fairness": 0.9,
        "consent": 1,
        "eco_ok": 1,
        "thresholds": {}
    }
    
    risk_series = {"r0": 0.9, "r1": 0.92, "r2": 0.88}
    
    linf_weights = {"w1": 1, "w2": 1, "lambda_c": 0.1}
    linf_metrics = {"w1": 0.8, "w2": 0.9}
    
    thresholds = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    }
    
    verdict = life_equation(
        base_alpha=base_alpha,
        ethics_input=ethics_input,
        risk_series=risk_series,
        caos_components=caos_components,
        sr_components=sr_components,
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=0.02,
        ethical_ok_flag=True,
        G=G,
        dL_inf=dL_inf,
        thresholds=thresholds
    )
    
    return verdict.ok, verdict.alpha_eff


class LifeEquationTracker:
    """Track Life Equation results over time"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[LifeVerdict] = []
        self.alpha_eff_ema = None
        self.alpha_ema_alpha = 0.2
    
    def add_verdict(self, verdict: LifeVerdict) -> None:
        """Add a new verdict to history"""
        self.history.append(verdict)
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Update EMA
        if self.alpha_eff_ema is None:
            self.alpha_eff_ema = verdict.alpha_eff
        else:
            self.alpha_eff_ema = (
                self.alpha_ema_alpha * verdict.alpha_eff + 
                (1 - self.alpha_ema_alpha) * self.alpha_eff_ema
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from history"""
        if not self.history:
            return {"count": 0, "pass_rate": 0.0, "avg_alpha_eff": 0.0}
        
        passed_count = sum(1 for v in self.history if v.ok)
        pass_rate = passed_count / len(self.history)
        
        alpha_effs = [v.alpha_eff for v in self.history if v.ok]
        avg_alpha_eff = sum(alpha_effs) / len(alpha_effs) if alpha_effs else 0.0
        
        return {
            "count": len(self.history),
            "pass_rate": pass_rate,
            "avg_alpha_eff": avg_alpha_eff,
            "ema_alpha_eff": self.alpha_eff_ema,
            "latest_verdict": self.history[-1].to_dict() if self.history else None
        }
    
    def get_trend(self) -> str:
        """Get trend direction"""
        if len(self.history) < 2:
            return "stable"
        
        recent = self.history[-3:] if len(self.history) >= 3 else self.history[-2:]
        earlier = self.history[:len(self.history)-len(recent)]
        
        if not earlier:
            return "stable"
        
        recent_pass_rate = sum(1 for v in recent if v.ok) / len(recent)
        earlier_pass_rate = sum(1 for v in earlier if v.ok) / len(earlier)
        
        if recent_pass_rate > earlier_pass_rate + 0.1:
            return "improving"
        elif recent_pass_rate < earlier_pass_rate - 0.1:
            return "declining"
        else:
            return "stable"


# Integration helper for runners
def integrate_life_equation_in_cycle(
    base_alpha: float,
    current_state: Dict[str, Any],
    cycle_metrics: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[float, LifeVerdict]:
    """
    Integrate Life Equation into evolution cycle
    
    Args:
        base_alpha: Base learning rate
        current_state: Current system state
        cycle_metrics: Metrics from current cycle
        thresholds: Custom thresholds (optional)
        
    Returns:
        (alpha_eff, verdict)
    """
    if thresholds is None:
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    
    # Extract components from current state
    ethics_input = {
        "ece": current_state.get("ece", 0.005),
        "rho_bias": current_state.get("rho_bias", 1.01),
        "fairness": current_state.get("fairness", 0.9),
        "consent": current_state.get("consent", True),
        "eco_ok": current_state.get("eco_ok", True),
        "thresholds": {}
    }
    
    risk_series = current_state.get("risk_history", {"r0": 0.9, "r1": 0.92, "r2": 0.88})
    
    caos_components = (
        current_state.get("complexity", 0.8),
        current_state.get("adaptability", 0.7),
        current_state.get("openness", 0.6),
        current_state.get("stability", 0.9)
    )
    
    sr_components = (
        current_state.get("awareness", 0.85),
        current_state.get("ethics_ok", True),
        current_state.get("autocorrection", 0.80),
        current_state.get("metacognition", 0.82)
    )
    
    linf_weights = current_state.get("linf_weights", {"w1": 1, "w2": 1, "lambda_c": 0.1})
    linf_metrics = current_state.get("linf_metrics", {"w1": 0.8, "w2": 0.9})
    
    cost = current_state.get("cost", 0.02)
    ethical_ok_flag = current_state.get("ethical_ok_flag", True)
    G = current_state.get("global_coherence", 0.90)
    dL_inf = cycle_metrics.get("delta_linf", 0.02)
    
    modules_health = current_state.get("modules_health", None)
    
    verdict = life_equation(
        base_alpha=base_alpha,
        ethics_input=ethics_input,
        risk_series=risk_series,
        caos_components=caos_components,
        sr_components=sr_components,
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=cost,
        ethical_ok_flag=ethical_ok_flag,
        G=G,
        dL_inf=dL_inf,
        thresholds=thresholds,
        modules_health=modules_health
    )
    
    return verdict.alpha_eff, verdict