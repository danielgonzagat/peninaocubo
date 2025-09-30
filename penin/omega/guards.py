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
from typing import Dict, Any, List, Optional
from typing_extensions import Tuple
from dataclasses import dataclass
from enum import Enum

# Import do módulo de métricas éticas
from .ethics_metrics import EthicsCalculator, EthicsMetrics


class GuardResult(Enum):
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guard": self.guard_name,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "severity": self.severity
        }


class SigmaGuard:
    """
    Σ-Guard: Verificação ética e de segurança
    
    Verifica:
    - ECE ≤ threshold (calibração)
    - ρ_bias ≤ threshold (fairness)
    - consent == True (consentimento)
    - eco_ok == True (compliance ambiental)
    """
    
    def __init__(self,
                 ece_max: float = 0.01,
                 rho_bias_max: float = 1.05,
                 require_consent: bool = True,
                 require_eco: bool = True):
        """
        Args:
            ece_max: Threshold máximo para ECE
            rho_bias_max: Threshold máximo para bias ratio
            require_consent: Se consent é obrigatório
            require_eco: Se eco compliance é obrigatório
        """
        self.ece_max = ece_max
        self.rho_bias_max = rho_bias_max
        self.require_consent = require_consent
        self.require_eco = require_eco
        self.ethics_calc = EthicsCalculator()
        
    def check(self, 
              state_dict: Dict[str, Any],
              dataset_id: Optional[str] = None,
              seed: Optional[int] = None) -> Tuple[GuardResult, List[GuardViolation], Dict[str, Any]]:
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
            config = {
                "ethics": {
                    "ece_max": self.ece_max,
                    "rho_bias_max": self.rho_bias_max,
                    "consent_required": self.require_consent,
                    "eco_ok_required": self.require_eco
                }
            }
            
            ethics_result = calculate_and_validate_ethics(
                state_dict, config, dataset_id, seed
            )
            
            metrics = ethics_result["metrics"]
            validation = ethics_result["validation"]
            
            # Processar violações da validação
            for violation in validation["violations"]:
                guard_violation = GuardViolation(
                    guard_name="SIGMA_GUARD",
                    metric=violation["metric"],
                    value=violation["value"],
                    threshold=violation["threshold"],
                    message=violation["message"],
                    severity="high"
                )
                violations.append(guard_violation)
                
            # Determinar resultado
            if validation["passed"]:
                result = GuardResult.PASS
            else:
                result = GuardResult.FAIL
                
            evidence = {
                "guard": "SIGMA_GUARD",
                "timestamp": time.time(),
                "metrics": metrics,
                "validation": validation,
                "evidence_hash": ethics_result["evidence_hash"],
                "config": {
                    "ece_max": self.ece_max,
                    "rho_bias_max": self.rho_bias_max,
                    "require_consent": self.require_consent,
                    "require_eco": self.require_eco
                }
            }
            
        except Exception as e:
            # Fail-closed: erro vira falha
            violation = GuardViolation(
                guard_name="SIGMA_GUARD",
                metric="SYSTEM_ERROR",
                value=str(e),
                threshold="NO_ERROR",
                message=f"Σ-Guard system error: {e}",
                severity="high"
            )
            violations.append(violation)
            result = GuardResult.ERROR
            
            evidence = {
                "guard": "SIGMA_GUARD",
                "timestamp": time.time(),
                "error": str(e),
                "result": "ERROR"
            }
            
        return result, violations, evidence
        
    def update_thresholds(self, 
                         ece_max: Optional[float] = None,
                         rho_bias_max: Optional[float] = None,
                         require_consent: Optional[bool] = None,
                         require_eco: Optional[bool] = None) -> None:
        """Atualiza thresholds do guard"""
        if ece_max is not None:
            self.ece_max = ece_max
        if rho_bias_max is not None:
            self.rho_bias_max = rho_bias_max
        if require_consent is not None:
            self.require_consent = require_consent
        if require_eco is not None:
            self.require_eco = require_eco
            
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "ece_max": self.ece_max,
            "rho_bias_max": self.rho_bias_max,
            "require_consent": self.require_consent,
            "require_eco": self.require_eco
        }


