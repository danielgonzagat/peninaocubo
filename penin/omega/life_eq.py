# penin/omega/life_eq.py
"""
Equação de Vida (+) - Gate Não-Compensatório e Orquestrador Positivo
===================================================================

Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).

Fórmula: alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)

Onde:
- φ(CAOS⁺): Função CAOS⁺ (Complexity, Adaptability, Openness, Stability)
- SR: Self-Reflection Ω∞ (não-compensatório)
- G: Coerência global (Ω-ΣEA)
- accel(φ): Função de aceleração suave baseada em φ

Gates verificados:
1. Σ-Guard (ética): ECE ≤ 0.01, ρ_bias ≤ 1.05, consent, eco_ok
2. IR→IC (contratividade): ρ < 1.0
3. CAOS⁺: φ ≥ theta_caos
4. SR: SR ≥ tau_sr
5. ΔL∞: ΔL∞ ≥ beta_min
6. G (coerência global): G ≥ theta_G
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional
import time

# Motores existentes no repo
from .guards import sigma_guard, ir_to_ic_contractive, GuardResult
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega, SRComponents, SROmegaEngine, SRAggregationMethod


@dataclass
class LifeVerdict:
    """Resultado da Equação de Vida (+)"""
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_eff": self.alpha_eff,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "timestamp": self.timestamp
        }


def _accel(phi: float, kappa: float = 20.0) -> float:
    """
    Aceleração suave, monotônica e saturada (fail-closed-friendly)
    α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    """
    return (1.0 + kappa * max(0.0, phi)) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, Any],
    risk_series: List[float],
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
    """
    reasons = {}
    timestamp = time.time()

    # 1) Σ-Guard (ética) – não compensatório
    try:
        # Usar função sigma_guard existente
        sigma_result = sigma_guard(ethics_input)
        ok_sigma = sigma_result.passed if hasattr(sigma_result, 'passed') else bool(sigma_result)
        
        reasons["sigma_ok"] = ok_sigma
        reasons["sigma_details"] = sigma_result.to_dict() if hasattr(sigma_result, 'to_dict') else {"result": str(sigma_result)}
        
        if not (ok_sigma and ethical_ok_flag):
            return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)
    except Exception as e:
        reasons["sigma_ok"] = False
        reasons["sigma_error"] = str(e)
        return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)

    # 2) IR→IC (contratividade de risco)
    try:
        iric_result = ir_to_ic_contractive(risk_series, rho_threshold=1.0)
        contractive = iric_result.passed if hasattr(iric_result, 'passed') else bool(iric_result)
        
        # Calcular rho médio para métricas
        if len(risk_series) >= 2:
            ratios = []
            for i in range(1, len(risk_series)):
                if risk_series[i-1] > 1e-9:
                    ratio = risk_series[i] / risk_series[i-1]
                    ratios.append(ratio)
            rho = sum(ratios) / len(ratios) if ratios else 1.0
        else:
            rho = 1.0
            
        reasons["risk_contractive"] = contractive
        reasons["risk_rho"] = rho
        
        if not contractive:
            return LifeVerdict(False, 0.0, reasons, {"rho": rho}, thresholds, timestamp)
    except Exception as e:
        reasons["risk_contractive"] = False
        reasons["risk_error"] = str(e)
        return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)

    # 3) CAOS⁺ e SR
    try:
        C, A, O, S = caos_components
        phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)  # estável (log+tanh)
        reasons["caos_phi"] = phi
        
        if phi < thresholds.get("theta_caos", 0.25):
            return LifeVerdict(False, 0.0, reasons, {"phi": phi}, thresholds, timestamp)

        # SR usando engine existente
        awr, eth_ok, autoc, meta = sr_components
        sr_engine = SROmegaEngine(method=SRAggregationMethod.HARMONIC)
        sr_comps = SRComponents(awr, 1.0 if eth_ok else 0.001, autoc, meta)
        sr, sr_details = sr_engine.compute_sr(sr_comps)
        
        reasons["sr"] = sr
        reasons["sr_details"] = sr_details
        
        if sr < thresholds.get("tau_sr", 0.80):
            return LifeVerdict(False, 0.0, reasons, {"phi": phi, "sr": sr}, thresholds, timestamp)
    except Exception as e:
        reasons["caos_sr_error"] = str(e)
        return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)

    # 4) L∞ e ΔL∞ (anti-Goodhart)
    try:
        # Separar lambda_c dos pesos das métricas
        metric_weights = {k: v for k, v in linf_weights.items() if k != "lambda_c"}
        lambda_c = linf_weights.get("lambda_c", 0.0)
        
        L_inf = linf_harmonic(
            list(linf_metrics.values()),
            list(metric_weights.values()),
            cost_norm=cost,
            lambda_c=lambda_c,
            ethical_ok=True,
        )
        reasons["L_inf"] = L_inf
        reasons["dL_inf"] = dL_inf
        
        if dL_inf < thresholds.get("beta_min", 0.01):
            return LifeVerdict(False, 0.0, reasons, 
                             {"L_inf": float(L_inf), "dL_inf": float(dL_inf), "phi": phi, "sr": sr}, 
                             thresholds, timestamp)
    except Exception as e:
        reasons["linf_error"] = str(e)
        return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)

    # 5) Coerência global Ω-ΣEA (média harmônica dos 8 módulos)
    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(False, 0.0, reasons, 
                         {"L_inf": float(L_inf), "dL_inf": float(dL_inf), "phi": phi, "sr": sr, "G": G}, 
                         thresholds, timestamp)

    # 6) α_eff – aceleração por CAOS⁺, SR e G (fail-closed)
    try:
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
        
        return LifeVerdict(True, float(alpha_eff), reasons, metrics, thresholds, timestamp)
    except Exception as e:
        reasons["alpha_eff_error"] = str(e)
        return LifeVerdict(False, 0.0, reasons, {}, thresholds, timestamp)


