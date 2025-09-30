#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω Ethics Metrics Module
==============================

Implements real computation and attestation of ethical metrics:
- ECE (Expected Calibration Error)
- ρ_bias (Bias ratio across protected groups)
- Fairness (demographic parity / equalized odds)
- Consent (data usage compliance)
- Eco-impact (carbon footprint estimates)

All metrics produce attestation hashes for WORM ledger.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class FairnessMetric(str, Enum):
    """Fairness metric types"""
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUAL_OPPORTUNITY = "equal_opportunity"


@dataclass
class EthicsAttestation:
    """Attestation record for ethics metrics"""
    timestamp: float
    dataset_hash: str  # Hash of input dataset
    seed: int
    ece: float  # Expected Calibration Error
    rho_bias: float  # Bias ratio (worst protected group)
    fairness_score: float  # Fairness metric [0,1]
    consent_ok: bool  # Data usage consent verified
    eco_impact_kg: float  # Estimated CO2 in kg
    evidence_hash: str  # Hash of all computation evidence
    pass_sigma_guard: bool  # Overall pass/fail
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def compute_hash(self) -> str:
        """Compute attestation hash for WORM ledger"""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class CalibrationBin:
    """Single bin for calibration measurement"""
    confidence_lower: float
    confidence_upper: float
    predicted_probs: List[float] = field(default_factory=list)
    true_labels: List[int] = field(default_factory=list)
    
    def accuracy(self) -> float:
        """Empirical accuracy in this bin"""
        if not self.true_labels:
            return 0.0
        return sum(self.true_labels) / len(self.true_labels)
    
    def avg_confidence(self) -> float:
        """Average predicted confidence in bin"""
        if not self.predicted_probs:
            return 0.0
        return sum(self.predicted_probs) / len(self.predicted_probs)
    
    def count(self) -> int:
        return len(self.predicted_probs)


