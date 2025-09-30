"""
Ethics Metrics Module
=====================

Computes real ethics and risk metrics for Σ-Guard validation:
- ECE (Expected Calibration Error)
- Bias ratios (ρ_bias)
- Fairness metrics (demographic parity, equal opportunity)
- Consent validation
- Risk contractivity (ρ for IR→IC)

All metrics are computed with evidence tracking for WORM audit trail.
"""

import math
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class EthicsMetricsResult:
    """Container for computed ethics metrics with evidence"""
    ece: float  # Expected Calibration Error [0,1]
    rho_bias: float  # Bias amplification ratio
    fairness_dp: float  # Demographic parity distance
    fairness_eo: float  # Equal opportunity distance
    consent_valid: bool  # Consent validation passed
    eco_impact: float  # Ecological impact score [0,1]
    rho_risk: float  # Risk contractivity factor
    evidence_hash: str  # Hash of input data for audit
    details: Dict[str, Any]  # Additional details
    timestamp: float
    
    def passes_sigma_guard(self, 
                          ece_max: float = 0.01,
                          rho_bias_max: float = 1.05,
                          rho_risk_max: float = 1.0) -> Tuple[bool, List[str]]:
        """Check if metrics pass Σ-Guard thresholds"""
        failures = []
        
        if self.ece > ece_max:
            failures.append(f"ECE {self.ece:.4f} > {ece_max}")
        
        if self.rho_bias > rho_bias_max:
            failures.append(f"ρ_bias {self.rho_bias:.4f} > {rho_bias_max}")
            
        if self.rho_risk >= rho_risk_max:
            failures.append(f"ρ_risk {self.rho_risk:.4f} >= {rho_risk_max}")
            
        if not self.consent_valid:
            failures.append("Consent validation failed")
            
        return len(failures) == 0, failures


def compute_ece(predictions: List[Tuple[float, bool]], 
                n_bins: int = 10,
                weighted: bool = True) -> Tuple[float, Dict]:
    """
    Compute Expected Calibration Error (ECE).
    
    Args:
        predictions: List of (confidence, correct) tuples
        n_bins: Number of bins for calibration
        weighted: Whether to weight by bin size
        
    Returns:
        ECE value and details dict
    """
    if not predictions:
        return 0.0, {"n_samples": 0, "bins": []}
    
    n = len(predictions)
    
    # Create bin boundaries (numpy-free implementation)
    if HAS_NUMPY:
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
    else:
        # Manual linspace
        bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
    
    ece = 0.0
    bin_details = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Collect predictions in this bin
        in_bin = [(conf, correct) for conf, correct in predictions
                  if bin_lower <= conf < bin_upper or (conf == 1.0 and bin_upper == 1.0)]
        
        if not in_bin:
            bin_details.append({
                "range": [float(bin_lower), float(bin_upper)],
                "n": 0,
                "avg_conf": 0,
                "accuracy": 0,
                "gap": 0
            })
            continue
            
        bin_size = len(in_bin)
        avg_confidence = sum(conf for conf, _ in in_bin) / bin_size
        accuracy = sum(1 for _, correct in in_bin if correct) / bin_size
        gap = abs(avg_confidence - accuracy)
        
        if weighted:
            ece += (bin_size / n) * gap
        else:
            ece += gap / n_bins
            
        bin_details.append({
            "range": [float(bin_lower), float(bin_upper)],
            "n": bin_size,
            "avg_conf": float(avg_confidence),
            "accuracy": float(accuracy),
            "gap": float(gap)
        })
    
    return float(ece), {"n_samples": n, "n_bins": n_bins, "bins": bin_details}