def quick_life_check(
    base_alpha: float = 0.001,
    C: float = 0.6, A: float = 0.6, O: float = 0.8, S: float = 0.9,
    awareness: float = 0.85, ethics_ok: bool = True, autocorr: float = 0.80, metacog: float = 0.82,
    G: float = 0.90, dL_inf: float = 0.02,
    ece: float = 0.005, rho_bias: float = 1.01, consent: bool = True, eco_ok: bool = True
) -> LifeVerdict:
    """Verificação rápida da Equação de Vida para testes"""
    
    ethics_input = {
        "ece": ece,
        "rho_bias": rho_bias,
        "consent_valid": consent,
        "eco_impact": 0.3 if eco_ok else 0.8
    }
    
    risk_series = [0.9, 0.85, 0.82]  # Série contrativa
    caos_components = (C, A, O, S)
    sr_components = (awareness, ethics_ok, autocorr, metacog)
    
    linf_weights = {"metric1": 1.0, "metric2": 1.0, "lambda_c": 0.1}
    linf_metrics = {"metric1": 0.8, "metric2": 0.9}
    
    thresholds = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    }
    
    return life_equation(
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


def validate_life_equation_gates() -> Dict[str, Any]:
    """Valida que todos os gates da Equação de Vida funcionam corretamente"""
    results = {}
    
    # Teste 1: Tudo OK - deve passar
    verdict_ok = quick_life_check()
    results["all_ok"] = {
        "passed": verdict_ok.ok,
        "alpha_eff": verdict_ok.alpha_eff,
        "expected": "should_pass"
    }
    
    # Teste 2: ECE alto - deve falhar
    verdict_ece = quick_life_check(ece=0.05)
    results["high_ece"] = {
        "passed": verdict_ece.ok,
        "alpha_eff": verdict_ece.alpha_eff,
        "expected": "should_fail"
    }
    
    # Teste 3: ΔL∞ baixo - deve falhar
    verdict_dlinf = quick_life_check(dL_inf=0.005)
    results["low_dlinf"] = {
        "passed": verdict_dlinf.ok,
        "alpha_eff": verdict_dlinf.alpha_eff,
        "expected": "should_fail"
    }
    
    # Teste 4: G baixo - deve falhar
    verdict_g = quick_life_check(G=0.70)
    results["low_g"] = {
        "passed": verdict_g.ok,
        "alpha_eff": verdict_g.alpha_eff,
        "expected": "should_fail"
    }
    
    # Teste 5: Ética falha - deve falhar
    verdict_ethics = quick_life_check(ethics_ok=False)
    results["ethics_fail"] = {
        "passed": verdict_ethics.ok,
        "alpha_eff": verdict_ethics.alpha_eff,
        "expected": "should_fail"
    }
    
    return results


class LifeEquationEngine:
    """Engine para a Equação de Vida (+) com configuração persistente"""
    
    def __init__(self, 
                 base_alpha: float = 0.001,
                 thresholds: Optional[Dict[str, float]] = None):
        self.base_alpha = base_alpha
        self.thresholds = thresholds or {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        self.history = []
    
    def evaluate(self, 
                 ethics_input: Dict[str, Any],
                 risk_series: List[float],
                 caos_components: Tuple[float, float, float, float],
                 sr_components: Tuple[float, float, float, float],
                 linf_weights: Dict[str, float],
                 linf_metrics: Dict[str, float],
                 cost: float,
                 ethical_ok_flag: bool,
                 G: float,
                 dL_inf: float) -> LifeVerdict:
        """Avalia a Equação de Vida com os parâmetros fornecidos"""
        
        verdict = life_equation(
            base_alpha=self.base_alpha,
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
            thresholds=self.thresholds
        )
        
        # Adicionar ao histórico
        self.history.append(verdict)
        if len(self.history) > 100:  # Manter apenas os últimos 100
            self.history.pop(0)
            
        return verdict
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do histórico"""
        if not self.history:
            return {"count": 0}
        
        passed_count = sum(1 for v in self.history if v.ok)
        total_count = len(self.history)
        
        alpha_effs = [v.alpha_eff for v in self.history if v.ok]
        avg_alpha_eff = sum(alpha_effs) / len(alpha_effs) if alpha_effs else 0.0
        
        return {
            "count": total_count,
            "passed_count": passed_count,
            "pass_rate": passed_count / total_count,
            "avg_alpha_eff": avg_alpha_eff,
            "latest_verdict": self.history[-1].to_dict()
        }
    
    def update_thresholds(self, **kwargs):
        """Atualiza thresholds"""
        self.thresholds.update(kwargs)