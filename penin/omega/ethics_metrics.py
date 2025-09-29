"""
Ethics Metrics — Real Calculation & Attestation
================================================

P0 Correction: Implementação real dos cálculos de ECE, ρ_bias, fairness,
consent com evidência registrada no WORM.

Métricas implementadas:
- ECE (Expected Calibration Error): calibração de probabilidades
- ρ_bias: viés demográfico/paridade de taxa
- fairness: paridade de erro entre grupos
- consent: validação de opt-in/privacidade
"""

from __future__ import annotations
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object


# ============================================================================
# Schema de atestado ético
# ============================================================================

if HAS_PYDANTIC:
    class EthicsAttestation(BaseModel):
        """Registro imutável de medição ética para WORM."""
        timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        cycle_id: str
        seed: int
        dataset_hash: str  # SHA256 do dataset usado
        
        # Métricas medidas
        ece: float = Field(ge=0.0, le=1.0)
        rho_bias: float = Field(ge=1.0)  # ≥1.0 (1.0 = sem viés)
        fairness_score: float = Field(ge=0.0, le=1.0)
        consent_valid: bool
        
        # Limites esperados (da config)
        ece_threshold: float = 0.01
        rho_bias_threshold: float = 1.05
        fairness_threshold: float = 0.95
        
        # Veredicto
        passes_gates: bool
        evidence: Dict[str, Any] = Field(default_factory=dict)
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                "timestamp": self.timestamp,
                "cycle_id": self.cycle_id,
                "seed": self.seed,
                "dataset_hash": self.dataset_hash,
                "ece": self.ece,
                "rho_bias": self.rho_bias,
                "fairness_score": self.fairness_score,
                "consent_valid": self.consent_valid,
                "ece_threshold": self.ece_threshold,
                "rho_bias_threshold": self.rho_bias_threshold,
                "fairness_threshold": self.fairness_threshold,
                "passes_gates": self.passes_gates,
                "evidence": self.evidence
            }
else:
    @dataclass
    class EthicsAttestation:
        timestamp: str = ""
        cycle_id: str = ""
        seed: int = 0
        dataset_hash: str = ""
        ece: float = 0.0
        rho_bias: float = 1.0
        fairness_score: float = 1.0
        consent_valid: bool = False
        ece_threshold: float = 0.01
        rho_bias_threshold: float = 1.05
        fairness_threshold: float = 0.95
        passes_gates: bool = False
        evidence: Dict[str, Any] = field(default_factory=dict)
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
                "cycle_id": self.cycle_id,
                "seed": self.seed,
                "dataset_hash": self.dataset_hash,
                "ece": self.ece,
                "rho_bias": self.rho_bias,
                "fairness_score": self.fairness_score,
                "consent_valid": self.consent_valid,
                "ece_threshold": self.ece_threshold,
                "rho_bias_threshold": self.rho_bias_threshold,
                "fairness_threshold": self.fairness_threshold,
                "passes_gates": self.passes_gates,
                "evidence": self.evidence
            }


# ============================================================================
# ECE (Expected Calibration Error)
# ============================================================================

def calculate_ece(
    predictions: List[float],
    outcomes: List[bool],
    n_bins: int = 10,
    strategy: str = "uniform"
) -> Tuple[float, Dict[str, Any]]:
    """
    Calcula Expected Calibration Error.
    
    ECE mede se as probabilidades preditas correspondem às frequências observadas.
    Por exemplo, se o modelo diz "70% de chance", deve acertar ~70% das vezes.
    
    Args:
        predictions: Probabilidades preditas [0,1]
        outcomes: Resultados reais (True/False)
        n_bins: Número de bins para agrupamento
        strategy: 'uniform' ou 'quantile'
    
    Returns:
        (ece_score, evidence_dict)
    """
    if len(predictions) != len(outcomes):
        raise ValueError("predictions e outcomes devem ter mesmo tamanho")
    
    if len(predictions) == 0:
        return 0.0, {"n_samples": 0, "bins": []}
    
    # Criar bins
    if strategy == "uniform":
        bin_edges = [i / n_bins for i in range(n_bins + 1)]
    else:
        # Quantile-based bins
        import numpy as np
        bin_edges = np.quantile(predictions, [i / n_bins for i in range(n_bins + 1)]).tolist()
    
    bins_data = []
    total_samples = len(predictions)
    weighted_error = 0.0
    
    for i in range(n_bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1] if i < n_bins - 1 else 1.0 + 1e-9
        
        # Samples neste bin
        mask = [(lower <= p < upper) for p in predictions]
        bin_preds = [p for p, m in zip(predictions, mask) if m]
        bin_outcomes = [o for o, m in zip(outcomes, mask) if m]
        
        if not bin_preds:
            continue
        
        # Média de confiança e acurácia neste bin
        avg_confidence = sum(bin_preds) / len(bin_preds)
        avg_accuracy = sum(bin_outcomes) / len(bin_outcomes)
        bin_weight = len(bin_preds) / total_samples
        
        error = abs(avg_confidence - avg_accuracy)
        weighted_error += bin_weight * error
        
        bins_data.append({
            "range": [lower, upper],
            "n_samples": len(bin_preds),
            "avg_confidence": avg_confidence,
            "avg_accuracy": avg_accuracy,
            "error": error
        })
    
    evidence = {
        "n_samples": total_samples,
        "n_bins": n_bins,
        "strategy": strategy,
        "bins": bins_data
    }
    
    return weighted_error, evidence


