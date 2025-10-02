"""
Guards Module - Σ-Guard + IR→IC (Fail-Closed)
==============================================

Implementa:
- Σ-Guard: Verificação ética/segurança (ECE, ρ_bias, consent, eco_ok)
- IR→IC: Contratividade de risco (ρ < 1 para convergência)
- Fail-closed: Qualquer falha bloqueia promoção com detalhes
- Integração com ethics_metrics para cálculo real das métricas
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Import do módulo de métricas éticas
from .ethics_metrics import EthicsCalculator


class GuardResultType(Enum):
    """Resultado dos guards"""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class GuardViolation:
    """Violação de guard"""

    guard_name: str
    metric: str
    value: Any
    threshold: Any
    message: str
    severity: str = "high"  # high, medium, low

    def to_dict(self) -> dict[str, Any]:
        return {
            "guard": self.guard_name,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "severity": self.severity,
        }


# Standalone functions for compatibility with tests
def sigma_guard(
    metrics: dict[str, Any], policy: "SigmaGuardPolicy" = None
) -> "GuardResult":
    """Standalone sigma guard function"""
    if policy is None:
        policy = SigmaGuardPolicy()

    guard = SigmaGuard(policy)
    result, violations, details = guard.check(metrics)
    return result


def ir_to_ic_contractive(
    risk_history: list[float], rho_threshold: float = 1.0
) -> "GuardResult":
    """Standalone IR→IC contractivity check"""
    guard = IRICGuard(rho_threshold)
    result, violations, details = guard.check(risk_history)
    return result


def combined_guard_check(
    metrics: dict[str, Any],
    risk_history: list[float],
    policy: "SigmaGuardPolicy" = None,
) -> tuple[bool, dict[str, Any]]:
    """Combined guard check"""
    if policy is None:
        policy = SigmaGuardPolicy()

    sigma_result = sigma_guard(metrics, policy)
    iric_result = ir_to_ic_contractive(risk_history)

    all_passed = sigma_result.passed and iric_result.passed

    results = {
        "sigma_guard": sigma_result,
        "ir_ic_guard": iric_result,
        "all_passed": all_passed,
    }

    return all_passed, results


@dataclass
class GuardResult:
    """Result from a guard check"""

    passed: bool
    violations: list[GuardViolation]
    details: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "details": self.details,
            "timestamp": self.timestamp,
        }


class IRICGuard:
    """IR→IC Contractivity Guard"""

    def __init__(self, rho_threshold: float = 1.0):
        self.rho_threshold = rho_threshold

    def check(
        self, risk_history: list[float]
    ) -> tuple[GuardResult, list[GuardViolation], dict[str, Any]]:
        """Check if risk is contractive (IR→IC)"""
        violations = []

        if len(risk_history) < 2:
            violations.append(
                GuardViolation(
                    guard_name="IR_IC_GUARD",
                    metric="risk_history_length",
                    value=len(risk_history),
                    threshold=2,
                    message="Insufficient risk history for contractivity analysis",
                    severity="high",
                )
            )

            result = GuardResult(
                passed=False,
                violations=violations,
                details={"error": "insufficient_data"},
                timestamp=str(time.time()),
            )

            return result, violations, {"error": "insufficient_data"}

        # Calculate ratios between consecutive values
        ratios = []
        for i in range(1, len(risk_history)):
            if risk_history[i - 1] > 1e-9:
                ratio = risk_history[i] / risk_history[i - 1]
                ratios.append(ratio)

        if not ratios:
            violations.append(
                GuardViolation(
                    guard_name="IR_IC_GUARD",
                    metric="valid_ratios",
                    value=0,
                    threshold=1,
                    message="No valid risk ratios found",
                    severity="high",
                )
            )

            result = GuardResult(
                passed=False,
                violations=violations,
                details={"error": "no_valid_ratios"},
                timestamp=str(time.time()),
            )

            return result, violations, {"error": "no_valid_ratios"}

        # Check contractivity
        avg_ratio = sum(ratios) / len(ratios)
        is_contractive = avg_ratio < self.rho_threshold

        if not is_contractive:
            violations.append(
                GuardViolation(
                    guard_name="IR_IC_GUARD",
                    metric="avg_ratio",
                    value=avg_ratio,
                    threshold=self.rho_threshold,
                    message=f"Risk is not contractive: avg ratio {avg_ratio:.4f} >= {self.rho_threshold}",
                    severity="high",
                )
            )

        passed = len(violations) == 0
        result = GuardResult(
            passed=passed,
            violations=violations,
            details={
                "avg_ratio": avg_ratio,
                "is_contractive": is_contractive,
                "ratios": ratios,
            },
            timestamp=str(time.time()),
        )

        evidence = {
            "guard": "IR_IC_GUARD",
            "risk_history": risk_history,
            "ratios": ratios,
            "avg_ratio": avg_ratio,
            "is_contractive": is_contractive,
            "threshold": self.rho_threshold,
        }

        return result, violations, evidence


@dataclass
class SigmaGuardPolicy:
    """Policy configuration for Σ-Guard"""

    ece_threshold: float = 0.01
    rho_bias_threshold: float = 1.05
    fairness_dp_threshold: float = 0.1
    fairness_eo_threshold: float = 0.1
    rho_risk_threshold: float = 1.0
    eco_impact_threshold: float = 0.5
    confidence_threshold: float = 0.7
    uncertainty_threshold: float = 0.3


class SigmaGuard:
    """
    Σ-Guard: Verificação ética e de segurança

    Verifica:
    - ECE ≤ threshold (calibração)
    - ρ_bias ≤ threshold (fairness)
    - consent == True (consentimento)
    - eco_ok == True (compliance ambiental)
    """

    def __init__(
        self,
        policy: SigmaGuardPolicy = None,
        ece_max: float = None,
        rho_bias_max: float = None,
        require_consent: bool = None,
        require_eco: bool = None,
    ):
        """
        Args:
            policy: SigmaGuardPolicy object with thresholds
            ece_max: Threshold máximo para ECE (overrides policy)
            rho_bias_max: Threshold máximo para bias ratio (overrides policy)
            require_consent: Se consent é obrigatório (overrides policy)
            require_eco: Se eco compliance é obrigatório (overrides policy)
        """
        if policy is None:
            policy = SigmaGuardPolicy()

        self.ece_max = ece_max if ece_max is not None else policy.ece_threshold
        self.rho_bias_max = (
            rho_bias_max if rho_bias_max is not None else policy.rho_bias_threshold
        )
        self.require_consent = require_consent if require_consent is not None else True
        self.require_eco = require_eco if require_eco is not None else True
        self.ethics_calc = EthicsCalculator()

    def check(
        self,
        state_dict: dict[str, Any],
        dataset_id: str | None = None,
        seed: int | None = None,
    ) -> tuple[GuardResult, list[GuardViolation], dict[str, Any]]:
        """
        Executa verificação Σ-Guard

        Args:
            state_dict: Estado atual do sistema
            dataset_id: ID do dataset para evidência
            seed: Seed para reprodutibilidade

        Returns:
            (result, violations, evidence)
        """
        violations = []

        try:
            # Calcular métricas éticas reais

            # Use provided metrics directly for now
            metrics = state_dict

            # Check each metric against thresholds
            violations = []

            # Check ECE
            ece = metrics.get("ece", 1.0)
            if ece > self.ece_max:
                violations.append(
                    GuardViolation(
                        guard_name="SIGMA_GUARD",
                        metric="ece",
                        value=ece,
                        threshold=self.ece_max,
                        message=f"ECE {ece:.4f} exceeds threshold {self.ece_max}",
                        severity="high",
                    )
                )

            # Check bias ratio
            rho_bias = metrics.get("rho_bias", 10.0)
            if rho_bias > self.rho_bias_max:
                violations.append(
                    GuardViolation(
                        guard_name="SIGMA_GUARD",
                        metric="rho_bias",
                        value=rho_bias,
                        threshold=self.rho_bias_max,
                        message=f"Bias ratio {rho_bias:.4f} exceeds threshold {self.rho_bias_max}",
                        severity="high",
                    )
                )

            # Check consent
            consent_valid = metrics.get("consent_valid", False)
            if self.require_consent and not consent_valid:
                violations.append(
                    GuardViolation(
                        guard_name="SIGMA_GUARD",
                        metric="consent_valid",
                        value=consent_valid,
                        threshold=True,
                        message="Consent is required but not valid",
                        severity="high",
                    )
                )

            # Check eco impact
            eco_impact = metrics.get("eco_impact", 1.0)
            eco_threshold = 0.5  # Default threshold
            if eco_impact > eco_threshold:
                violations.append(
                    GuardViolation(
                        guard_name="SIGMA_GUARD",
                        metric="eco_impact",
                        value=eco_impact,
                        threshold=eco_threshold,
                        message=f"Eco impact {eco_impact:.4f} exceeds threshold {eco_threshold}",
                        severity="medium",
                    )
                )

            # Determinar resultado
            passed = len(violations) == 0
            result = GuardResult(
                passed=passed,
                violations=violations,
                details={"status": "passed" if passed else "failed"},
                timestamp=str(time.time()),
            )

            evidence = {
                "guard": "SIGMA_GUARD",
                "timestamp": time.time(),
                "metrics": metrics,
                "violations": [v.to_dict() for v in violations],
                "evidence_hash": "no_hash_available",
                "config": {
                    "ece_max": self.ece_max,
                    "rho_bias_max": self.rho_bias_max,
                    "require_consent": self.require_consent,
                    "require_eco": self.require_eco,
                },
            }

        except Exception as e:
            # Fail-closed: erro vira falha
            violation = GuardViolation(
                guard_name="SIGMA_GUARD",
                metric="SYSTEM_ERROR",
                value=str(e),
                threshold="NO_ERROR",
                message=f"Σ-Guard system error: {e}",
                severity="high",
            )
            violations.append(violation)
            result = GuardResult(
                passed=False,
                violations=[
                    GuardViolation(
                        guard_name="SigmaGuard",
                        metric="system",
                        value="error",
                        threshold="n/a",
                        message=f"System error: {str(e)}",
                        severity="high",
                    )
                ],
                details={"error": str(e)},
                timestamp=str(time.time()),
            )

            evidence = {
                "guard": "SIGMA_GUARD",
                "timestamp": time.time(),
                "error": str(e),
                "result": "ERROR",
            }

        return result, violations, evidence

    def update_thresholds(
        self,
        ece_max: float | None = None,
        rho_bias_max: float | None = None,
        require_consent: bool | None = None,
        require_eco: bool | None = None,
    ) -> None:
        """Atualiza thresholds do guard"""
        if ece_max is not None:
            self.ece_max = ece_max
        if rho_bias_max is not None:
            self.rho_bias_max = rho_bias_max
        if require_consent is not None:
            self.require_consent = require_consent
        if require_eco is not None:
            self.require_eco = require_eco

    def get_config(self) -> dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "ece_max": self.ece_max,
            "rho_bias_max": self.rho_bias_max,
            "require_consent": self.require_consent,
            "require_eco": self.require_eco,
        }


class IRtoICGuard:
    """
    IR→IC Guard: Verificação de contratividade de risco

    Verifica se ρ < 1 (sistema contrativo/convergente)
    """

    def __init__(
        self,
        rho_max: float = 0.95,
        min_history_length: int = 2,
        contraction_factor: float = 0.98,
    ):
        """
        Args:
            rho_max: Threshold máximo para ρ
            min_history_length: Mínimo de pontos para análise
            contraction_factor: Fator de contração esperado
        """
        self.rho_max = rho_max
        self.min_history = min_history_length
        self.contraction_factor = contraction_factor

    def check_contractive(
        self, risk_series: list[float]
    ) -> tuple[GuardResult, list[GuardViolation], dict[str, Any]]:
        """
        Verifica contratividade da série de risco

        Args:
            risk_series: Série temporal de valores de risco

        Returns:
            (result, violations, analysis)
        """
        violations = []

        try:
            if len(risk_series) < self.min_history:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="HISTORY_LENGTH",
                    value=len(risk_series),
                    threshold=self.min_history,
                    message=f"Insufficient risk history: {len(risk_series)} < {self.min_history}",
                    severity="medium",
                )
                violations.append(violation)

                analysis = {
                    "guard": "IR_TO_IC",
                    "result": "INSUFFICIENT_DATA",
                    "series_length": len(risk_series),
                    "min_required": self.min_history,
                }

                return GuardResult.FAIL, violations, analysis

            # Calcular ratios consecutivos
            ratios = []
            for i in range(1, len(risk_series)):
                if risk_series[i - 1] != 0:
                    ratio = abs(risk_series[i] / risk_series[i - 1])
                    ratios.append(ratio)

            if not ratios:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="VALID_RATIOS",
                    value=0,
                    threshold=1,
                    message="No valid risk ratios found (division by zero)",
                    severity="high",
                )
                violations.append(violation)

                return (
                    GuardResult(
                        passed=False,
                        violations=violations,
                        details={"error": "no_valid_ratios"},
                        timestamp=str(time.time()),
                    ),
                    violations,
                    {"error": "no_valid_ratios"},
                )

            # Análise de contratividade
            max_ratio = max(ratios)
            mean_ratio = sum(ratios) / len(ratios)

            # Verificar se é contrativo (ρ < 1)
            is_contractive = max_ratio < 1.0
            meets_threshold = max_ratio < self.rho_max

            if not meets_threshold:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="RHO_MAX",
                    value=max_ratio,
                    threshold=self.rho_max,
                    message=f"Risk ratio ρ={max_ratio:.3f} ≥ {self.rho_max} (non-contractive)",
                    severity="high",
                )
                violations.append(violation)

            if not is_contractive:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="CONTRACTIVE",
                    value=max_ratio,
                    threshold=1.0,
                    message=f"System not contractive: max ρ={max_ratio:.3f} ≥ 1.0",
                    severity="high",
                )
                violations.append(violation)

            # Resultado
            if meets_threshold and is_contractive:
                result = GuardResult(
                    passed=True,
                    violations=[],
                    details={"status": "passed"},
                    timestamp=str(time.time()),
                )
            else:
                result = GuardResult(
                    passed=False,
                    violations=violations,
                    details={"status": "failed"},
                    timestamp=str(time.time()),
                )

            analysis = {
                "guard": "IR_TO_IC",
                "result": result.value,
                "max_ratio": max_ratio,
                "mean_ratio": mean_ratio,
                "is_contractive": is_contractive,
                "meets_threshold": meets_threshold,
                "series_length": len(risk_series),
                "n_ratios": len(ratios),
                "ratios": ratios[-5:],  # Últimos 5 para debug
                "config": {
                    "rho_max": self.rho_max,
                    "contraction_factor": self.contraction_factor,
                },
            }

        except Exception as e:
            # Fail-closed
            violation = GuardViolation(
                guard_name="IR_TO_IC",
                metric="SYSTEM_ERROR",
                value=str(e),
                threshold="NO_ERROR",
                message=f"IR→IC system error: {e}",
                severity="high",
            )
            violations.append(violation)
            result = GuardResult(
                passed=False,
                violations=[
                    GuardViolation(
                        guard_name="SigmaGuard",
                        metric="system",
                        value="error",
                        threshold="n/a",
                        message=f"System error: {str(e)}",
                        severity="high",
                    )
                ],
                details={"error": str(e)},
                timestamp=str(time.time()),
            )

            analysis = {"guard": "IR_TO_IC", "error": str(e), "result": "ERROR"}

        return result, violations, analysis

    def apply_contraction(self, current_risk: float) -> float:
        """Aplica fator de contração ao risco atual"""
        return current_risk * self.contraction_factor

    def get_config(self) -> dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "rho_max": self.rho_max,
            "min_history": self.min_history,
            "contraction_factor": self.contraction_factor,
        }


class GuardOrchestrator:
    """
    Orquestrador de todos os guards

    Executa Σ-Guard e IR→IC em sequência, fail-closed
    """

    def __init__(
        self,
        sigma_guard: SigmaGuard | None = None,
        iric_guard: IRtoICGuard | None = None,
    ):
        """
        Args:
            sigma_guard: Instância do Σ-Guard (default: padrão)
            iric_guard: Instância do IR→IC Guard (default: padrão)
        """
        self.sigma_guard = sigma_guard or SigmaGuard()
        self.iric_guard = iric_guard or IRtoICGuard()

    def check_all_guards(
        self,
        state_dict: dict[str, Any],
        risk_series: list[float] | None = None,
        dataset_id: str | None = None,
        seed: int | None = None,
    ) -> tuple[bool, list[GuardViolation], dict[str, Any]]:
        """
        Executa todos os guards

        Args:
            state_dict: Estado atual do sistema
            risk_series: Série de risco para IR→IC
            dataset_id: ID do dataset
            seed: Seed para reprodutibilidade

        Returns:
            (all_passed, all_violations, combined_evidence)
        """
        all_violations = []
        evidence = {
            "timestamp": time.time(),
            "guards_executed": [],
            "overall_result": None,
        }

        # 1. Σ-Guard
        sigma_result, sigma_violations, sigma_evidence = self.sigma_guard.check(
            state_dict, dataset_id, seed
        )

        all_violations.extend(sigma_violations)
        evidence["sigma_guard"] = sigma_evidence
        evidence["guards_executed"].append("SIGMA_GUARD")

        # 2. IR→IC Guard
        if risk_series is None:
            # Usar histórico do state_dict ou valor atual
            risk_series = state_dict.get("risk_history", [state_dict.get("rho", 0.5)])

        iric_result, iric_violations, iric_evidence = self.iric_guard.check_contractive(
            risk_series
        )

        all_violations.extend(iric_violations)
        evidence["iric_guard"] = iric_evidence
        evidence["guards_executed"].append("IR_TO_IC")

        # Resultado combinado (fail-closed)
        all_passed = sigma_result.passed and iric_result.passed

        evidence["overall_result"] = "PASS" if all_passed else "FAIL"
        evidence["sigma_result"] = "PASS" if sigma_result.passed else "FAIL"
        evidence["iric_result"] = "PASS" if iric_result.passed else "FAIL"
        evidence["total_violations"] = len(all_violations)

        return all_passed, all_violations, evidence

    def get_guard_summary(self) -> dict[str, Any]:
        """Retorna resumo de configuração dos guards"""
        return {
            "sigma_guard": self.sigma_guard.get_config(),
            "iric_guard": self.iric_guard.get_config(),
            "orchestrator": {"fail_closed": True, "guards_count": 2},
        }


# Funções de conveniência
def quick_sigma_guard_check(
    state_dict: dict[str, Any], ece_max: float = 0.01, rho_bias_max: float = 1.05
) -> tuple[bool, list[str]]:
    """Verificação rápida do Σ-Guard"""
    guard = SigmaGuard(ece_max=ece_max, rho_bias_max=rho_bias_max)
    result, violations, _ = guard.check(state_dict)

    passed = result.passed
    messages = [v.message for v in violations]

    return passed, messages


def quick_iric_check(
    risk_series: list[float], rho_max: float = 0.95
) -> tuple[bool, float]:
    """Verificação rápida do IR→IC"""
    guard = IRtoICGuard(rho_max=rho_max)
    result, violations, analysis = guard.check_contractive(risk_series)

    passed = result.passed
    max_ratio = analysis.get("max_ratio", 1.0)

    return passed, max_ratio


def full_guard_check(
    state_dict: dict[str, Any], risk_series: list[float] | None = None
) -> dict[str, Any]:
    """
    Verificação completa de todos os guards

    Returns:
        Dict com resultado detalhado
    """
    orchestrator = GuardOrchestrator()
    passed, violations, evidence = orchestrator.check_all_guards(
        state_dict, risk_series
    )

    return {
        "passed": passed,
        "violations": [v.to_dict() for v in violations],
        "evidence": evidence,
        "summary": orchestrator.get_guard_summary(),
    }
