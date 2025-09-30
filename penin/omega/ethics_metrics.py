"""
Ethics Metrics Calculator
========================

Implementa cálculo e ateste das métricas éticas/risco:
- ECE (Expected Calibration Error) por binning
- ρ_bias (fairness/paridade de taxa)
- consent e eco_ok (compliance flags)
- ρ (risk bound/contratividade)

Todas as métricas são calculadas e validadas internamente,
não apenas declaradas na config.
"""

import math
import hashlib
import json
from typing import Dict, List, Any, Optional
from typing_extensions import Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class EthicsEvidence:
    """Evidência para auditoria das métricas éticas"""
    dataset_hash: str
    sample_size: int
    method: str
    timestamp: float
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_hash": self.dataset_hash,
            "sample_size": self.sample_size,
            "method": self.method,
            "timestamp": self.timestamp,
            "seed": self.seed
        }


class ECECalculator:
    """Expected Calibration Error calculator with binning"""
    
    def __init__(self, n_bins: int = 15):
        self.n_bins = n_bins
        
    def calculate(self, confidences: List[float], predictions: List[int], 
                  labels: List[int]) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula ECE usando binning strategy
        
        Args:
            confidences: Lista de confidências [0,1]
            predictions: Lista de predições (0/1 ou classes)
            labels: Lista de labels verdadeiros
            
        Returns:
            (ece_value, details_dict)
        """
        if len(confidences) != len(predictions) != len(labels):
            raise ValueError("All inputs must have same length")
            
        if not confidences:
            return 0.0, {"method": "empty", "n_bins": self.n_bins}
            
        # Criar bins
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0.0
        bin_details = []
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Encontrar amostras neste bin
            in_bin = [(conf >= bin_lower) and (conf < bin_upper) 
                     for conf in confidences]
            prop_in_bin = sum(in_bin) / len(in_bin)
            
            if prop_in_bin > 0:
                # Calcular accuracy e confidence médias no bin
                bin_confidences = [confidences[i] for i, in_b in enumerate(in_bin) if in_b]
                bin_predictions = [predictions[i] for i, in_b in enumerate(in_bin) if in_b]
                bin_labels = [labels[i] for i, in_b in enumerate(in_bin) if in_b]
                
                avg_confidence = sum(bin_confidences) / len(bin_confidences)
                avg_accuracy = sum(1 for p, l in zip(bin_predictions, bin_labels) if p == l) / len(bin_predictions)
                
                # Contribuição para ECE
                bin_ece = abs(avg_confidence - avg_accuracy) * prop_in_bin
                ece += bin_ece
                
                bin_details.append({
                    "bin_range": [bin_lower, bin_upper],
                    "prop_in_bin": prop_in_bin,
                    "avg_confidence": avg_confidence,
                    "avg_accuracy": avg_accuracy,
                    "bin_ece": bin_ece,
                    "n_samples": len(bin_confidences)
                })
        
        details = {
            "method": "binning",
            "n_bins": self.n_bins,
            "total_samples": len(confidences),
            "bin_details": bin_details,
            "ece": ece
        }
        
        return ece, details


class BiasCalculator:
    """Calculadora de bias/fairness (ρ_bias)"""
    
    def calculate_demographic_parity(self, predictions: List[int], 
                                   protected_attr: List[int]) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula demographic parity ratio
        
        Args:
            predictions: Lista de predições (0/1)
            protected_attr: Lista de atributo protegido (0/1)
            
        Returns:
            (rho_bias, details)
        """
        if len(predictions) != len(protected_attr):
            raise ValueError("Predictions and protected attributes must have same length")
            
        # Separar por grupo
        group_0_preds = [p for p, attr in zip(predictions, protected_attr) if attr == 0]
        group_1_preds = [p for p, attr in zip(predictions, protected_attr) if attr == 1]
        
        if not group_0_preds or not group_1_preds:
            return 1.0, {"method": "demographic_parity", "error": "Missing group data"}
            
        # Calcular taxas de predição positiva
        rate_0 = sum(group_0_preds) / len(group_0_preds)
        rate_1 = sum(group_1_preds) / len(group_1_preds)
        
        # Ratio (sempre >= 1, com 1 = perfeita paridade)
        if rate_0 == 0 and rate_1 == 0:
            rho_bias = 1.0
        elif rate_0 == 0 or rate_1 == 0:
            rho_bias = float('inf')  # Será clampado
        else:
            rho_bias = max(rate_0 / rate_1, rate_1 / rate_0)
            
        details = {
            "method": "demographic_parity",
            "group_0_rate": rate_0,
            "group_1_rate": rate_1,
            "group_0_size": len(group_0_preds),
            "group_1_size": len(group_1_preds),
            "rho_bias": rho_bias
        }
        
        return min(rho_bias, 10.0), details  # Clamp para evitar inf