# ============================================================================
# ρ_bias (Demographic Parity / Equalized Odds)
# ============================================================================

def calculate_rho_bias(
    predictions: List[bool],
    outcomes: List[bool],
    groups: List[str],
    protected_attrs: Optional[List[str]] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calcula ρ_bias como razão máxima de taxa de previsão positiva entre grupos.
    
    ρ = max_group(rate) / min_group(rate)
    
    ρ = 1.0 significa paridade perfeita.
    ρ > 1.05 indica viés demográfico acima do limiar.
    
    Args:
        predictions: Predições binárias
        outcomes: Resultados reais
        groups: Identificadores de grupo (ex: 'A', 'B')
        protected_attrs: Atributos protegidos (opcional, para evidência)
    
    Returns:
        (rho_bias, evidence_dict)
    """
    if not (len(predictions) == len(outcomes) == len(groups)):
        raise ValueError("Tamanhos inconsistentes entre predictions/outcomes/groups")
    
    # Agrupar por categoria
    group_stats = {}
    for pred, outcome, grp in zip(predictions, outcomes, groups):
        if grp not in group_stats:
            group_stats[grp] = {"positive": 0, "total": 0}
        group_stats[grp]["total"] += 1
        if pred:
            group_stats[grp]["positive"] += 1
    
    # Calcular taxas
    rates = {}
    for grp, stats in group_stats.items():
        if stats["total"] > 0:
            rates[grp] = stats["positive"] / stats["total"]
        else:
            rates[grp] = 0.0
    
    if not rates:
        return 1.0, {"groups": {}, "rho": 1.0}
    
    max_rate = max(rates.values())
    min_rate = min(rates.values())
    
    # Evitar divisão por zero: usar epsilon
    epsilon = 1e-6
    if min_rate < epsilon:
        min_rate = epsilon
    if max_rate < epsilon:
        max_rate = epsilon
    
    rho = max_rate / min_rate
    
    evidence = {
        "groups": {
            grp: {
                "rate": rates[grp],
                "positive": group_stats[grp]["positive"],
                "total": group_stats[grp]["total"]
            }
            for grp in group_stats
        },
        "max_rate": max_rate,
        "min_rate": min_rate,
        "rho": rho,
        "protected_attrs": protected_attrs or []
    }
    
    return rho, evidence


# ============================================================================
# Fairness (Equalized Error Rates)
# ============================================================================

def calculate_fairness(
    predictions: List[bool],
    outcomes: List[bool],
    groups: List[str]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calcula fairness como similaridade de taxas de erro entre grupos.
    
    Score = 1 - max_disparity, onde disparity é a diferença máxima de taxa de erro.
    
    Args:
        predictions: Predições binárias
        outcomes: Resultados reais
        groups: Identificadores de grupo
    
    Returns:
        (fairness_score, evidence_dict)
    """
    if not (len(predictions) == len(outcomes) == len(groups)):
        raise ValueError("Tamanhos inconsistentes")
    
    # Calcular taxa de erro por grupo
    group_errors = {}
    for pred, outcome, grp in zip(predictions, outcomes, groups):
        if grp not in group_errors:
            group_errors[grp] = {"errors": 0, "total": 0}
        group_errors[grp]["total"] += 1
        if pred != outcome:
            group_errors[grp]["errors"] += 1
    
    error_rates = {}
    for grp, stats in group_errors.items():
        if stats["total"] > 0:
            error_rates[grp] = stats["errors"] / stats["total"]
        else:
            error_rates[grp] = 0.0
    
    if not error_rates:
        return 1.0, {"groups": {}, "fairness_score": 1.0}
    
    max_err = max(error_rates.values())
    min_err = min(error_rates.values())
    disparity = max_err - min_err
    
    fairness_score = 1.0 - disparity
    
    evidence = {
        "groups": {
            grp: {
                "error_rate": error_rates[grp],
                "errors": group_errors[grp]["errors"],
                "total": group_errors[grp]["total"]
            }
            for grp in group_errors
        },
        "max_error_rate": max_err,
        "min_error_rate": min_err,
        "disparity": disparity,
        "fairness_score": fairness_score
    }
    
    return fairness_score, evidence


# ============================================================================
# Consent Validation
# ============================================================================

def validate_consent(
    dataset_metadata: Dict[str, Any],
    required_flags: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Valida que dados foram coletados com consentimento apropriado.
    
    Args:
        dataset_metadata: Metadados do dataset (deve conter flags de consentimento)
        required_flags: Flags obrigatórias (ex: ['user_consent', 'gdpr_compliant'])
    
    Returns:
        (valid, evidence_dict)
    """
    if required_flags is None:
        required_flags = ['user_consent', 'privacy_policy_accepted']
    
    consent_status = {}
    all_valid = True
    
    for flag in required_flags:
        present = flag in dataset_metadata
        value = dataset_metadata.get(flag, False)
        consent_status[flag] = {"present": present, "value": value}
        
        if not (present and value):
            all_valid = False
    
    evidence = {
        "required_flags": required_flags,
        "consent_status": consent_status,
        "valid": all_valid,
        "dataset_id": dataset_metadata.get("id", "unknown")
    }
    
    return all_valid, evidence


# ============================================================================
# Atestado completo
# ============================================================================

def create_ethics_attestation(
    cycle_id: str,
    seed: int,
    dataset: Dict[str, Any],
    predictions: List[float],
    outcomes: List[bool],
    groups: List[str],
    config: Optional[Dict[str, float]] = None
) -> EthicsAttestation:
    """
    Cria atestado ético completo com todas as métricas.
    
    Args:
        cycle_id: ID do ciclo de evolução
        seed: Seed para reprodutibilidade
        dataset: Metadados do dataset
        predictions: Probabilidades preditas
        outcomes: Resultados reais
        groups: Grupos demográficos
        config: Limites configurados (opcional)
    
    Returns:
        EthicsAttestation completo
    """
    cfg = config or {}
    
    # Hash do dataset para rastreabilidade
    dataset_str = str(sorted(dataset.items()))
    dataset_hash = hashlib.sha256(dataset_str.encode()).hexdigest()
    
    # Calcular métricas
    ece, ece_evidence = calculate_ece(predictions, outcomes)
    
    binary_preds = [p >= 0.5 for p in predictions]
    rho_bias, rho_evidence = calculate_rho_bias(binary_preds, outcomes, groups)
    fairness_score, fairness_evidence = calculate_fairness(binary_preds, outcomes, groups)
    consent_valid, consent_evidence = validate_consent(dataset)
    
    # Verificar gates
    ece_ok = ece <= cfg.get("ece_threshold", 0.01)
    rho_ok = rho_bias <= cfg.get("rho_bias_threshold", 1.05)
    fairness_ok = fairness_score >= cfg.get("fairness_threshold", 0.95)
    
    passes_gates = ece_ok and rho_ok and fairness_ok and consent_valid
    
    attestation = EthicsAttestation(
        cycle_id=cycle_id,
        seed=seed,
        dataset_hash=dataset_hash,
        ece=ece,
        rho_bias=rho_bias,
        fairness_score=fairness_score,
        consent_valid=consent_valid,
        ece_threshold=cfg.get("ece_threshold", 0.01),
        rho_bias_threshold=cfg.get("rho_bias_threshold", 1.05),
        fairness_threshold=cfg.get("fairness_threshold", 0.95),
        passes_gates=passes_gates,
        evidence={
            "ece": ece_evidence,
            "rho_bias": rho_evidence,
            "fairness": fairness_evidence,
            "consent": consent_evidence
        }
    )
    
    return attestation


# ============================================================================
# Integração com WORM
# ============================================================================

def persist_attestation_to_worm(attestation: EthicsAttestation, ledger_path: str = "ledger_f3.jsonl") -> None:
    """
    Persiste atestado ético no WORM ledger.
    
    Args:
        attestation: Atestado a ser registrado
        ledger_path: Caminho do ledger JSONL
    """
    import json
    from pathlib import Path
    
    record = {
        "type": "ETHICS_ATTESTATION",
        "data": attestation.to_dict()
    }
    
    # Append-only write
    ledger = Path(ledger_path)
    with ledger.open("a") as f:
        f.write(json.dumps(record) + "\n")