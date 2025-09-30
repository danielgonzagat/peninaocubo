# penin/omega/life_eq.py
"""
Equação de Vida (+) - Gate Não-Compensatório e Orquestrador Positivo
===================================================================

Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).

Fórmula:
alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)

Onde:
- φ(CAOS⁺): Função CAOS⁺ (Complexity, Adaptability, Openness, Stability)
- SR: Self-Reflection Ω∞ (não-compensatório)
- G: Coerência global (Ω-ΣEA)
- accel(φ): Função de aceleração suave baseada em φ

Gates não-compensatórios:
1. Σ-Guard (ética): ECE ≤ 0.01, ρ_bias ≤ 1.05, consent=True, eco_ok=True
2. IR→IC (contratividade): ρ < 1.0
3. CAOS⁺: φ ≥ theta_caos (default: 0.25)
4. SR: SR ≥ tau_sr (default: 0.80)
5. ΔL∞: ΔL∞ ≥ beta_min (default: 0.01)
6. G: G ≥ theta_G (default: 0.85)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional
import time

# Motores existentes no repo
from .guards import sigma_guard, ir_to_ic_contractive, SigmaGuard, IRICGuard
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega, SROmegaEngine, SRComponents


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
    
    Fórmula: α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    
    Args:
        phi: Valor φ do CAOS⁺ [0,1]
        kappa: Parâmetro de aceleração (default: 20.0)
        
    Returns:
        Fator de aceleração [0,1]
    """
    phi = max(0.0, min(1.0, phi))  # Clamp to [0,1]
    kappa = max(1.0, kappa)  # Ensure kappa >= 1
    return (1.0 + kappa * phi) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float] | List[float],
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
    
    Args:
        base_alpha: Alpha base para modulação
        ethics_input: Métricas éticas (ece, rho_bias, fairness, consent, eco_ok)
        risk_series: Série de risco para IR→IC (dict ou list)
        caos_components: (C, A, O, S) para CAOS⁺
        sr_components: (awareness, ethics_ok, autocorr, metacog) para SR
        linf_weights: Pesos para L∞
        linf_metrics: Métricas para L∞
        cost: Custo atual
        ethical_ok_flag: Flag ético global
        G: Coerência global Ω-ΣEA
        dL_inf: ΔL∞ do ciclo
        thresholds: Thresholds dos gates
        
    Returns:
        LifeVerdict com resultado e detalhes
    """
    reasons = {}
    timestamp = time.time()
    
    # Thresholds padrão
    beta_min = thresholds.get("beta_min", 0.01)
    theta_caos = thresholds.get("theta_caos", 0.25)
    tau_sr = thresholds.get("tau_sr", 0.80)
    theta_G = thresholds.get("theta_G", 0.85)
    
    # 1) Σ-Guard (ética) – não compensatório
    try:
        sigma_guard_instance = SigmaGuard(
            ece_max=ethics_input.get("ece_max", 0.01),
            rho_bias_max=ethics_input.get("rho_bias_max", 1.05),
            require_consent=ethics_input.get("require_consent", True),
            require_eco=ethics_input.get("require_eco", True)
        )
        
        sigma_result, sigma_violations, sigma_details = sigma_guard_instance.check(ethics_input)
        ok_sigma = sigma_result.passed
        
    except Exception as e:
        ok_sigma = False
        sigma_details = {"error": str(e)}
        
    reasons["sigma_ok"] = ok_sigma
    reasons["sigma_details"] = sigma_details
    
    if not (ok_sigma and ethical_ok_flag):
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # 2) IR→IC (contratividade de risco)
    try:
        # Converter risk_series para lista se necessário
        if isinstance(risk_series, dict):
            risk_list = list(risk_series.values())
        else:
            risk_list = list(risk_series)
            
        iric_guard = IRICGuard(rho_threshold=1.0)
        iric_result, iric_violations, iric_evidence = iric_guard.check(risk_list)
        contractive = iric_result.passed
        rho = iric_evidence.get("avg_ratio", 1.0)
        
    except Exception as e:
        contractive = False
        rho = 1.0
        iric_evidence = {"error": str(e)}
        
    reasons["risk_contractive"] = contractive
    reasons["risk_rho"] = rho
    reasons["iric_evidence"] = iric_evidence
    
    if not contractive:
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={"rho": rho}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # 3) CAOS⁺ e SR
    try:
        C, A, O, S = caos_components
        phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)  # estável (log+tanh)
        
    except Exception as e:
        phi = 0.0
        
    reasons["caos_phi"] = phi
    reasons["caos_components"] = {"C": C, "A": A, "O": O, "S": S}
    
    if phi < theta_caos:
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={"phi": phi, "rho": rho}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # SR-Ω∞
    try:
        awr, eth_ok, autoc, meta = sr_components
        
        # Usar SROmegaEngine para cálculo não-compensatório
        sr_engine = SROmegaEngine()
        sr_comp = SRComponents(
            awareness=awr,
            ethics=1.0 if eth_ok else 0.001,  # Valor muito baixo para veto ético
            autocorrection=autoc,
            metacognition=meta
        )
        sr, sr_details = sr_engine.compute_sr(sr_comp)
        
    except Exception as e:
        sr = 0.0
        sr_details = {"error": str(e)}
        
    reasons["sr"] = sr
    reasons["sr_details"] = sr_details
    reasons["sr_components"] = {"awareness": awr, "ethics_ok": eth_ok, "autocorrection": autoc, "metacognition": meta}
    
    if sr < tau_sr:
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={"phi": phi, "sr": sr, "rho": rho}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # 4) L∞ e ΔL∞ (anti-Goodhart)
    try:
        L_inf = linf_harmonic(
            linf_metrics,
            linf_weights,
            cost_norm=cost,
            lambda_c=linf_weights.get("lambda_c", 0.0),
            ethical_ok=True,
        )
    except Exception as e:
        L_inf = 0.0
        
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    
    if dL_inf < beta_min:
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={"L_inf": float(L_inf), "dL_inf": float(dL_inf), "phi": phi, "sr": sr, "rho": rho}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # 5) Coerência global Ω-ΣEA (média harmônica dos 8 módulos)
    reasons["G"] = G
    if G < theta_G:
        return LifeVerdict(
            ok=False, 
            alpha_eff=0.0, 
            reasons=reasons, 
            metrics={"L_inf": float(L_inf), "dL_inf": float(dL_inf), "phi": phi, "sr": sr, "G": G, "rho": rho}, 
            thresholds=thresholds,
            timestamp=timestamp
        )

    # 6) α_eff – aceleração por CAOS⁺, SR e G (fail-closed)
    try:
        accel_factor = _accel(phi, kappa=20.0)
        alpha_eff = base_alpha * phi * sr * G * accel_factor
        
    except Exception as e:
        alpha_eff = 0.0
        accel_factor = 0.0
        
    reasons["accel_factor"] = accel_factor
    reasons["alpha_calculation"] = {
        "base_alpha": base_alpha,
        "phi": phi,
        "sr": sr,
        "G": G,
        "accel_factor": accel_factor,
        "formula": "base_alpha * phi * sr * G * accel_factor"
    }

    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
        "rho": float(rho),
        "accel_factor": float(accel_factor)
    }
    
    return LifeVerdict(
        ok=True, 
        alpha_eff=float(alpha_eff), 
        reasons=reasons, 
        metrics=metrics, 
        thresholds=thresholds,
        timestamp=timestamp
    )


class LifeEquationEngine:
    """
    Engine para a Equação de Vida (+) com configuração persistente
    """
    
    def __init__(self, 
                 thresholds: Optional[Dict[str, float]] = None,
                 base_alpha: float = 0.001):
        """
        Args:
            thresholds: Thresholds dos gates
            base_alpha: Alpha base padrão
        """
        if thresholds is None:
            thresholds = {
                "beta_min": 0.01,
                "theta_caos": 0.25,
                "tau_sr": 0.80,
                "theta_G": 0.85
            }
        
        self.thresholds = thresholds
        self.base_alpha = base_alpha
        self.history = []
        
    def evaluate(self, **kwargs) -> LifeVerdict:
        """
        Avalia a Equação de Vida (+) com os parâmetros fornecidos
        
        Args:
            **kwargs: Parâmetros para life_equation()
            
        Returns:
            LifeVerdict
        """
        # Usar base_alpha padrão se não fornecido
        if "base_alpha" not in kwargs:
            kwargs["base_alpha"] = self.base_alpha
            
        # Usar thresholds padrão se não fornecido
        if "thresholds" not in kwargs:
            kwargs["thresholds"] = self.thresholds
            
        verdict = life_equation(**kwargs)
        
        # Adicionar ao histórico
        self.history.append(verdict)
        if len(self.history) > 100:  # Manter apenas últimos 100
            self.history.pop(0)
            
        return verdict
        
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do histórico"""
        if not self.history:
            return {"count": 0}
            
        total = len(self.history)
        passed = sum(1 for v in self.history if v.ok)
        
        alpha_values = [v.alpha_eff for v in self.history]
        avg_alpha = sum(alpha_values) / len(alpha_values) if alpha_values else 0.0
        
        return {
            "count": total,
            "passed": passed,
            "pass_rate": passed / total,
            "avg_alpha_eff": avg_alpha,
            "latest_verdict": self.history[-1].to_dict() if self.history else None
        }
        
    def update_thresholds(self, **new_thresholds):
        """Atualiza thresholds"""
        self.thresholds.update(new_thresholds)
        
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "thresholds": self.thresholds.copy(),
            "base_alpha": self.base_alpha,
            "history_length": len(self.history)
        }


