"""
Σ-Guard - Complete Implementation
==================================

Non-compensatory fail-closed security gate with 10 gates.

Formula:
    V_t = 𝟙_{ρ<1 ∧ ECE≤0.01 ∧ ρ_bias≤1.05 ∧ SR≥0.80 ∧ G≥0.85 ∧ ΔL∞≥β_min ∧ κ≥20 ∧ consent ∧ eco_ok}

Gates:
    1. Contractivity (ρ < 1) - IR→IC
    2. Calibration (ECE ≤ 0.01)
    3. Bias (ρ_bias ≤ 1.05)
    4. SR score (SR ≥ 0.80) - reflexivity
    5. Coherence (G ≥ 0.85) - global coherence
    6. Improvement (ΔL∞ ≥ β_min)
    7. Cost (within budget)
    8. Kappa (κ ≥ 20)
    9. Consent (explicit)
   10. Ecological (eco_ok)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class GateStatus(Enum):
    """Gate status"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"  # Not evaluated


@dataclass
class GateResult:
    """Result of a single gate evaluation"""
    gate_name: str
    status: GateStatus
    actual_value: Optional[float] = None
    threshold: Optional[float] = None
    reason: str = ""


@dataclass
class GuardEvaluation:
    """Complete Σ-Guard evaluation result"""
    verdict: str  # "PASS" or "FAIL"
    gates: List[GateResult]
    failed_gates: List[str]
    passed_gates: List[str]
    all_pass: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'verdict': self.verdict,
            'gates': {g.gate_name: g.status.value for g in self.gates},
            'failed_gates': self.failed_gates,
            'passed_gates': self.passed_gates,
            'all_pass': self.all_pass,
        }


@dataclass
class GuardThresholds:
    """Σ-Guard thresholds (configurable via foundation.yaml or env)"""
    
    # Contractivity
    rho_max: float = 0.95  # ρ < 1 (strictly contractive)
    
    # Calibration
    ece_max: float = 0.01  # ECE ≤ 1%
    
    # Bias
    rho_bias_max: float = 1.05  # Demographic parity ≤ 5% deviation
    
    # Reflexivity
    sr_min: float = 0.80  # SR-Ω∞ ≥ 0.80
    
    # Coherence
    g_min: float = 0.85  # Global coherence ≥ 0.85
    
    # Improvement
    beta_min: float = 0.01  # ΔL∞ ≥ 1%
    
    # Kappa
    kappa_min: float = 20.0  # κ ≥ 20
    
    # Budget
    cost_max_multiplier: float = 1.10  # Cost ≤ 110% of budget