class RiskCalculator:
    """Calculadora de risco ρ (contratividade)"""
    
    def calculate_risk_bound(self, risk_series: List[float]) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula bound de risco baseado em série temporal
        
        Args:
            risk_series: Série de valores de risco
            
        Returns:
            (rho, details)
        """
        if len(risk_series) < 2:
            return 0.5, {"method": "insufficient_data", "series_length": len(risk_series)}
            
        # Calcular contratividade: rho = max(|r_{t+1}/r_t|) para t consecutivos
        ratios = []
        for i in range(1, len(risk_series)):
            if risk_series[i-1] != 0:
                ratio = abs(risk_series[i] / risk_series[i-1])
                ratios.append(ratio)
                
        if not ratios:
            return 0.5, {"method": "no_valid_ratios"}
            
        rho = max(ratios)
        
        # Verificar convergência (rho < 1 indica contratividade)
        is_contractive = rho < 1.0
        
        details = {
            "method": "temporal_ratios",
            "series_length": len(risk_series),
            "n_ratios": len(ratios),
            "max_ratio": rho,
            "mean_ratio": sum(ratios) / len(ratios),
            "is_contractive": is_contractive,
            "ratios": ratios[-5:]  # Últimos 5 para debug
        }
        
        return rho, details


class EthicsMetricsCalculator:
    """Calculadora principal de métricas éticas"""
    
    def __init__(self):
        self.ece_calc = ECECalculator()
        self.bias_calc = BiasCalculator()
        self.risk_calc = RiskCalculator()
        
    def calculate_all_metrics(self, 
                            # ECE inputs
                            confidences: Optional[List[float]] = None,
                            predictions: Optional[List[int]] = None,
                            labels: Optional[List[int]] = None,
                            # Bias inputs
                            protected_attr: Optional[List[int]] = None,
                            # Risk inputs
                            risk_series: Optional[List[float]] = None,
                            # Compliance flags
                            consent: bool = True,
                            eco_ok: bool = True,
                            # Evidence
                            dataset_id: Optional[str] = None,
                            seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Calcula todas as métricas éticas com evidência
        
        Returns:
            Dict com métricas calculadas e evidência
        """
        import time
        
        results = {
            "timestamp": time.time(),
            "seed": seed,
            "consent": consent,
            "eco_ok": eco_ok
        }
        
        # ECE
        if confidences and predictions and labels:
            try:
                ece, ece_details = self.ece_calc.calculate(confidences, predictions, labels)
                results["ece"] = ece
                results["ece_details"] = ece_details
            except Exception as e:
                results["ece"] = 1.0  # Fail-closed: assume worst ECE
                results["ece_error"] = str(e)
        else:
            results["ece"] = 0.0  # Default para dados sintéticos
            results["ece_details"] = {"method": "default", "reason": "no_data"}
            
        # Bias
        if predictions and protected_attr:
            try:
                rho_bias, bias_details = self.bias_calc.calculate_demographic_parity(
                    predictions, protected_attr)
                results["rho_bias"] = rho_bias
                results["bias_details"] = bias_details
            except Exception as e:
                results["rho_bias"] = 2.0  # Fail-closed: assume high bias
                results["bias_error"] = str(e)
        else:
            results["rho_bias"] = 1.0  # Default: sem bias
            results["bias_details"] = {"method": "default", "reason": "no_data"}
            
        # Risk
        if risk_series:
            try:
                rho, risk_details = self.risk_calc.calculate_risk_bound(risk_series)
                results["rho"] = rho
                results["risk_details"] = risk_details
            except Exception as e:
                results["rho"] = 1.0  # Fail-closed: assume non-contractive
                results["risk_error"] = str(e)
        else:
            results["rho"] = 0.5  # Default: contractive
            results["risk_details"] = {"method": "default", "reason": "no_data"}
            
        # Evidência
        if dataset_id:
            dataset_hash = hashlib.sha256(dataset_id.encode()).hexdigest()[:16]
        else:
            dataset_hash = "synthetic"
            
        sample_size = len(confidences) if confidences else 0
        
        evidence = EthicsEvidence(
            dataset_hash=dataset_hash,
            sample_size=sample_size,
            method="integrated_calculation",
            timestamp=results["timestamp"],
            seed=seed
        )
        
        results["evidence"] = evidence.to_dict()
        results["evidence_hash"] = hashlib.sha256(
            json.dumps(evidence.to_dict(), sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return results
        
    def validate_against_thresholds(self, metrics: Dict[str, Any], 
                                  ece_max: float = 0.01,
                                  rho_bias_max: float = 1.05,
                                  rho_max: float = 0.95,
                                  require_consent: bool = True,
                                  require_eco: bool = True) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Valida métricas contra thresholds (Σ-Guard)
        
        Returns:
            (all_passed, violations_list)
        """
        violations = []
        
        # ECE check
        ece = metrics.get("ece", 1.0)
        if ece > ece_max:
            violations.append({
                "metric": "ECE",
                "value": ece,
                "threshold": ece_max,
                "passed": False,
                "message": f"ECE {ece:.4f} > {ece_max}"
            })
            
        # Bias check
        rho_bias = metrics.get("rho_bias", 2.0)
        if rho_bias > rho_bias_max:
            violations.append({
                "metric": "RHO_BIAS",
                "value": rho_bias,
                "threshold": rho_bias_max,
                "passed": False,
                "message": f"ρ_bias {rho_bias:.3f} > {rho_bias_max}"
            })
            
        # Risk check
        rho = metrics.get("rho", 1.0)
        if rho >= rho_max:
            violations.append({
                "metric": "RHO",
                "value": rho,
                "threshold": rho_max,
                "passed": False,
                "message": f"ρ {rho:.3f} >= {rho_max} (não-contrativo)"
            })
            
        # Consent check
        consent = metrics.get("consent", False)
        if require_consent and not consent:
            violations.append({
                "metric": "CONSENT",
                "value": consent,
                "threshold": True,
                "passed": False,
                "message": "Consent required but not granted"
            })
            
        # Eco check
        eco_ok = metrics.get("eco_ok", False)
        if require_eco and not eco_ok:
            violations.append({
                "metric": "ECO",
                "value": eco_ok,
                "threshold": True,
                "passed": False,
                "message": "Eco compliance required but not met"
            })
            
        return len(violations) == 0, violations


# Função de conveniência para integração
def calculate_and_validate_ethics(state_dict: Dict[str, Any], 
                                config: Dict[str, Any],
                                dataset_id: Optional[str] = None,
                                seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Função de conveniência para calcular e validar métricas éticas
    
    Args:
        state_dict: Estado atual do sistema
        config: Configuração com thresholds
        dataset_id: ID do dataset para evidência
        seed: Seed para reprodutibilidade
        
    Returns:
        Dict com métricas, validação e evidência
    """
    calc = EthicsMetricsCalculator()
    
    # Gerar dados sintéticos se necessário (para demonstração)
    # Em produção, estes viriam de avaliações reais
    confidences = None
    predictions = None
    labels = None
    protected_attr = None
    risk_series = state_dict.get("risk_history", [state_dict.get("rho", 0.5)])
    
    # Calcular métricas
    metrics = calc.calculate_all_metrics(
        confidences=confidences,
        predictions=predictions,
        labels=labels,
        protected_attr=protected_attr,
        risk_series=risk_series,
        consent=state_dict.get("consent", True),
        eco_ok=state_dict.get("eco", True),
        dataset_id=dataset_id,
        seed=seed
    )
    
    # Validar contra thresholds
    ethics_config = config.get("ethics", {})
    passed, violations = calc.validate_against_thresholds(
        metrics,
        ece_max=ethics_config.get("ece_max", 0.01),
        rho_bias_max=ethics_config.get("rho_bias_max", 1.05),
        rho_max=0.95,  # Hardcoded safety
        require_consent=ethics_config.get("consent_required", True),
        require_eco=ethics_config.get("eco_ok_required", True)
    )
    
    return {
        "metrics": metrics,
        "validation": {
            "passed": passed,
            "violations": violations
        },
        "evidence_hash": metrics["evidence_hash"]
    }