# Funções de conveniência para testes
def quick_life_check(
    caos_components: Tuple[float, float, float, float],
    sr_components: Tuple[float, float, float, float],
    G: float = 0.9,
    dL_inf: float = 0.02,
    ethical_ok: bool = True
) -> Tuple[bool, float]:
    """
    Verificação rápida da Equação de Vida (+)
    
    Returns:
        (passed, alpha_eff)
    """
    # Parâmetros mínimos para teste
    ethics_input = {
        "ece": 0.005,
        "rho_bias": 1.01,
        "fairness": 0.9,
        "consent_valid": True,
        "eco_impact": 0.3
    }
    
    risk_series = [0.9, 0.88, 0.85]  # Série contrativa
    
    linf_weights = {"metric1": 1.0, "metric2": 1.0}
    linf_metrics = {"metric1": 0.8, "metric2": 0.9}
    
    thresholds = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    }
    
    verdict = life_equation(
        base_alpha=0.001,
        ethics_input=ethics_input,
        risk_series=risk_series,
        caos_components=caos_components,
        sr_components=sr_components,
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=0.02,
        ethical_ok_flag=ethical_ok,
        G=G,
        dL_inf=dL_inf,
        thresholds=thresholds
    )
    
    return verdict.ok, verdict.alpha_eff