def compute_bias_ratio(group_outcomes: Dict[str, List[float]],
                       reference_group: Optional[str] = None) -> Tuple[float, Dict]:
    """
    Compute bias amplification ratio (ρ_bias).
    
    Args:
        group_outcomes: Dict mapping group names to outcome values
        reference_group: Reference group for comparison (default: best performing)
        
    Returns:
        Maximum bias ratio and details
    """
    if not group_outcomes or all(not v for v in group_outcomes.values()):
        return 1.0, {"groups": {}, "reference": None}
    
    # Compute mean outcome per group
    group_means = {}
    for group, outcomes in group_outcomes.items():
        if outcomes:
            group_means[group] = sum(outcomes) / len(outcomes)
    
    if not group_means:
        return 1.0, {"groups": {}, "reference": None}
    
    # Find reference group (best performing if not specified)
    if reference_group is None or reference_group not in group_means:
        reference_group = max(group_means, key=group_means.get)
    
    ref_mean = group_means[reference_group]
    if ref_mean == 0:
        return float('inf'), {"groups": group_means, "reference": reference_group}
    
    # Compute ratios
    ratios = {}
    for group, mean_val in group_means.items():
        if group != reference_group:
            # Bias ratio: how much worse is this group compared to reference
            if mean_val == 0:
                ratios[group] = float('inf')
            else:
                ratios[group] = ref_mean / mean_val if ref_mean > mean_val else mean_val / ref_mean
    
    max_ratio = max(ratios.values()) if ratios else 1.0
    
    return float(max_ratio), {
        "groups": {k: float(v) for k, v in group_means.items()},
        "reference": reference_group,
        "ratios": {k: float(v) for k, v in ratios.items()}
    }


def compute_fairness_metrics(predictions_by_group: Dict[str, List[Tuple[float, bool]]],
                            positive_class: bool = True) -> Dict[str, float]:
    """
    Compute fairness metrics: demographic parity and equal opportunity.
    
    Args:
        predictions_by_group: Dict mapping groups to (prediction, actual) tuples
        positive_class: Which class to consider positive
        
    Returns:
        Dict with fairness metrics
    """
    if not predictions_by_group:
        return {"demographic_parity": 0.0, "equal_opportunity": 0.0}
    
    # Compute positive rates per group
    positive_rates = {}
    tpr_rates = {}  # True positive rates for equal opportunity
    
    for group, preds in predictions_by_group.items():
        if not preds:
            continue
            
        # Demographic parity: P(Ŷ=1)
        positive_predictions = sum(1 for pred, _ in preds if pred >= 0.5)
        positive_rates[group] = positive_predictions / len(preds)
        
        # Equal opportunity: P(Ŷ=1|Y=1) - TPR
        positives = [(pred, actual) for pred, actual in preds if actual == positive_class]
        if positives:
            true_positives = sum(1 for pred, _ in positives if pred >= 0.5)
            tpr_rates[group] = true_positives / len(positives)
    
    # Compute max differences
    dp_distance = 0.0
    eo_distance = 0.0
    
    if positive_rates:
        dp_distance = max(positive_rates.values()) - min(positive_rates.values())
    
    if tpr_rates:
        eo_distance = max(tpr_rates.values()) - min(tpr_rates.values())
    
    return {
        "demographic_parity": float(dp_distance),
        "equal_opportunity": float(eo_distance),
        "positive_rates": {k: float(v) for k, v in positive_rates.items()},
        "tpr_rates": {k: float(v) for k, v in tpr_rates.items()}
    }


def validate_consent(data_sources: List[Dict[str, Any]],
                     required_fields: List[str] = None) -> Tuple[bool, Dict]:
    """
    Validate consent and data usage compliance.
    
    Args:
        data_sources: List of data source metadata dicts
        required_fields: Required consent fields
        
    Returns:
        Validation result and details
    """
    if required_fields is None:
        required_fields = ["consent_given", "purpose_specified", "retention_defined"]
    
    all_valid = True
    details = {"sources": []}
    
    for source in data_sources:
        source_valid = all(source.get(field, False) for field in required_fields)
        all_valid = all_valid and source_valid
        
        details["sources"].append({
            "id": source.get("id", "unknown"),
            "valid": source_valid,
            "fields": {field: source.get(field, False) for field in required_fields}
        })
    
    return all_valid, details


