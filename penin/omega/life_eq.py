"""
Life Equation (+) - Non-Compensatory Gate & Positive Evolution Orchestrator
==========================================================================

Implements the Life Equation (+) as the counterpart to the Death Equation.
This is the central orchestrator that determines WHEN and WITH WHAT STEP (α_eff)
the system should evolve, under strict fail-closed constraints.

Key principles:
- Non-compensatory: ANY gate failure → α_eff = 0 (fail-closed)
- α_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
- All checks must pass: Σ-Guard, IR→IC, CAOS⁺, SR, ΔL∞, G (global coherence)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

# Import existing omega modules
from .guards import sigma_guard, ir_to_ic_contractive, SigmaGuardPolicy
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import quick_sr_harmonic


@dataclass
class LifeVerdict:
    """Result of Life Equation (+) evaluation"""
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_eff": self.alpha_eff,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "thresholds": self.thresholds
        }


def _accel(phi: float, kappa: float = 20.0) -> float:
    """
    Smooth, monotonic, saturated acceleration function (fail-closed-friendly).
    
    Formula: α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    
    This ensures:
    - Output is always in (0, 1]
    - Monotonic increase with phi
    - Saturated at high values
    - Never explodes numerically
    
    Args:
        phi: CAOS⁺ phi value [0, 1]
        kappa: Scaling factor (default 20.0)
        
    Returns:
        Acceleration multiplier in (0, 1]
    """
    return (1.0 + kappa * max(0.0, min(1.0, phi))) / (1.0 + kappa)


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
    G: float,    # Global coherence (Ω-ΣEA)
    dL_inf: float,  # ΔL∞ in the cycle
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    """
    Implements the Life Equation (+) as the positive evolution orchestrator.
    
    This is a non-compensatory gate: if ANY condition fails, alpha_eff = 0 (fail-closed).
    
    Formula:
        α_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
        
    Gates (all must pass):
        1. Σ-Guard (ethics): ECE, ρ_bias, consent, eco_ok
        2. IR→IC (contractivity): ρ < 1
        3. CAOS⁺: φ ≥ theta_caos
        4. SR: SR ≥ tau_sr
        5. ΔL∞: dL_inf ≥ beta_min
        6. G (global coherence): G ≥ theta_G
    
    Args:
        base_alpha: Base learning rate/step size
        ethics_input: Dict with ECE, rho_bias, fairness, consent, eco_ok, thresholds
        risk_series: Historical risk values for IR→IC check
        caos_components: (C, A, O, S) tuple for CAOS⁺
        sr_components: (awareness, ethics_ok, autocorr, metacog) tuple for SR
        linf_weights: Weights for L∞ calculation
        linf_metrics: Metrics for L∞ calculation
        cost: Cost of the operation
        ethical_ok_flag: Additional ethics flag
        G: Global coherence score (Ω-ΣEA)
        dL_inf: Delta L∞ from current cycle
        thresholds: Dict with beta_min, theta_caos, tau_sr, theta_G
        
    Returns:
        LifeVerdict with ok status, alpha_eff, reasons, metrics, and thresholds
    """
    reasons = {}
    
    # Gate 1: Σ-Guard (ethics) - non-compensatory
    print("  🛡️  Gate 1: Σ-Guard (ethics)...")
    sigma_result = sigma_guard(ethics_input, policy=None)
    reasons["sigma_ok"] = sigma_result.passed
    reasons["sigma_details"] = sigma_result.details
    
    if not (sigma_result.passed and ethical_ok_flag):
        print(f"    ❌ FAILED: sigma={sigma_result.passed}, ethical_flag={ethical_ok_flag}")
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    print("    ✅ PASSED")
    
    # Gate 2: IR→IC (contractivity of risk)
    print("  🛡️  Gate 2: IR→IC (risk contractivity)...")
    iric_result = ir_to_ic_contractive(risk_series, rho_threshold=1.0)
    reasons["risk_contractive"] = iric_result.passed
    reasons["risk_rho"] = iric_result.details.get("avg_ratio", 1.0)
    
    if not iric_result.passed:
        rho = reasons["risk_rho"]
        print(f"    ❌ FAILED: ρ={rho:.4f} >= 1.0")
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    print(f"    ✅ PASSED: ρ={reasons['risk_rho']:.4f}")
    
    # Gate 3: CAOS⁺ and SR
    print("  🛡️  Gate 3: CAOS⁺...")
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)  # Stable (log+tanh)
    reasons["caos_phi"] = phi
    
    theta_caos = thresholds.get("theta_caos", 0.25)
    if phi < theta_caos:
        print(f"    ❌ FAILED: φ={phi:.4f} < {theta_caos}")
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    print(f"    ✅ PASSED: φ={phi:.4f}")
    
    print("  🛡️  Gate 4: SR-Ω∞...")
    awr, eth_ok, autoc, meta = sr_components
    sr = quick_sr_harmonic(awr, eth_ok, autoc, meta)  # Non-compensatory (harmonic/min-soft)
    reasons["sr"] = sr
    
    tau_sr = thresholds.get("tau_sr", 0.80)
    if sr < tau_sr:
        print(f"    ❌ FAILED: SR={sr:.4f} < {tau_sr}")
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    print(f"    ✅ PASSED: SR={sr:.4f}")
    
    # Gate 4: L∞ and ΔL∞ (anti-Goodhart)
    print("  🛡️  Gate 5: L∞ and ΔL∞...")
    # Ensure weights and metrics have same keys
    metric_keys = [k for k in linf_metrics.keys() if k != "lambda_c"]
    m_vals = [linf_metrics[k] for k in metric_keys]
    w_vals = [linf_weights.get(k, 1.0) for k in metric_keys]
    
    L_inf = linf_harmonic(
        m_vals,
        w_vals,
        cost_norm=cost,
        lambda_c=linf_weights.get("lambda_c", 0.0),
        ethical_ok=True,
    )
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    
    beta_min = thresholds.get("beta_min", 0.01)
    if dL_inf < beta_min:
        print(f"    ❌ FAILED: ΔL∞={dL_inf:.4f} < {beta_min}")
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)
    print(f"    ✅ PASSED: ΔL∞={dL_inf:.4f}")
    
    # Gate 5: Global coherence Ω-ΣEA (harmonic mean of 8 modules)
    print("  🛡️  Gate 6: Global coherence (G)...")
    reasons["G"] = G
    
    theta_G = thresholds.get("theta_G", 0.85)
    if G < theta_G:
        print(f"    ❌ FAILED: G={G:.4f} < {theta_G}")
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)
    print(f"    ✅ PASSED: G={G:.4f}")
    
    # Gate 6: Calculate α_eff - acceleration by CAOS⁺, SR and G (fail-closed)
    print("  🔧 Calculating α_eff...")
    alpha_eff = base_alpha * phi * sr * G * _accel(phi, kappa=20.0)
    print(f"    α_eff = {base_alpha:.6f} * {phi:.4f} * {sr:.4f} * {G:.4f} * {_accel(phi):.4f} = {alpha_eff:.6f}")
    
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
        "rho": float(reasons["risk_rho"]),
    }
    
    print("  ✅ ALL GATES PASSED - Evolution authorized!")
    return LifeVerdict(True, float(alpha_eff), reasons, metrics, thresholds)


def quick_life_check(
    base_alpha: float = 1e-3,
    C: float = 0.6,
    A: float = 0.6, 
    O: float = 1.0,
    S: float = 1.0,
    awareness: float = 0.85,
    ethics_ok: bool = True,
    autocorr: float = 0.80,
    metacog: float = 0.82,
    G: float = 0.90,
    dL_inf: float = 0.02,
) -> LifeVerdict:
    """Quick life equation check for testing"""
    
    ethics_input = {
        "ece": 0.005,
        "rho_bias": 1.01,
        "fairness": 0.9,
        "consent": 1,
        "eco_ok": 1,
        "thresholds": {},
        "consent_valid": True,
        "eco_impact": 0.3
    }
    
    risk_series = [0.9, 0.88, 0.85]
    
    linf_weights = {"w1": 1.0, "w2": 1.0, "lambda_c": 0.1}
    linf_metrics = {"w1": 0.8, "w2": 0.9}
    
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
        caos_components=(C, A, O, S),
        sr_components=(awareness, 1.0 if ethics_ok else 0.001, autocorr, metacog),
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=0.02,
        ethical_ok_flag=ethics_ok,
        G=G,
        dL_inf=dL_inf,
        thresholds=thresholds
    )


# Convenience functions for integration
def compute_alpha_eff(
    state: Dict[str, Any],
    base_alpha: float = 1e-3
) -> Tuple[float, LifeVerdict]:
    """
    Compute effective alpha from current state.
    
    Args:
        state: Current system state with all metrics
        base_alpha: Base learning rate
        
    Returns:
        (alpha_eff, verdict) tuple
    """
    # Extract components from state
    ethics_input = state.get("ethics", {})
    risk_series = state.get("risk_history", [0.9, 0.88, 0.85])
    caos_components = (
        state.get("C", 0.6),
        state.get("A", 0.6),
        state.get("O", 1.0),
        state.get("S", 1.0)
    )
    sr_components = (
        state.get("awareness", 0.85),
        state.get("ethics_ok", True),
        state.get("autocorrection", 0.80),
        state.get("metacognition", 0.82)
    )
    linf_weights = state.get("linf_weights", {"w1": 1.0, "w2": 1.0, "lambda_c": 0.1})
    linf_metrics = state.get("linf_metrics", {"w1": 0.8, "w2": 0.9})
    cost = state.get("cost", 0.02)
    ethical_ok_flag = state.get("ethical_ok_flag", True)
    G = state.get("G", 0.90)
    dL_inf = state.get("dL_inf", 0.02)
    thresholds = state.get("thresholds", {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    })
    
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
        thresholds=thresholds
    )
    
    return verdict.alpha_eff, verdict