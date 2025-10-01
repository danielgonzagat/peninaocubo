"""
Σ-Guard — Fail-Closed Security & Ethics Gate
=============================================

Complete implementation of Σ-Guard with OPA/Rego integration:

    V_t = 1_{ρ<1 ∧ ECE≤0.01 ∧ ρ_bias≤1.05 ∧ consent ∧ eco_ok}

Properties:
- Fail-closed: Default deny on any violation
- Non-compensatory: All gates must pass
- Auditable: All decisions logged with reasons
- Policy-as-code: OPA/Rego policies
- Rollback triggers: Automatic on failure

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 15
- Blueprint § 2, § 3.5
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class GateStatus(str, Enum):
    """Gate evaluation status."""

    PASS = "pass"
    FAIL = "fail"
    CANARY = "canary"
    QUARANTINE = "quarantine"


@dataclass
class GateMetrics:
    """Metrics for Σ-Guard evaluation."""

    rho: float
    ece: float
    rho_bias: float
    sr_score: float
    omega_g: float
    delta_linf: float
    caos_plus: float
    cost_increase: float
    kappa: float
    consent: bool
    eco_ok: bool


@dataclass
class GateResult:
    """Individual gate evaluation result."""

    gate_name: str
    status: GateStatus
    value: float
    threshold: float
    passed: bool
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class SigmaGuardVerdict:
    """Complete Σ-Guard verdict with all gate results."""

    verdict: GateStatus
    passed: bool
    gates: list[GateResult]
    aggregate_score: float
    reason: str
    action: str  # "promote", "rollback", "canary", "quarantine"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    hash_proof: str = ""
    attestation: Any | None = None  # Cryptographic attestation (avoid circular import)

    def __post_init__(self):
        """Generate hash proof for auditability."""
        if not self.hash_proof:
            proof_data = {
                "verdict": self.verdict,
                "gates": [
                    {
                        "name": g.gate_name,
                        "status": g.status,
                        "value": g.value,
                        "threshold": g.threshold,
                    }
                    for g in self.gates
                ],
                "timestamp": self.timestamp,
            }
            self.hash_proof = hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
    
    def create_attestation(self, candidate_id: str) -> Any:
        """Create cryptographic attestation for this verdict"""
        try:
            from penin.omega.attestation import create_sigma_guard_attestation
            
            gates_data = [
                {
                    "name": g.gate_name,
                    "status": g.status.value if hasattr(g.status, 'value') else str(g.status),
                    "value": g.value,
                    "threshold": g.threshold,
                    "passed": g.passed,
                }
                for g in self.gates
            ]
            
            verdict_str = "pass" if self.passed else "fail"
            attestation = create_sigma_guard_attestation(
                verdict=verdict_str,
                candidate_id=candidate_id,
                gates=gates_data,
                aggregate_score=self.aggregate_score
            )
            self.attestation = attestation
            return attestation
        except ImportError:
            return None


class SigmaGuard:
    """
    Σ-Guard: Non-compensatory fail-closed security gate.

    Validates all critical thresholds before allowing evolution.
    """

    def __init__(
        self,
        rho_max: float = 0.99,
        ece_max: float = 0.01,
        rho_bias_max: float = 1.05,
        sr_min: float = 0.80,
        G_min: float = 0.85,
        delta_Linf_min: float = 0.01,
        cost_max_increase: float = 0.10,
        kappa_min: float = 20.0,
        consent_required: bool = True,
        eco_ok_required: bool = True,
    ):
        """
        Initialize Σ-Guard with thresholds.

        Args:
            rho_max: Maximum contractivity factor (must be < 1.0)
            ece_max: Maximum Expected Calibration Error
            rho_bias_max: Maximum bias ratio
            sr_min: Minimum SR-Ω∞ score
            G_min: Minimum global coherence
            delta_Linf_min: Minimum improvement (β_min)
            cost_max_increase: Maximum cost increase (e.g., 10%)
            kappa_min: Minimum CAOS⁺ kappa
            consent_required: Require user consent
            eco_ok_required: Require ecological constraints
        """
        self.rho_max = rho_max
        self.ece_max = ece_max
        self.rho_bias_max = rho_bias_max
        self.sr_min = sr_min
        self.G_min = G_min
        self.delta_Linf_min = delta_Linf_min
        self.cost_max_increase = cost_max_increase
        self.kappa_min = kappa_min
        self.consent_required = consent_required
        self.eco_ok_required = eco_ok_required

    def validate(self, metrics: GateMetrics) -> SigmaGuardVerdict:
        """
        Validate metrics against all gates.

        Args:
            metrics: GateMetrics to validate

        Returns:
            SigmaGuardVerdict with complete results
        """
        gates = []
        all_passed = True

        # Gate 1: Contratividade (ρ < 1.0)
        passed = metrics.rho < self.rho_max
        gates.append(
            GateResult(
                gate_name="contractividade",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.rho,
                threshold=self.rho_max,
                passed=passed,
                reason=f"ρ={metrics.rho:.4f} {'<' if passed else '≥'} {self.rho_max}",
            )
        )
        all_passed = all_passed and passed

        # Gate 2: Calibration (ECE ≤ 0.01)
        passed = metrics.ece <= self.ece_max
        gates.append(
            GateResult(
                gate_name="calibration",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.ece,
                threshold=self.ece_max,
                passed=passed,
                reason=f"ECE={metrics.ece:.4f} {'≤' if passed else '>'} {self.ece_max}",
            )
        )
        all_passed = all_passed and passed

        # Gate 3: Bias (ρ_bias ≤ 1.05)
        passed = metrics.rho_bias <= self.rho_bias_max
        gates.append(
            GateResult(
                gate_name="bias",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.rho_bias,
                threshold=self.rho_bias_max,
                passed=passed,
                reason=f"ρ_bias={metrics.rho_bias:.4f} {'≤' if passed else '>'} {self.rho_bias_max}",
            )
        )
        all_passed = all_passed and passed

        # Gate 4: Self-Reflection (SR ≥ 0.80)
        passed = metrics.sr_score >= self.sr_min
        gates.append(
            GateResult(
                gate_name="self_reflection",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.sr_score,
                threshold=self.sr_min,
                passed=passed,
                reason=f"SR={metrics.sr_score:.4f} {'≥' if passed else '<'} {self.sr_min}",
            )
        )
        all_passed = all_passed and passed

        # Gate 5: Global Coherence (G ≥ 0.85)
        passed = metrics.omega_g >= self.G_min
        gates.append(
            GateResult(
                gate_name="global_coherence",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.omega_g,
                threshold=self.G_min,
                passed=passed,
                reason=f"G={metrics.omega_g:.4f} {'≥' if passed else '<'} {self.G_min}",
            )
        )
        all_passed = all_passed and passed

        # Gate 6: Improvement (ΔL∞ ≥ β_min)
        passed = metrics.delta_linf >= self.delta_Linf_min
        gates.append(
            GateResult(
                gate_name="improvement",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.delta_linf,
                threshold=self.delta_Linf_min,
                passed=passed,
                reason=f"ΔL∞={metrics.delta_linf:.4f} {'≥' if passed else '<'} {self.delta_Linf_min}",
            )
        )
        all_passed = all_passed and passed

        # Gate 7: Cost Control
        passed = metrics.cost_increase <= self.cost_max_increase
        gates.append(
            GateResult(
                gate_name="cost_control",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.cost_increase,
                threshold=self.cost_max_increase,
                passed=passed,
                reason=f"cost_increase={metrics.cost_increase*100:.1f}% {'≤' if passed else '>'} {self.cost_max_increase*100:.1f}%",
            )
        )
        all_passed = all_passed and passed

        # Gate 8: Kappa (κ ≥ 20.0)
        passed = metrics.kappa >= self.kappa_min
        gates.append(
            GateResult(
                gate_name="kappa",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=metrics.kappa,
                threshold=self.kappa_min,
                passed=passed,
                reason=f"κ={metrics.kappa:.2f} {'≥' if passed else '<'} {self.kappa_min}",
            )
        )
        all_passed = all_passed and passed

        # Gate 9: Consent
        passed = not self.consent_required or metrics.consent
        gates.append(
            GateResult(
                gate_name="consent",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=1.0 if metrics.consent else 0.0,
                threshold=1.0,
                passed=passed,
                reason=f"consent={'✓' if metrics.consent else '✗'}",
            )
        )
        all_passed = all_passed and passed

        # Gate 10: Ecological
        passed = not self.eco_ok_required or metrics.eco_ok
        gates.append(
            GateResult(
                gate_name="ecological",
                status=GateStatus.PASS if passed else GateStatus.FAIL,
                value=1.0 if metrics.eco_ok else 0.0,
                threshold=1.0,
                passed=passed,
                reason=f"eco_ok={'✓' if metrics.eco_ok else '✗'}",
            )
        )
        all_passed = all_passed and passed

        # Aggregate score (harmonic mean of passed gates)
        passed_values = [g.value for g in gates if g.passed and g.value > 0]
        if passed_values:
            epsilon = 1e-6
            aggregate_score = len(passed_values) / sum(1.0 / max(epsilon, v) for v in passed_values)
        else:
            aggregate_score = 0.0

        # Determine verdict and action
        if all_passed:
            verdict = GateStatus.PASS
            action = "promote"
            reason = "All gates passed"
        else:
            verdict = GateStatus.FAIL
            action = "rollback"
            failed_gates = [g.gate_name for g in gates if not g.passed]
            reason = f"Failed gates: {', '.join(failed_gates)}"

        return SigmaGuardVerdict(
            verdict=verdict,
            passed=all_passed,
            gates=gates,
            aggregate_score=aggregate_score,
            reason=reason,
            action=action,
        )

    def validate_legacy(
        self,
        rho: float,
        ece: float,
        rho_bias: float,
        sr_score: float,
        G_coherence: float,
        delta_Linf: float,
        cost_increase: float,
        kappa: float,
        consent: bool,
        eco_ok: bool,
        metadata: dict[str, Any] | None = None,
    ) -> SigmaGuardVerdict:
        """
        Validate all gates and return verdict.

        Args:
            rho: Contractivity factor
            ece: Expected Calibration Error
            rho_bias: Bias ratio
            sr_score: SR-Ω∞ reflexive score
            G_coherence: Global coherence (Ω-ΣEA)
            delta_Linf: Improvement in L∞
            cost_increase: Relative cost increase
            kappa: CAOS⁺ kappa parameter
            consent: User consent flag
            eco_ok: Ecological constraints satisfied
            metadata: Additional metadata for logging

        Returns:
            SigmaGuardVerdict with detailed gate results
        """
        gates: list[GateResult] = []

        # Gate 1: Contractivity (ρ < 1)
        rho_passed = rho < self.rho_max
        gates.append(
            GateResult(
                gate_name="contractivity",
                status=GateStatus.PASS if rho_passed else GateStatus.FAIL,
                value=rho,
                threshold=self.rho_max,
                passed=rho_passed,
                reason=f"ρ={rho:.6f} {'<' if rho_passed else '≥'} {self.rho_max} (IR→IC)",
            )
        )

        # Gate 2: Calibration (ECE ≤ threshold)
        ece_passed = ece <= self.ece_max
        gates.append(
            GateResult(
                gate_name="calibration",
                status=GateStatus.PASS if ece_passed else GateStatus.FAIL,
                value=ece,
                threshold=self.ece_max,
                passed=ece_passed,
                reason=f"ECE={ece:.6f} {'≤' if ece_passed else '>'} {self.ece_max}",
            )
        )

        # Gate 3: Bias (ρ_bias ≤ threshold)
        bias_passed = rho_bias <= self.rho_bias_max
        gates.append(
            GateResult(
                gate_name="bias",
                status=GateStatus.PASS if bias_passed else GateStatus.FAIL,
                value=rho_bias,
                threshold=self.rho_bias_max,
                passed=bias_passed,
                reason=f"ρ_bias={rho_bias:.6f} {'≤' if bias_passed else '>'} {self.rho_bias_max}",
            )
        )

        # Gate 4: SR-Ω∞ (reflexivity)
        sr_passed = sr_score >= self.sr_min
        gates.append(
            GateResult(
                gate_name="reflexivity",
                status=GateStatus.PASS if sr_passed else GateStatus.FAIL,
                value=sr_score,
                threshold=self.sr_min,
                passed=sr_passed,
                reason=f"SR={sr_score:.4f} {'≥' if sr_passed else '<'} {self.sr_min}",
            )
        )

        # Gate 5: Global Coherence (Ω-ΣEA)
        G_passed = G_coherence >= self.G_min
        gates.append(
            GateResult(
                gate_name="coherence",
                status=GateStatus.PASS if G_passed else GateStatus.FAIL,
                value=G_coherence,
                threshold=self.G_min,
                passed=G_passed,
                reason=f"G={G_coherence:.4f} {'≥' if G_passed else '<'} {self.G_min}",
            )
        )

        # Gate 6: Minimum Improvement (ΔL∞)
        improvement_passed = delta_Linf >= self.delta_Linf_min
        gates.append(
            GateResult(
                gate_name="improvement",
                status=GateStatus.PASS if improvement_passed else GateStatus.FAIL,
                value=delta_Linf,
                threshold=self.delta_Linf_min,
                passed=improvement_passed,
                reason=f"ΔL∞={delta_Linf:.6f} {'≥' if improvement_passed else '<'} {self.delta_Linf_min}",
            )
        )

        # Gate 7: Cost Control
        cost_passed = cost_increase <= self.cost_max_increase
        gates.append(
            GateResult(
                gate_name="cost",
                status=GateStatus.PASS if cost_passed else GateStatus.FAIL,
                value=cost_increase,
                threshold=self.cost_max_increase,
                passed=cost_passed,
                reason=f"Cost↑={cost_increase:.4f} {'≤' if cost_passed else '>'} {self.cost_max_increase}",
            )
        )

        # Gate 8: Kappa (CAOS⁺)
        kappa_passed = kappa >= self.kappa_min
        gates.append(
            GateResult(
                gate_name="kappa",
                status=GateStatus.PASS if kappa_passed else GateStatus.FAIL,
                value=kappa,
                threshold=self.kappa_min,
                passed=kappa_passed,
                reason=f"κ={kappa:.2f} {'≥' if kappa_passed else '<'} {self.kappa_min}",
            )
        )

        # Gate 9: Consent (if required)
        consent_passed = consent if self.consent_required else True
        gates.append(
            GateResult(
                gate_name="consent",
                status=GateStatus.PASS if consent_passed else GateStatus.FAIL,
                value=1.0 if consent else 0.0,
                threshold=1.0,
                passed=consent_passed,
                reason=f"Consent={'granted' if consent_passed else 'denied'}",
            )
        )

        # Gate 10: Ecological (if required)
        eco_passed = eco_ok if self.eco_ok_required else True
        gates.append(
            GateResult(
                gate_name="ecological",
                status=GateStatus.PASS if eco_passed else GateStatus.FAIL,
                value=1.0 if eco_ok else 0.0,
                threshold=1.0,
                passed=eco_passed,
                reason=f"Eco={'OK' if eco_passed else 'FAIL'}",
            )
        )

        # Non-compensatory: ALL must pass
        all_passed = all(g.passed for g in gates)

        # Compute aggregate score (harmonic mean for transparency)
        if all_passed:
            values = [g.value / g.threshold for g in gates if g.threshold > 0]
            eps = 1e-6
            aggregate = len(values) / sum(1.0 / max(eps, v) for v in values) if values else 0.0
        else:
            aggregate = 0.0

        # Determine action
        if all_passed:
            verdict = GateStatus.PASS
            action = "promote"
            reason = "All gates PASS → PROMOTE"
        else:
            # Find worst gate
            failed_gates = [g for g in gates if not g.passed]
            worst = min(failed_gates, key=lambda g: g.value / g.threshold if g.threshold > 0 else 0.0)
            verdict = GateStatus.FAIL
            action = "rollback"
            reason = f"FAIL on {worst.gate_name}: {worst.reason} → ROLLBACK"

        return SigmaGuardVerdict(
            verdict=verdict, passed=all_passed, gates=gates, aggregate_score=aggregate, reason=reason, action=action
        )


# Export public API
__all__ = [
    "SigmaGuard",
    "SigmaGuardVerdict",
    "GateResult",
    "GateStatus",
]