class SigmaGuard:
    """
    Σ-Guard: Complete non-compensatory fail-closed gate.
    
    Properties:
    - Non-compensatory: ALL gates must pass
    - Fail-closed: Default deny
    - Auditable: All decisions logged with reasons
    """
    
    def __init__(self, thresholds: Optional[GuardThresholds] = None):
        self.thresholds = thresholds or GuardThresholds()
    
    def evaluate_gate_contractivity(self, metrics: Dict) -> GateResult:
        """Gate 1: Contractivity (IR→IC)"""
        rho = metrics.get('rho', 1.0)
        
        passed = rho < self.thresholds.rho_max
        
        return GateResult(
            gate_name="contractivity",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=rho,
            threshold=self.thresholds.rho_max,
            reason=f"ρ={rho:.3f} {'<' if passed else '≥'} {self.thresholds.rho_max}"
        )
    
    def evaluate_gate_calibration(self, metrics: Dict) -> GateResult:
        """Gate 2: Calibration"""
        ece = metrics.get('ece', 1.0)
        
        passed = ece <= self.thresholds.ece_max
        
        return GateResult(
            gate_name="calibration",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=ece,
            threshold=self.thresholds.ece_max,
            reason=f"ECE={ece:.4f} {'≤' if passed else '>'} {self.thresholds.ece_max}"
        )
    
    def evaluate_gate_bias(self, metrics: Dict) -> GateResult:
        """Gate 3: Bias (demographic parity)"""
        rho_bias = metrics.get('rho_bias', 2.0)
        
        passed = rho_bias <= self.thresholds.rho_bias_max
        
        return GateResult(
            gate_name="bias",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=rho_bias,
            threshold=self.thresholds.rho_bias_max,
            reason=f"ρ_bias={rho_bias:.3f} {'≤' if passed else '>'} {self.thresholds.rho_bias_max}"
        )
    
    def evaluate_gate_sr(self, metrics: Dict) -> GateResult:
        """Gate 4: SR-Ω∞ (reflexivity)"""
        sr = metrics.get('sr', 0.0)
        
        passed = sr >= self.thresholds.sr_min
        
        return GateResult(
            gate_name="sr_score",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=sr,
            threshold=self.thresholds.sr_min,
            reason=f"SR={sr:.3f} {'≥' if passed else '<'} {self.thresholds.sr_min}"
        )
    
    def evaluate_gate_coherence(self, metrics: Dict) -> GateResult:
        """Gate 5: Global coherence"""
        g = metrics.get('g', 0.0)
        
        passed = g >= self.thresholds.g_min
        
        return GateResult(
            gate_name="coherence",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=g,
            threshold=self.thresholds.g_min,
            reason=f"G={g:.3f} {'≥' if passed else '<'} {self.thresholds.g_min}"
        )
    
    def evaluate_gate_improvement(self, metrics: Dict) -> GateResult:
        """Gate 6: Improvement (ΔL∞)"""
        delta_linf = metrics.get('delta_linf', -1.0)
        
        passed = delta_linf >= self.thresholds.beta_min
        
        return GateResult(
            gate_name="improvement",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=delta_linf,
            threshold=self.thresholds.beta_min,
            reason=f"ΔL∞={delta_linf:+.4f} {'≥' if passed else '<'} {self.thresholds.beta_min}"
        )
    
    def evaluate_gate_cost(self, metrics: Dict) -> GateResult:
        """Gate 7: Cost (within budget)"""
        cost = metrics.get('cost', 1000.0)
        budget = metrics.get('budget', 0.0)
        max_cost = budget * self.thresholds.cost_max_multiplier
        
        passed = cost <= max_cost
        
        return GateResult(
            gate_name="cost",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=cost,
            threshold=max_cost,
            reason=f"Cost={cost:.3f} {'≤' if passed else '>'} {max_cost:.3f} (budget={budget:.3f})"
        )
    
    def evaluate_gate_kappa(self, metrics: Dict) -> GateResult:
        """Gate 8: Kappa (κ ≥ 20)"""
        kappa = metrics.get('kappa', 0.0)
        
        passed = kappa >= self.thresholds.kappa_min
        
        return GateResult(
            gate_name="kappa",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=kappa,
            threshold=self.thresholds.kappa_min,
            reason=f"κ={kappa:.1f} {'≥' if passed else '<'} {self.thresholds.kappa_min}"
        )
    
    def evaluate_gate_consent(self, metrics: Dict) -> GateResult:
        """Gate 9: Consent (explicit user consent)"""
        consent = metrics.get('consent', False)
        
        passed = consent is True
        
        return GateResult(
            gate_name="consent",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=1.0 if consent else 0.0,
            threshold=1.0,
            reason=f"Consent={'granted' if passed else 'not granted'}"
        )
    
    def evaluate_gate_ecological(self, metrics: Dict) -> GateResult:
        """Gate 10: Ecological (eco footprint OK)"""
        eco_ok = metrics.get('eco_ok', False)
        
        passed = eco_ok is True
        
        return GateResult(
            gate_name="ecological",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            actual_value=1.0 if eco_ok else 0.0,
            threshold=1.0,
            reason=f"Ecological={'OK' if passed else 'NOT OK'}"
        )
    
    def evaluate(self, metrics: Dict) -> GuardEvaluation:
        """
        Evaluate ALL 10 gates (non-compensatory).
        
        Args:
            metrics: Dictionary with all required metrics:
                - rho: Contractivity factor
                - ece: Expected calibration error
                - rho_bias: Bias ratio
                - sr: SR-Ω∞ score
                - g: Global coherence
                - delta_linf: Improvement
                - cost: Mutation cost
                - budget: Available budget
                - kappa: CAOS+ kappa
                - consent: User consent (bool)
                - eco_ok: Ecological OK (bool)
        
        Returns:
            GuardEvaluation with verdict and details
        """
        
        # Evaluate all gates
        gates = [
            self.evaluate_gate_contractivity(metrics),
            self.evaluate_gate_calibration(metrics),
            self.evaluate_gate_bias(metrics),
            self.evaluate_gate_sr(metrics),
            self.evaluate_gate_coherence(metrics),
            self.evaluate_gate_improvement(metrics),
            self.evaluate_gate_cost(metrics),
            self.evaluate_gate_kappa(metrics),
            self.evaluate_gate_consent(metrics),
            self.evaluate_gate_ecological(metrics),
        ]
        
        # Extract results
        failed_gates = [g.gate_name for g in gates if g.status == GateStatus.FAIL]
        passed_gates = [g.gate_name for g in gates if g.status == GateStatus.PASS]
        all_pass = len(failed_gates) == 0
        
        # Non-compensatory: ALL must pass
        verdict = "PASS" if all_pass else "FAIL"
        
        return GuardEvaluation(
            verdict=verdict,
            gates=gates,
            failed_gates=failed_gates,
            passed_gates=passed_gates,
            all_pass=all_pass,
        )
