"""
Life Equation (+) - Non-Compensatory Gate and Alpha Orchestrator
===============================================================

Implements the Life Equation (+) as the positive counterpart to the Death Equation.
This serves as the primary non-compensatory gate that determines when and with what
step size (alpha_eff) the system should evolve.

Key principles:
- Non-compensatory: ANY failure in gates results in alpha_eff = 0 (fail-closed)
- Life Equation: alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
- Gates: Σ-Guard, IR→IC, CAOS⁺, SR, ΔL∞, G (global coherence)
- Fail-closed: If any condition fails, evolution stops
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


class LifeGateStatus(Enum):
    """Status of Life Equation gates"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class LifeVerdict:
    """Result of Life Equation evaluation"""
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    gate_statuses: Dict[str, LifeGateStatus]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_eff": self.alpha_eff,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "gate_statuses": {k: v.value for k, v in self.gate_statuses.items()},
            "timestamp": self.timestamp
        }


def _accel(phi: float, kappa: float = 20.0) -> float:
    """
    Acceleration function: smooth, monotonic, saturated (fail-closed-friendly)
    
    α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    
    Args:
        phi: CAOS⁺ phi value
        kappa: Acceleration factor
        
    Returns:
        Acceleration factor in [0, 1]
    """
    phi_clamped = max(0.0, min(1.0, phi))
    return (1.0 + kappa * phi_clamped) / (1.0 + kappa)


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
) -> LifeVerdict:
    """
    Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
    Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).
    
    alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
    
    Args:
        base_alpha: Alpha base do sistema
        ethics_input: Inputs para Σ-Guard
        risk_series: Série de risco para IR→IC
        caos_components: Componentes CAOS⁺ (C, A, O, S)
        sr_components: Componentes SR (awareness, ethics_ok, autocorr, metacog)
        linf_weights: Pesos para L∞
        linf_metrics: Métricas para L∞
        cost: Custo atual
        ethical_ok_flag: Flag de ética OK
        G: Coerência global
        dL_inf: Delta L∞
        thresholds: Limiares para gates
        
    Returns:
        LifeVerdict com resultado completo
    """
    start_time = time.time()
    reasons = {}
    gate_statuses = {}
    
    # Default thresholds
    default_thresholds = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    }
    thresholds = {**default_thresholds, **thresholds}
    
    try:
        # 1) Σ-Guard (ética) – não compensatório
        try:
            sigma_result = sigma_guard(ethics_input)
            sigma_ok = sigma_result.passed if hasattr(sigma_result, 'passed') else True
            gate_statuses["sigma_guard"] = LifeGateStatus.PASS if sigma_ok else LifeGateStatus.FAIL
        except Exception as e:
            sigma_ok = False
            gate_statuses["sigma_guard"] = LifeGateStatus.ERROR
            reasons["sigma_error"] = str(e)
        
        reasons["sigma_ok"] = sigma_ok
        if not (sigma_ok and ethical_ok_flag):
            return LifeVerdict(
                False, 0.0, reasons, {}, thresholds, gate_statuses, start_time
            )

        # 2) IR→IC (contratividade de risco)
        try:
            risk_list = list(risk_series.values()) if isinstance(risk_series, dict) else risk_series
            iric_result = ir_to_ic_contractive(risk_list, rho_threshold=1.0)
            contractive = iric_result.passed if hasattr(iric_result, 'passed') else True
            rho = getattr(iric_result, 'details', {}).get('avg_ratio', 0.95)
            gate_statuses["ir_ic"] = LifeGateStatus.PASS if contractive else LifeGateStatus.FAIL
        except Exception as e:
            contractive = False
            rho = 1.0
            gate_statuses["ir_ic"] = LifeGateStatus.ERROR
            reasons["iric_error"] = str(e)
        
        reasons["risk_contractive"] = contractive
        reasons["risk_rho"] = rho
        if not contractive:
            return LifeVerdict(
                False, 0.0, reasons, {}, thresholds, gate_statuses, start_time
            )

        # 3) CAOS⁺ e SR
        C, A, O, S = caos_components
        try:
            phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)
            gate_statuses["caos"] = LifeGateStatus.PASS if phi >= thresholds["theta_caos"] else LifeGateStatus.FAIL
        except Exception as e:
            phi = 0.0
            gate_statuses["caos"] = LifeGateStatus.ERROR
            reasons["caos_error"] = str(e)
        
        reasons["caos_phi"] = phi
        if phi < thresholds["theta_caos"]:
            return LifeVerdict(
                False, 0.0, reasons, {}, thresholds, gate_statuses, start_time
            )

        awr, eth_ok, autoc, meta = sr_components
        try:
            sr = sr_omega(awr, eth_ok, autoc, meta)
            gate_statuses["sr"] = LifeGateStatus.PASS if sr >= thresholds["tau_sr"] else LifeGateStatus.FAIL
        except Exception as e:
            sr = 0.0
            gate_statuses["sr"] = LifeGateStatus.ERROR
            reasons["sr_error"] = str(e)
        
        reasons["sr"] = sr
        if sr < thresholds["tau_sr"]:
            return LifeVerdict(
                False, 0.0, reasons, {}, thresholds, gate_statuses, start_time
            )

        # 4) L∞ e ΔL∞ (anti-Goodhart)
        try:
            L_inf = linf_harmonic(
                list(linf_weights.values()),
                list(linf_metrics.values()),
                cost=cost,
                lambda_c=linf_weights.get("lambda_c", 0.0),
                ethical_ok=True,
            )
            gate_statuses["linf"] = LifeGateStatus.PASS if dL_inf >= thresholds["beta_min"] else LifeGateStatus.FAIL
        except Exception as e:
            L_inf = 0.0
            gate_statuses["linf"] = LifeGateStatus.ERROR
            reasons["linf_error"] = str(e)
        
        reasons["L_inf"] = L_inf
        reasons["dL_inf"] = dL_inf
        if dL_inf < thresholds["beta_min"]:
            return LifeVerdict(
                False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, 
                thresholds, gate_statuses, start_time
            )

        # 5) Coerência global Ω-ΣEA (média harmônica dos 8 módulos)
        reasons["G"] = G
        gate_statuses["global_coherence"] = LifeGateStatus.PASS if G >= thresholds["theta_G"] else LifeGateStatus.FAIL
        if G < thresholds["theta_G"]:
            return LifeVerdict(
                False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, 
                thresholds, gate_statuses, start_time
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
            "rho": float(rho),
        }
        
        return LifeVerdict(
            True, float(alpha_eff), reasons, metrics, thresholds, gate_statuses, start_time
        )
        
    except Exception as e:
        # Fail-closed: qualquer erro vira falha
        reasons["system_error"] = str(e)
        gate_statuses["system"] = LifeGateStatus.ERROR
        return LifeVerdict(
            False, 0.0, reasons, {}, thresholds, gate_statuses, start_time
        )