class IRtoICGuard:
    """
    IR→IC Guard: Verificação de contratividade de risco
    
    Verifica se ρ < 1 (sistema contrativo/convergente)
    """
    
    def __init__(self,
                 rho_max: float = 0.95,
                 min_history_length: int = 2,
                 contraction_factor: float = 0.98):
        """
        Args:
            rho_max: Threshold máximo para ρ
            min_history_length: Mínimo de pontos para análise
            contraction_factor: Fator de contração esperado
        """
        self.rho_max = rho_max
        self.min_history = min_history_length
        self.contraction_factor = contraction_factor
        
    def check_contractive(self, 
                         risk_series: List[float]) -> Tuple[GuardResult, List[GuardViolation], Dict[str, Any]]:
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
                    severity="medium"
                )
                violations.append(violation)
                
                analysis = {
                    "guard": "IR_TO_IC",
                    "result": "INSUFFICIENT_DATA",
                    "series_length": len(risk_series),
                    "min_required": self.min_history
                }
                
                return GuardResult.FAIL, violations, analysis
                
            # Calcular ratios consecutivos
            ratios = []
            for i in range(1, len(risk_series)):
                if risk_series[i-1] != 0:
                    ratio = abs(risk_series[i] / risk_series[i-1])
                    ratios.append(ratio)
                    
            if not ratios:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="VALID_RATIOS",
                    value=0,
                    threshold=1,
                    message="No valid risk ratios found (division by zero)",
                    severity="high"
                )
                violations.append(violation)
                
                return GuardResult.ERROR, violations, {"error": "no_valid_ratios"}
                
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
                    severity="high"
                )
                violations.append(violation)
                
            if not is_contractive:
                violation = GuardViolation(
                    guard_name="IR_TO_IC",
                    metric="CONTRACTIVE",
                    value=max_ratio,
                    threshold=1.0,
                    message=f"System not contractive: max ρ={max_ratio:.3f} ≥ 1.0",
                    severity="high"
                )
                violations.append(violation)
                
            # Resultado
            if meets_threshold and is_contractive:
                result = GuardResult.PASS
            else:
                result = GuardResult.FAIL
                
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
                    "contraction_factor": self.contraction_factor
                }
            }
            
        except Exception as e:
            # Fail-closed
            violation = GuardViolation(
                guard_name="IR_TO_IC",
                metric="SYSTEM_ERROR",
                value=str(e),
                threshold="NO_ERROR",
                message=f"IR→IC system error: {e}",
                severity="high"
            )
            violations.append(violation)
            result = GuardResult.ERROR
            
            analysis = {
                "guard": "IR_TO_IC",
                "error": str(e),
                "result": "ERROR"
            }
            
        return result, violations, analysis
        
    def apply_contraction(self, current_risk: float) -> float:
        """Aplica fator de contração ao risco atual"""
        return current_risk * self.contraction_factor
        
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "rho_max": self.rho_max,
            "min_history": self.min_history,
            "contraction_factor": self.contraction_factor
        }


class GuardOrchestrator:
    """
    Orquestrador de todos os guards
    
    Executa Σ-Guard e IR→IC em sequência, fail-closed
    """
    
    def __init__(self,
                 sigma_guard: Optional[SigmaGuard] = None,
                 iric_guard: Optional[IRtoICGuard] = None):
        """
        Args:
            sigma_guard: Instância do Σ-Guard (default: padrão)
            iric_guard: Instância do IR→IC Guard (default: padrão)
        """
        self.sigma_guard = sigma_guard or SigmaGuard()
        self.iric_guard = iric_guard or IRtoICGuard()
        
    def check_all_guards(self,
                        state_dict: Dict[str, Any],
                        risk_series: Optional[List[float]] = None,
                        dataset_id: Optional[str] = None,
                        seed: Optional[int] = None) -> Tuple[bool, List[GuardViolation], Dict[str, Any]]:
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
            "overall_result": None
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
            
        iric_result, iric_violations, iric_evidence = self.iric_guard.check_contractive(risk_series)
        
        all_violations.extend(iric_violations)
        evidence["iric_guard"] = iric_evidence
        evidence["guards_executed"].append("IR_TO_IC")
        
        # Resultado combinado (fail-closed)
        all_passed = (sigma_result == GuardResult.PASS and 
                     iric_result == GuardResult.PASS)
        
        evidence["overall_result"] = "PASS" if all_passed else "FAIL"
        evidence["sigma_result"] = sigma_result.value
        evidence["iric_result"] = iric_result.value
        evidence["total_violations"] = len(all_violations)
        
        return all_passed, all_violations, evidence
        
    def get_guard_summary(self) -> Dict[str, Any]:
        """Retorna resumo de configuração dos guards"""
        return {
            "sigma_guard": self.sigma_guard.get_config(),
            "iric_guard": self.iric_guard.get_config(),
            "orchestrator": {
                "fail_closed": True,
                "guards_count": 2
            }
        }


# Funções de conveniência
def quick_sigma_guard_check(state_dict: Dict[str, Any],
                           ece_max: float = 0.01,
                           rho_bias_max: float = 1.05) -> Tuple[bool, List[str]]:
    """Verificação rápida do Σ-Guard"""
    guard = SigmaGuard(ece_max=ece_max, rho_bias_max=rho_bias_max)
    result, violations, _ = guard.check(state_dict)
    
    passed = result == GuardResult.PASS
    messages = [v.message for v in violations]
    
    return passed, messages


def quick_iric_check(risk_series: List[float],
                    rho_max: float = 0.95) -> Tuple[bool, float]:
    """Verificação rápida do IR→IC"""
    guard = IRtoICGuard(rho_max=rho_max)
    result, violations, analysis = guard.check_contractive(risk_series)
    
    passed = result == GuardResult.PASS
    max_ratio = analysis.get("max_ratio", 1.0)
    
    return passed, max_ratio


def full_guard_check(state_dict: Dict[str, Any],
                    risk_series: Optional[List[float]] = None) -> Dict[str, Any]:
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
        "summary": orchestrator.get_guard_summary()
    }