def validate_life_equation_gates() -> Dict[str, Any]:
    """
    Valida que todos os gates da Equação de Vida (+) funcionam corretamente
    
    Returns:
        Dict com resultados dos testes
    """
    results = {}
    
    # Caso base (deve passar)
    base_case = quick_life_check(
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        G=0.90,
        dL_inf=0.02,
        ethical_ok=True
    )
    results["base_case"] = {"passed": base_case[0], "alpha_eff": base_case[1]}
    
    # Teste gate ético
    ethics_fail = quick_life_check(
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        G=0.90,
        dL_inf=0.02,
        ethical_ok=False  # Falha ética
    )
    results["ethics_fail"] = {"passed": ethics_fail[0], "alpha_eff": ethics_fail[1]}
    
    # Teste CAOS⁺ baixo
    caos_fail = quick_life_check(
        caos_components=(0.1, 0.1, 0.1, 0.1),  # CAOS⁺ muito baixo
        sr_components=(0.85, True, 0.80, 0.82),
        G=0.90,
        dL_inf=0.02,
        ethical_ok=True
    )
    results["caos_fail"] = {"passed": caos_fail[0], "alpha_eff": caos_fail[1]}
    
    # Teste SR baixo
    sr_fail = quick_life_check(
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.1, True, 0.1, 0.1),  # SR muito baixo
        G=0.90,
        dL_inf=0.02,
        ethical_ok=True
    )
    results["sr_fail"] = {"passed": sr_fail[0], "alpha_eff": sr_fail[1]}
    
    # Teste G baixo
    g_fail = quick_life_check(
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        G=0.5,  # G muito baixo
        dL_inf=0.02,
        ethical_ok=True
    )
    results["g_fail"] = {"passed": g_fail[0], "alpha_eff": g_fail[1]}
    
    # Teste ΔL∞ baixo
    dlinf_fail = quick_life_check(
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        G=0.90,
        dL_inf=0.005,  # ΔL∞ muito baixo
        ethical_ok=True
    )
    results["dlinf_fail"] = {"passed": dlinf_fail[0], "alpha_eff": dlinf_fail[1]}
    
    # Resumo
    total_tests = len(results)
    expected_passes = 1  # Apenas base_case deve passar
    actual_passes = sum(1 for r in results.values() if r["passed"])
    
    results["summary"] = {
        "total_tests": total_tests,
        "expected_passes": expected_passes,
        "actual_passes": actual_passes,
        "gates_working": actual_passes == expected_passes
    }
    
    return results