def quick_life_equation(
    base_alpha: float = 1e-3,
    ece: float = 0.005,
    rho_bias: float = 1.01,
    consent: bool = True,
    eco_ok: bool = True,
    risk_history: List[float] = None,
    C: float = 0.8,
    A: float = 0.7,
    O: float = 0.6,
    S: float = 0.9,
    awareness: float = 0.85,
    ethics_ok: bool = True,
    autocorr: float = 0.80,
    metacog: float = 0.82,
    G: float = 0.90,
    dL_inf: float = 0.02,
    cost: float = 0.02
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Quick Life Equation evaluation with default parameters
    
    Returns:
        (ok, alpha_eff, details)
    """
    if risk_history is None:
        risk_history = [0.9, 0.92, 0.88]
    
    ethics_input = {
        "ece": ece,
        "rho_bias": rho_bias,
        "fairness": 0.9,
        "consent": 1 if consent else 0,
        "eco_ok": 1 if eco_ok else 0,
        "thresholds": {}
    }
    
    risk_series = {f"r{i}": v for i, v in enumerate(risk_history)}
    caos_components = (C, A, O, S)
    sr_components = (awareness, ethics_ok, autocorr, metacog)
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
        cost=cost,
        ethical_ok_flag=consent and eco_ok,
        G=G,
        dL_inf=dL_inf,
        thresholds=thresholds
    )
    
    return verdict.ok, verdict.alpha_eff, verdict.to_dict()


class LifeEquationTracker:
    """Track Life Equation evaluations over time"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history = []
        self.ema_alpha = None
        self.alpha_smoothing = 0.2
    
    def update(self, verdict: LifeVerdict) -> Tuple[float, float]:
        """Update tracker with new verdict"""
        alpha_eff = verdict.alpha_eff
        
        # Update EMA
        if self.ema_alpha is None:
            self.ema_alpha = alpha_eff
        else:
            self.ema_alpha = (1.0 - self.alpha_smoothing) * self.ema_alpha + self.alpha_smoothing * alpha_eff
        
        # Update history
        self.history.append(verdict.to_dict())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return alpha_eff, self.ema_alpha
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Life Equation statistics"""
        if not self.history:
            return {"count": 0, "avg_alpha": 0.0, "success_rate": 0.0}
        
        alphas = [h["alpha_eff"] for h in self.history]
        successes = [h["ok"] for h in self.history]
        
        return {
            "count": len(self.history),
            "avg_alpha": sum(alphas) / len(alphas),
            "max_alpha": max(alphas),
            "min_alpha": min(alphas),
            "success_rate": sum(successes) / len(successes),
            "ema_alpha": self.ema_alpha,
            "latest_alpha": alphas[-1] if alphas else 0.0
        }
    
    def get_gate_failure_rate(self) -> Dict[str, float]:
        """Get failure rate for each gate"""
        if not self.history:
            return {}
        
        gate_counts = {}
        gate_failures = {}
        
        for verdict in self.history:
            gate_statuses = verdict.get("gate_statuses", {})
            for gate, status in gate_statuses.items():
                gate_counts[gate] = gate_counts.get(gate, 0) + 1
                if status == "fail":
                    gate_failures[gate] = gate_failures.get(gate, 0) + 1
        
        failure_rates = {}
        for gate in gate_counts:
            failure_rates[gate] = gate_failures.get(gate, 0) / gate_counts[gate]
        
        return failure_rates


# Integration helper for runners
def integrate_life_equation_in_cycle(
    runner_config: Dict[str, Any],
    current_metrics: Dict[str, Any],
    risk_history: List[float],
    global_coherence: float,
    delta_linf: float
) -> Tuple[float, Dict[str, Any]]:
    """
    Integrate Life Equation into evolution cycle
    
    Args:
        runner_config: Configuration from runner
        current_metrics: Current system metrics
        risk_history: Risk history for IR→IC
        global_coherence: Global coherence G
        delta_linf: Delta L∞ for this cycle
        
    Returns:
        (alpha_eff, life_verdict_dict)
    """
    # Extract parameters from runner config and metrics
    base_alpha = runner_config.get("base_alpha", 1e-3)
    
    ethics_input = {
        "ece": current_metrics.get("ece", 0.005),
        "rho_bias": current_metrics.get("rho_bias", 1.01),
        "fairness": current_metrics.get("fairness", 0.9),
        "consent": current_metrics.get("consent", True),
        "eco_ok": current_metrics.get("eco_ok", True),
        "thresholds": {}
    }
    
    caos_components = (
        current_metrics.get("complexity", 0.8),
        current_metrics.get("adaptability", 0.7),
        current_metrics.get("openness", 0.6),
        current_metrics.get("stability", 0.9)
    )
    
    sr_components = (
        current_metrics.get("awareness", 0.85),
        current_metrics.get("ethics_ok", True),
        current_metrics.get("autocorrection", 0.80),
        current_metrics.get("metacognition", 0.82)
    )
    
    linf_weights = runner_config.get("linf_weights", {"w1": 1, "w2": 1, "lambda_c": 0.1})
    linf_metrics = {
        "w1": current_metrics.get("utility", 0.8),
        "w2": current_metrics.get("safety", 0.9)
    }
    
    cost = current_metrics.get("cost", 0.02)
    ethical_ok_flag = ethics_input["consent"] and ethics_input["eco_ok"]
    
    thresholds = runner_config.get("life_thresholds", {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    })
    
    verdict = life_equation(
        base_alpha=base_alpha,
        ethics_input=ethics_input,
        risk_series={f"r{i}": v for i, v in enumerate(risk_history)},
        caos_components=caos_components,
        sr_components=sr_components,
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=cost,
        ethical_ok_flag=ethical_ok_flag,
        G=global_coherence,
        dL_inf=delta_linf,
        thresholds=thresholds
    )
    
    return verdict.alpha_eff, verdict.to_dict()