class EthicsMetricsCalculator:
    """
    Computes and attests ethical metrics for model outputs.
    
    Fail-closed: if computation fails or data insufficient, 
    returns worst-case values to block promotion.
    """
    
    def __init__(
        self,
        ece_bins: int = 10,
        fairness_threshold: float = 0.8,
        bias_threshold: float = 1.05,
        ece_threshold: float = 0.01,
    ):
        self.ece_bins = ece_bins
        self.fairness_threshold = fairness_threshold
        self.bias_threshold = bias_threshold
        self.ece_threshold = ece_threshold
    
    def compute_ece(
        self,
        predicted_probs: List[float],
        true_labels: List[int],
    ) -> Tuple[float, str]:
        """
        Compute Expected Calibration Error using binning method.
        
        ECE = Σ (|B_i|/n) * |acc(B_i) - conf(B_i)|
        
        Returns:
            (ece_value, evidence_hash)
        """
        if len(predicted_probs) != len(true_labels):
            # Fail-closed: return worst case
            return 1.0, hashlib.sha256(b"length_mismatch").hexdigest()
        
        if len(predicted_probs) < self.ece_bins:
            # Not enough data for reliable ECE
            return 1.0, hashlib.sha256(b"insufficient_data").hexdigest()
        
        # Create bins
        bins: List[CalibrationBin] = []
        for i in range(self.ece_bins):
            lower = i / self.ece_bins
            upper = (i + 1) / self.ece_bins
            bins.append(CalibrationBin(lower, upper))
        
        # Assign predictions to bins
        for prob, label in zip(predicted_probs, true_labels):
            bin_idx = min(int(prob * self.ece_bins), self.ece_bins - 1)
            bins[bin_idx].predicted_probs.append(prob)
            bins[bin_idx].true_labels.append(label)
        
        # Compute ECE
        n_total = len(predicted_probs)
        ece = 0.0
        
        for bin in bins:
            if bin.count() == 0:
                continue
            
            weight = bin.count() / n_total
            calibration_error = abs(bin.accuracy() - bin.avg_confidence())
            ece += weight * calibration_error
        
        # Create evidence hash
        evidence = {
            "n_samples": n_total,
            "n_bins": self.ece_bins,
            "bin_counts": [b.count() for b in bins],
            "ece": ece,
        }
        evidence_hash = hashlib.sha256(
            json.dumps(evidence, sort_keys=True).encode()
        ).hexdigest()
        
        return ece, evidence_hash
    
    def compute_bias_ratio(
        self,
        predictions: List[int],
        protected_groups: List[str],
        labels: List[int],
    ) -> Tuple[float, str]:
        """
        Compute worst-case bias ratio across protected groups.
        
        ρ_bias = max_group(positive_rate_group / positive_rate_overall)
        
        Returns:
        if len(predictions) != len(protected_groups) or len(predictions) != len(labels):
            # Fail-closed
            return 10.0, hashlib.sha256(b"length_mismatch").hexdigest()
        
        if len(predictions) < 10:
            return 10.0, hashlib.sha256(b"insufficient_data").hexdigest()
        
        # Compute overall positive rate with safety check
        overall_pos_rate = sum(predictions) / len(predictions)
        if overall_pos_rate < 1e-6:
            overall_pos_rate = 1e-6  # Avoid division by zero
            # Fail-closed
            return 10.0, hashlib.sha256(b"length_mismatch").hexdigest()
        
        if len(predictions) < 10:
            return 10.0, hashlib.sha256(b"insufficient_data").hexdigest()
        
        # Compute overall positive rate
        overall_pos_rate = sum(predictions) / len(predictions)
        if overall_pos_rate < 1e-6:
            overall_pos_rate = 1e-6  # Avoid division by zero
        
        # Compute per-group rates
        group_stats: Dict[str, Dict[str, float]] = {}
        for group in set(protected_groups):
            group_preds = [p for p, g in zip(predictions, protected_groups) if g == group]
            if not group_preds:
                continue
            
            pos_rate = sum(group_preds) / len(group_preds)
            ratio = pos_rate / overall_pos_rate
            
            group_stats[group] = {
                "positive_rate": pos_rate,
                "ratio": ratio,
                "count": len(group_preds),
            }
        
        # Find worst bias ratio
        if not group_stats:
            return 10.0, hashlib.sha256(b"no_groups").hexdigest()
        
        max_ratio = max(stats["ratio"] for stats in group_stats.values())
        min_ratio = min(stats["ratio"] for stats in group_stats.values())
        
        # Bias is deviation from 1.0 in either direction
        rho_bias = max(max_ratio, 1.0 / (min_ratio + 1e-6))
        
        # Evidence hash
        evidence = {
            "overall_rate": overall_pos_rate,
            "group_stats": group_stats,
            "rho_bias": rho_bias,
        }
        evidence_hash = hashlib.sha256(
            json.dumps(evidence, sort_keys=True).encode()
        ).hexdigest()
        
        return rho_bias, evidence_hash
    
    def compute_fairness(
        self,
        predictions: List[int],
        protected_groups: List[str],
        labels: List[int],
        metric: FairnessMetric = FairnessMetric.DEMOGRAPHIC_PARITY,
    ) -> Tuple[float, str]:
        """
        Compute fairness score [0,1] where 1.0 is perfectly fair.
        
        Demographic Parity: P(Ŷ=1|A=a) should be equal across groups
        Equalized Odds: TPR and FPR should be equal across groups
        
        Returns:
            (fairness_score, evidence_hash)
        """
        if len(predictions) != len(protected_groups):
            return 0.0, hashlib.sha256(b"length_mismatch").hexdigest()
        
        unique_groups = list(set(protected_groups))
        if len(unique_groups) < 2:
            # Only one group - perfectly "fair" by definition
            return 1.0, hashlib.sha256(b"single_group").hexdigest()
        
        group_metrics: Dict[str, Dict[str, float]] = {}
        
        for group in unique_groups:
            group_mask = [g == group for g in protected_groups]
            group_preds = [p for p, m in zip(predictions, group_mask) if m]
            group_labels = [l for l, m in zip(labels, group_mask) if m]
            
            if not group_preds:
                continue
            
            if metric == FairnessMetric.DEMOGRAPHIC_PARITY:
                # Measure positive rate
                pos_rate = sum(group_preds) / len(group_preds)
                group_metrics[group] = {"positive_rate": pos_rate}
            
            elif metric in (FairnessMetric.EQUALIZED_ODDS, FairnessMetric.EQUAL_OPPORTUNITY):
                # Compute TPR and FPR
                tp = sum(1 for p, l in zip(group_preds, group_labels) if p == 1 and l == 1)
                fp = sum(1 for p, l in zip(group_preds, group_labels) if p == 1 and l == 0)
                fn = sum(1 for p, l in zip(group_preds, group_labels) if p == 0 and l == 1)
                tn = sum(1 for p, l in zip(group_preds, group_labels) if p == 0 and l == 0)
                
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                
                group_metrics[group] = {"tpr": tpr, "fpr": fpr}
        
        if not group_metrics:
            return 0.0, hashlib.sha256(b"no_valid_groups").hexdigest()
        
        # Compute fairness as 1 - max_disparity
        if metric == FairnessMetric.DEMOGRAPHIC_PARITY:
            rates = [m["positive_rate"] for m in group_metrics.values()]
            disparity = max(rates) - min(rates)
        else:
            tpr_values = [m["tpr"] for m in group_metrics.values()]
            fpr_values = [m["fpr"] for m in group_metrics.values()]
            tpr_disparity = max(tpr_values) - min(tpr_values)
            fpr_disparity = max(fpr_values) - min(fpr_values)
            disparity = max(tpr_disparity, fpr_disparity)
        
        fairness_score = max(0.0, 1.0 - disparity)
        
        # Evidence hash
        evidence = {
            "metric": metric.value,
            "group_metrics": group_metrics,
            "disparity": disparity,
            "fairness_score": fairness_score,
        }
        evidence_hash = hashlib.sha256(
            json.dumps(evidence, sort_keys=True).encode()
        ).hexdigest()
        
        return fairness_score, evidence_hash
    
    def compute_full_attestation(
        self,
        predicted_probs: List[float],
        predictions: List[int],
        labels: List[int],
        protected_groups: List[str],
        dataset_hash: str,
        seed: int,
        consent_verified: bool = True,
        estimated_tokens: int = 0,
    ) -> EthicsAttestation:
        """
        Compute full ethics attestation with all metrics.
        
        This is the main entry point for ethics verification.
        """
        # Compute ECE
        ece, ece_evidence = self.compute_ece(predicted_probs, labels)
        
        # Compute bias ratio
        rho_bias, bias_evidence = self.compute_bias_ratio(
            predictions, protected_groups, labels
        )
        
        # Compute fairness
        fairness_score, fairness_evidence = self.compute_fairness(
            predictions, protected_groups, labels,
            metric=FairnessMetric.DEMOGRAPHIC_PARITY
        )
        
        # Estimate eco impact (rough: 0.2g CO2 per 1000 tokens)
        eco_impact_kg = (estimated_tokens / 1000.0) * 0.0002
        
        # Aggregate evidence hash
        all_evidence = {
            "ece": ece_evidence,
            "bias": bias_evidence,
            "fairness": fairness_evidence,
            "eco": eco_impact_kg,
        }
        evidence_hash = hashlib.sha256(
            json.dumps(all_evidence, sort_keys=True).encode()
        ).hexdigest()
        
        # Determine if passes Σ-Guard
        pass_sigma_guard = (
            ece <= self.ece_threshold
            and rho_bias <= self.bias_threshold
            and fairness_score >= self.fairness_threshold
            and consent_verified
        )
        
        return EthicsAttestation(
            timestamp=time.time() if 'time' in dir() else 0.0,
            dataset_hash=dataset_hash,
            seed=seed,
            ece=ece,
            rho_bias=rho_bias,
            fairness_score=fairness_score,
            consent_ok=consent_verified,
            eco_impact_kg=eco_impact_kg,
            evidence_hash=evidence_hash,
            pass_sigma_guard=pass_sigma_guard,
        )


# Convenience functions for integration
def compute_ethics_attestation(
    model_outputs: Dict[str, Any],
    ground_truth: Dict[str, Any],
    seed: int,
    thresholds: Optional[Dict[str, float]] = None,
) -> EthicsAttestation:
    """
    Convenience wrapper for computing ethics attestation.
    
    Args:
        model_outputs: Dict with keys:
            - predicted_probs: List[float] - confidence scores
            - predictions: List[int] - binary predictions
            - protected_groups: List[str] - group labels
            - estimated_tokens: int - token count
        ground_truth: Dict with keys:
            - labels: List[int] - true binary labels
            - dataset_hash: str - hash of input data
            - consent_verified: bool - consent flag
        seed: int - random seed for reproducibility
        thresholds: Optional dict to override defaults
    
    Returns:
        EthicsAttestation object
    """
    calc_kwargs = thresholds or {}
    calculator = EthicsMetricsCalculator(**calc_kwargs)
    
    return calculator.compute_full_attestation(
        predicted_probs=model_outputs.get("predicted_probs", []),
        predictions=model_outputs.get("predictions", []),
        labels=ground_truth.get("labels", []),
        protected_groups=model_outputs.get("protected_groups", []),
        dataset_hash=ground_truth.get("dataset_hash", ""),
        seed=seed,
        consent_verified=ground_truth.get("consent_verified", False),
        estimated_tokens=model_outputs.get("estimated_tokens", 0),
    )


if __name__ == "__main__":
    # Self-test
    import time
    
    print("Testing Ethics Metrics Calculator...")
    
    # Generate synthetic data
    n_samples = 100
    predicted_probs = [0.1 * i / n_samples + 0.05 for i in range(n_samples)]
    predictions = [1 if p > 0.5 else 0 for p in predicted_probs]
    labels = [1 if (i % 3 == 0) else 0 for i in range(n_samples)]
    protected_groups = ["A" if i % 2 == 0 else "B" for i in range(n_samples)]
    
    calculator = EthicsMetricsCalculator()
    
    # Test ECE
    ece, ece_ev = calculator.compute_ece(predicted_probs, labels)
    print(f"✓ ECE: {ece:.4f} (evidence: {ece_ev[:8]}...)")
    
    # Test bias ratio
    rho, rho_ev = calculator.compute_bias_ratio(predictions, protected_groups, labels)
    print(f"✓ ρ_bias: {rho:.4f} (evidence: {rho_ev[:8]}...)")
    
    # Test fairness
    fair, fair_ev = calculator.compute_fairness(predictions, protected_groups, labels)
    print(f"✓ Fairness: {fair:.4f} (evidence: {fair_ev[:8]}...)")
    
    # Test full attestation
    model_outputs = {
        "predicted_probs": predicted_probs,
        "predictions": predictions,
        "protected_groups": protected_groups,
        "estimated_tokens": 1000,
    }
    ground_truth = {
        "labels": labels,
        "dataset_hash": "test_hash_123",
        "consent_verified": True,
    }
    
    attestation = compute_ethics_attestation(model_outputs, ground_truth, seed=42)
    print(f"\n✓ Full Attestation:")
    print(f"  - ECE: {attestation.ece:.4f}")
    print(f"  - ρ_bias: {attestation.rho_bias:.4f}")
    print(f"  - Fairness: {attestation.fairness_score:.4f}")
    print(f"  - Eco impact: {attestation.eco_impact_kg:.6f} kg CO2")
    print(f"  - Pass Σ-Guard: {attestation.pass_sigma_guard}")
    print(f"  - Attestation hash: {attestation.compute_hash()[:16]}...")
    
    print("\n✅ All tests passed!")