def compute_risk_contractivity(risk_history: List[float],
                              window: int = 10) -> Tuple[float, Dict]:
    """
    Compute risk contractivity factor ρ for IR→IC validation.
    
    Args:
        risk_history: Historical risk values
        window: Window size for computing contractivity
        
    Returns:
        Contractivity factor ρ and details
    """
    if len(risk_history) < 2:
        return 1.0, {"n_samples": len(risk_history), "trend": "insufficient_data"}
    
    # Use sliding window if history is long
    if len(risk_history) > window:
        risk_history = risk_history[-window:]
    
    # Compute successive ratios
    ratios = []
    for i in range(1, len(risk_history)):
        if risk_history[i-1] > 0:
            ratio = risk_history[i] / risk_history[i-1]
            ratios.append(ratio)
    
    if not ratios:
        return 1.0, {"n_samples": len(risk_history), "trend": "no_change"}
    
    # Contractivity is the maximum ratio (worst case)
    rho = max(ratios)
    avg_ratio = sum(ratios) / len(ratios)
    
    trend = "contracting" if rho < 1.0 else "expanding" if rho > 1.0 else "stable"
    
    return float(rho), {
        "n_samples": len(risk_history),
        "window": window,
        "max_ratio": float(rho),
        "avg_ratio": float(avg_ratio),
        "trend": trend,
        "ratios": [float(r) for r in ratios[-5:]]  # Last 5 for inspection
    }


def compute_ecological_impact(resource_usage: Dict[str, float],
                             baselines: Optional[Dict[str, float]] = None) -> float:
    """
    Compute normalized ecological impact score.
    
    Args:
        resource_usage: Dict with cpu_percent, memory_mb, gpu_watts, etc.
        baselines: Baseline values for normalization
        
    Returns:
        Ecological impact score [0,1], lower is better
    """
    if not resource_usage:
        return 0.0
    
    if baselines is None:
        baselines = {
            "cpu_percent": 100.0,
            "memory_mb": 8192.0,
            "gpu_watts": 300.0,
            "network_mb": 100.0
        }
    
    # Normalize each resource
    impacts = []
    for resource, usage in resource_usage.items():
        if resource in baselines and baselines[resource] > 0:
            normalized = min(1.0, usage / baselines[resource])
            impacts.append(normalized)
    
    if not impacts:
        return 0.0
    
    # Average normalized impact
    return sum(impacts) / len(impacts)


def hash_evidence(data: Any) -> str:
    """Create hash of evidence for audit trail"""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    
    return hashlib.sha256(data_str.encode()).hexdigest()[:16]


# Helper for complete ethics evaluation
def evaluate_ethics_comprehensive(
    predictions: List[Tuple[float, bool]],
    predictions_by_group: Optional[Dict[str, List[Tuple[float, bool]]]] = None,
    group_outcomes: Optional[Dict[str, List[float]]] = None,
    risk_history: Optional[List[float]] = None,
    data_sources: Optional[List[Dict[str, Any]]] = None,
    resource_usage: Optional[Dict[str, float]] = None,
    config: Optional[Dict[str, Any]] = None
) -> EthicsMetricsResult:
    """
    Comprehensive ethics evaluation combining all metrics.
    
    Returns complete EthicsMetricsResult with all computed values.
    """
    import time
    
    # Default config
    if config is None:
        config = {}
    
    # ECE computation
    ece, ece_details = compute_ece(predictions) if predictions else (0.0, {})
    
    # Bias ratio
    rho_bias, bias_details = compute_bias_ratio(group_outcomes) if group_outcomes else (1.0, {})
    
    # Fairness metrics
    fairness = compute_fairness_metrics(predictions_by_group) if predictions_by_group else {}
    
    # Consent validation
    consent_valid, consent_details = validate_consent(data_sources) if data_sources else (True, {})
    
    # Risk contractivity
    rho_risk, risk_details = compute_risk_contractivity(risk_history) if risk_history else (1.0, {})
    
    # Ecological impact
    eco_impact = compute_ecological_impact(resource_usage) if resource_usage else 0.0
    
    # Create evidence hash
    evidence = {
        "predictions_count": len(predictions) if predictions else 0,
        "groups": list(predictions_by_group.keys()) if predictions_by_group else [],
        "risk_points": len(risk_history) if risk_history else 0,
        "timestamp": time.time()
    }
    evidence_hash = hash_evidence(evidence)
    
    return EthicsMetricsResult(
        ece=ece,
        rho_bias=rho_bias,
        fairness_dp=fairness.get("demographic_parity", 0.0),
        fairness_eo=fairness.get("equal_opportunity", 0.0),
        consent_valid=consent_valid,
        eco_impact=eco_impact,
        rho_risk=rho_risk,
        evidence_hash=evidence_hash,
        details={
            "ece": ece_details,
            "bias": bias_details,
            "fairness": fairness,
            "consent": consent_details,
            "risk": risk_details,
            "config": config
        },
        timestamp=time.time()
    )


# Import json for evidence hashing
import json
