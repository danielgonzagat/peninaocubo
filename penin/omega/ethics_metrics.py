"""
PENIN-Ω Ethics Metrics Module
=============================

Implements calculation and attestation of ethical metrics (ΣEA/IR→IC):
- ECE (Expected Calibration Error)
- Bias ratio (ρ_bias)
- Fairness metrics
- Consent validation
- Risk contraction (IR→IC)

All metrics are calculated with evidence and logged to WORM.
"""

import math
import json
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

# Try to import numpy, fallback to basic Python if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("INFO: numpy not available, using basic Python fallback")

# Pydantic for validation
try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    print("WARNING: pydantic not available. Using dataclass fallback.")


@dataclass
class EthicsMetrics:
    """Ethics metrics with evidence"""
    ece: float
    rho_bias: float
    fairness: float
    consent: bool
    eco_ok: bool
    risk_rho: float
    evidence_hash: str
    calculation_timestamp: str
    dataset_hash: Optional[str] = None
    seed_hash: Optional[str] = None


class EthicsCalculator:
    """Calculator for ethical metrics with evidence tracking"""

    def __init__(self):
        self.evidence_cache = {}

    # Convenience aliases for different method names
    def compute_ece(self, predictions, targets, n_bins=15):
        """Alias for calculate_ece"""
        return self.calculate_ece(predictions, targets, n_bins)

    def compute_bias_ratio(self, predictions, groups, targets):
        """Alias for calculate_bias_ratio"""
        return self.calculate_bias_ratio(predictions, groups, targets)

    def compute_fairness(self, predictions, groups, targets, metric='demographic_parity'):
        """Alias for calculate_fairness"""
        return self.calculate_fairness(predictions, targets, groups)

    def calculate_ece(self, predictions: List[float], targets: List[int],
                     n_bins: int = 15) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Expected Calibration Error (ECE)
        
        Args:
            predictions: List of predicted probabilities [0,1]
            targets: List of true binary labels {0,1}
            n_bins: Number of bins for calibration
            
        Returns:
            (ece_score, evidence_hash)
        """
        # Fail-closed: return worst ECE if insufficient data
        if len(predictions) == 0 or len(targets) == 0 or len(predictions) != len(targets):
            evidence = {'method': 'ECE', 'error': 'insufficient_data'}
            evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
            return 1.0, evidence_hash

        if HAS_NUMPY:
            return self._calculate_ece_numpy(predictions, targets, n_bins)
        else:
            return self._calculate_ece_basic(predictions, targets, n_bins)

    def _calculate_ece_numpy(self, predictions: List[float], targets: List[int], n_bins: int):
        """ECE calculation using numpy"""
        # Convert to numpy arrays
        predictions_np = np.array(predictions)
        targets_np = np.array(targets)

        # Create bins
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        ece = 0
        bin_data = []

        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = np.logical_and(predictions_np > bin_lower, predictions_np <= bin_upper)
            prop_in_bin = in_bin.mean()

            if prop_in_bin > 0:
                accuracy_in_bin = targets_np[in_bin].mean()
                avg_confidence_in_bin = predictions_np[in_bin].mean()
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

                bin_data.append({
                    'bin_lower': float(bin_lower),
                    'bin_upper': float(bin_upper),
                    'prop_in_bin': float(prop_in_bin),
                    'accuracy': float(accuracy_in_bin),
                    'confidence': float(avg_confidence_in_bin),
                    'count': int(in_bin.sum())
                })

        evidence = {
            'method': 'ECE',
            'n_bins': n_bins,
            'n_samples': len(predictions),
            'bin_data': bin_data,
            'ece_score': float(ece)
        }

        # Return hash of evidence for WORM ledger
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()

        return float(ece), evidence_hash

    def _calculate_ece_basic(self, predictions: List[float], targets: List[int], n_bins: int):
        """ECE calculation using basic Python (no numpy)"""
        # Create bins manually
        bin_width = 1.0 / n_bins
        ece = 0
        bin_data = []

        for i in range(n_bins):
            bin_lower = i * bin_width
            bin_upper = (i + 1) * bin_width

            # Find predictions in this bin
            in_bin_preds = []
            in_bin_targets = []
            for pred, target in zip(predictions, targets):
                if (i == 0 and pred <= bin_upper) or (i > 0 and bin_lower < pred <= bin_upper):
                    in_bin_preds.append(pred)
                    in_bin_targets.append(target)
                    in_bin_preds.append(pred)
                    in_bin_targets.append(target)

            if in_bin_preds:
                prop_in_bin = len(in_bin_preds) / len(predictions)
                accuracy_in_bin = sum(in_bin_targets) / len(in_bin_targets)
                avg_confidence_in_bin = sum(in_bin_preds) / len(in_bin_preds)
                ece += abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

                bin_data.append({
                    'bin_lower': bin_lower,
                    'bin_upper': bin_upper,
                    'prop_in_bin': prop_in_bin,
                    'accuracy': accuracy_in_bin,
                    'confidence': avg_confidence_in_bin,
                    'count': len(in_bin_preds)
                })

        evidence = {
            'method': 'ECE',
            'n_bins': n_bins,
            'n_samples': len(predictions),
            'bin_data': bin_data,
            'ece_score': float(ece)
        }

        # Return hash of evidence for WORM ledger
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()

        return float(ece), evidence_hash

    def calculate_bias_ratio(self, predictions: List[float], targets: List[int],
                           protected_attributes: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate bias ratio (ρ_bias) across protected attributes
        
        Args:
            predictions: List of predicted probabilities
            targets: List of true labels
            protected_attributes: List of protected attribute values
            
        Returns:
            (rho_bias, evidence_dict)
        """
        if len(set(len(x) for x in [predictions, targets, protected_attributes])) != 1:
            raise ValueError("All inputs must have same length")

        # Group by protected attribute
        groups = {}
        for i, attr in enumerate(protected_attributes):
            if attr not in groups:
                groups[attr] = {'predictions': [], 'targets': []}
            groups[attr]['predictions'].append(predictions[i])
            groups[attr]['targets'].append(targets[i])

        # Calculate rates for each group (basic Python)
        group_rates = {}
        for attr, data in groups.items():
            preds = data['predictions']
            targets = data['targets']

            # Positive prediction rate
            pos_rate = sum(1 for p in preds if p > 0.5) / len(preds)

            # True positive rate
            positive_targets = [p for p, t in zip(preds, targets) if t == 1]
            tp_rate = sum(1 for p in positive_targets if p > 0.5) / len(positive_targets) if positive_targets else 0.0

            group_rates[attr] = {
                'positive_rate': pos_rate,
                'true_positive_rate': tp_rate,
                'count': len(preds)
            }

        # Calculate max bias ratio
        rates = [g['positive_rate'] for g in group_rates.values()]
        if len(rates) < 2 or min(rates) == 0:
            rho_bias = 1.0  # No bias if insufficient data
        else:
            rho_bias = max(rates) / min(rates)

        evidence = {
            'method': 'Bias_Ratio',
            'n_samples': len(predictions),
            'n_groups': len(groups),
            'group_rates': group_rates,
            'rho_bias': float(rho_bias)
        }

        # Return hash of evidence for WORM ledger
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()

        return float(rho_bias), evidence_hash

    def calculate_fairness(self, predictions: List[float], targets: List[int],
                          protected_attributes: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate fairness metric (1 - max_demographic_parity_difference)
        
        Args:
            predictions: List of predicted probabilities
            targets: List of true labels
            protected_attributes: List of protected attribute values
            
        Returns:
            (fairness_score, evidence_dict)
        """
        if len(set(len(x) for x in [predictions, targets, protected_attributes])) != 1:
            raise ValueError("All inputs must have same length")

        # Group by protected attribute
        groups = {}
        for i, attr in enumerate(protected_attributes):
            if attr not in groups:
                groups[attr] = {'predictions': [], 'targets': []}
            groups[attr]['predictions'].append(predictions[i])
            groups[attr]['targets'].append(targets[i])

        # Calculate positive rates for each group
        positive_rates = []
        group_data = {}

        for attr, data in groups.items():
            preds = data['predictions']
            pos_rate = sum(1 for p in preds if p > 0.5) / len(preds)
            positive_rates.append(pos_rate)

            group_data[attr] = {
                'positive_rate': pos_rate,
                'count': len(preds)
            }

        # Calculate demographic parity difference
        if len(positive_rates) < 2:
            max_diff = 0.0
        else:
            max_diff = max(positive_rates) - min(positive_rates)

        # Fairness score (higher is better)
        fairness = max(0.0, 1.0 - max_diff)

        evidence = {
            'method': 'Fairness_Demographic_Parity',
            'n_samples': len(predictions),
            'n_groups': len(groups),
            'group_data': group_data,
            'max_parity_difference': float(max_diff),
            'fairness_score': float(fairness)
        }

        # Return hash of evidence for WORM ledger
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()

        return float(fairness), evidence_hash

    def calculate_risk_contraction(self, risk_series: List[float],
                                  window_size: int = 10) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate risk contraction (IR→IC) - ρ < 1 indicates convergence
        
        Args:
            risk_series: Time series of risk values
            window_size: Window size for contraction analysis
            
        Returns:
            (rho_risk, evidence_dict)
        """
        if len(risk_series) < window_size:
            return 1.0, {'method': 'Risk_Contraction', 'error': 'insufficient_data'}

        # Calculate rolling variance (basic Python)
        rolling_var = []
        for i in range(window_size, len(risk_series)):
            window = risk_series[i-window_size:i]
            # Calculate variance manually
            mean_val = sum(window) / len(window)
            variance = sum((x - mean_val) ** 2 for x in window) / len(window)
            rolling_var.append(variance)

        if len(rolling_var) < 2:
            return 1.0, {'method': 'Risk_Contraction', 'error': 'insufficient_windows'}

        # Calculate contraction factor
        if any(v == 0 for v in rolling_var):
            rho_risk = 1.0  # Conservative default when variance is zero
        else:
            # Simple linear regression on log(variance) over time
            x = list(range(len(rolling_var)))
            y = [math.log(v + 1e-10) for v in rolling_var]  # Add small epsilon to avoid log(0)

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            if n * sum_x2 - sum_x * sum_x == 0:
                rho_risk = 1.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                rho_risk = math.exp(slope)

        evidence = {
            'method': 'Risk_Contraction',
            'n_samples': len(risk_series),
            'window_size': window_size,
            'rolling_variance': [float(v) for v in rolling_var],
            'contraction_factor': float(rho_risk),
            'is_contractive': rho_risk < 1.0
        }

        return float(rho_risk), evidence

    def calculate_all_metrics(self, predictions: List[float], targets: List[int],
                            protected_attributes: List[str], risk_series: List[float],
                            consent_data: Dict[str, Any], eco_data: Dict[str, Any],
                            dataset_id: Optional[str] = None, seed: Optional[int] = None) -> EthicsMetrics:
        """
        Calculate all ethical metrics with evidence
        
        Args:
            predictions: Model predictions
            targets: True labels
            protected_attributes: Protected attribute values
            risk_series: Risk time series
            consent_data: Consent validation data
            eco_data: Environmental compliance data
            dataset_id: Dataset identifier for hashing
            seed: Random seed for reproducibility
            
        Returns:
            EthicsMetrics with all calculated values and evidence
        """
        from datetime import datetime, timezone

        # Calculate individual metrics
        ece, ece_evidence = self.calculate_ece(predictions, targets)
        rho_bias, bias_evidence = self.calculate_bias_ratio(predictions, targets, protected_attributes)
        fairness, fairness_evidence = self.calculate_fairness(predictions, targets, protected_attributes)
        rho_risk, risk_evidence = self.calculate_risk_contraction(risk_series)

        # Validate consent and eco compliance
        consent = self._validate_consent(consent_data)
        eco_ok = self._validate_eco_compliance(eco_data)

        # Create evidence hash
        evidence_data = {
            'ece': ece_evidence,
            'bias': bias_evidence,
            'fairness': fairness_evidence,
            'risk': risk_evidence,
            'consent': consent_data,
            'eco': eco_data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'dataset_id': dataset_id,
            'seed': seed
        }

        evidence_str = json.dumps(evidence_data, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        # Calculate dataset and seed hashes
        dataset_hash = None
        if dataset_id:
            dataset_hash = hashlib.sha256(str(dataset_id).encode()).hexdigest()

        seed_hash = None
        if seed is not None:
            seed_hash = hashlib.sha256(str(seed).encode()).hexdigest()

        return EthicsMetrics(
            ece=ece,
            rho_bias=rho_bias,
            fairness=fairness,
            consent=consent,
            eco_ok=eco_ok,
            risk_rho=rho_risk,
            evidence_hash=evidence_hash,
            calculation_timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_hash=dataset_hash,
            seed_hash=seed_hash
        )

    def _validate_consent(self, consent_data: Dict[str, Any]) -> bool:
        """Validate consent requirements"""
        required_fields = ['user_consent', 'data_usage_consent', 'processing_consent']
        return all(consent_data.get(field, False) for field in required_fields)

    def _validate_eco_compliance(self, eco_data: Dict[str, Any]) -> bool:
        """Validate environmental compliance"""
        required_checks = ['carbon_footprint_ok', 'energy_efficiency_ok', 'waste_minimization_ok']
        return all(eco_data.get(check, False) for check in required_checks)


class EthicsGate:
    """Gate for ethical metrics validation"""

    def __init__(self, ece_threshold: float = 0.01, rho_bias_threshold: float = 1.05,
                 fairness_threshold: float = 0.95, consent_required: bool = True,
                 eco_required: bool = True, risk_threshold: float = 0.95):
        self.ece_threshold = ece_threshold
        self.rho_bias_threshold = rho_bias_threshold
        self.fairness_threshold = fairness_threshold
        self.consent_required = consent_required
        self.eco_required = eco_required
        self.risk_threshold = risk_threshold

    def validate(self, metrics: EthicsMetrics) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate ethical metrics against thresholds
        
        Returns:
            (is_valid, details_dict)
        """
        details = {
            'ece_ok': metrics.ece <= self.ece_threshold,
            'bias_ok': metrics.rho_bias <= self.rho_bias_threshold,
            'fairness_ok': metrics.fairness >= self.fairness_threshold,
            'consent_ok': metrics.consent if self.consent_required else True,
            'eco_ok': metrics.eco_ok if self.eco_required else True,
            'risk_ok': metrics.risk_rho < self.risk_threshold,
            'evidence_hash': metrics.evidence_hash,
            'timestamp': metrics.calculation_timestamp
        }

        # All gates must pass
        is_valid = all([
            details['ece_ok'],
            details['bias_ok'],
            details['fairness_ok'],
            details['consent_ok'],
            details['eco_ok'],
            details['risk_ok']
        ])

        details['overall_valid'] = is_valid

        return is_valid, details


if __name__ == "__main__":
    # Test the ethics calculator
    print("Testing Ethics Metrics Calculator...")

    calculator = EthicsCalculator()

    # Generate test data (basic Python)
    import random
    random.seed(42)
    n_samples = 1000
    predictions = [random.random() for _ in range(n_samples)]
    targets = [1 if random.random() > 0.3 else 0 for _ in range(n_samples)]
    protected_attrs = [random.choice(['A', 'B', 'C']) for _ in range(n_samples)]
    risk_series = [sum(random.random() - 0.5 for _ in range(i)) + 10 for i in range(50)]

    consent_data = {
        'user_consent': True,
        'data_usage_consent': True,
        'processing_consent': True
    }

    eco_data = {
        'carbon_footprint_ok': True,
        'energy_efficiency_ok': True,
        'waste_minimization_ok': True
    }

    # Calculate metrics
    metrics = calculator.calculate_all_metrics(
        predictions=predictions,
        targets=targets,
        protected_attributes=protected_attrs,
        risk_series=risk_series,
        consent_data=consent_data,
        eco_data=eco_data,
        dataset_id="test_dataset_001",
        seed=42
    )

    print(f"ECE: {metrics.ece:.4f}")
    print(f"Bias Ratio: {metrics.rho_bias:.4f}")
    print(f"Fairness: {metrics.fairness:.4f}")
    print(f"Risk Rho: {metrics.risk_rho:.4f}")
    print(f"Consent: {metrics.consent}")
    print(f"Eco OK: {metrics.eco_ok}")
    print(f"Evidence Hash: {metrics.evidence_hash[:16]}...")

    # Test gate
    gate = EthicsGate()
    is_valid, details = gate.validate(metrics)
    print(f"\nGate Valid: {is_valid}")
    print(f"Details: {details}")


# Backward compatibility aliases
EthicsMetricsCalculator = EthicsCalculator


def calculate_and_validate_ethics(
    state_dict: Dict[str, Any],
    config: Dict[str, Any],
    dataset_id: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate and validate ethics metrics (legacy API)

    Args:
        state_dict: State with predictions, labels, protected attributes, etc.
        config: Configuration with thresholds
        dataset_id: Dataset identifier
        seed: Random seed

    Returns:
        Dict with 'metrics' and 'validation' keys
    """
    calc = EthicsCalculator()

    predictions = state_dict.get('predictions', [])
    predicted_probs = state_dict.get('predicted_probs', predictions)
    labels = state_dict.get('labels', [])
    protected_attrs = state_dict.get('protected_attributes', [])
    risk_series = state_dict.get('risk_series', [0.5] * 10)

    # Calculate metrics
    ece, _ = calc.compute_ece(predicted_probs, labels) if predicted_probs else (1.0, '')
    rho, _ = calc.compute_bias_ratio(predictions, protected_attrs, labels) if protected_attrs else (1.0, '')
    fairness, _ = calc.compute_fairness(predictions, protected_attrs, labels) if protected_attrs else (0.0, '')
    risk_rho, _ = calc.calculate_risk_contraction(risk_series)

    consent = state_dict.get('consent', False)
    eco_ok = state_dict.get('eco_ok', True)

    # Get thresholds from config
    eth_config = config.get('ethics', {})
    ece_max = eth_config.get('ece_max', 0.15)
    rho_max = eth_config.get('rho_bias_max', 2.0)
    consent_required = eth_config.get('consent_required', True)
    eco_required = eth_config.get('eco_ok_required', False)

    # Validate
    violations = []
    if ece > ece_max:
        violations.append({
            'metric': 'ece',
            'value': ece,
            'threshold': ece_max,
            'message': f'ECE {ece:.4f} exceeds threshold {ece_max}'
        })

    if rho > rho_max:
        violations.append({
            'metric': 'rho_bias',
            'value': rho,
            'threshold': rho_max,
            'message': f'Bias ratio {rho:.4f} exceeds threshold {rho_max}'
        })

    if consent_required and not consent:
        violations.append({
            'metric': 'consent',
            'value': consent,
            'threshold': True,
            'message': 'Consent required but not granted'
        })

    if eco_required and not eco_ok:
        violations.append({
            'metric': 'eco_ok',
            'value': eco_ok,
            'threshold': True,
            'message': 'Eco compliance required but not met'
        })

    passed = len(violations) == 0

    return {
        'metrics': {
            'ece': ece,
            'rho_bias': rho,
            'fairness': fairness,
            'risk_rho': risk_rho,
            'consent': consent,
            'eco_ok': eco_ok
        },
        'validation': {
            'passed': passed,
            'violations': violations
        },
        'evidence': {
            'dataset_id': dataset_id,
            'seed': seed,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    }


def sigma_guard(
    ece: float,
    rho_bias: float,
    fairness_score: float,
    consent_ok: bool,
    risk_rho: float,
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Simple Sigma Guard check

    Args:
        ece: Expected calibration error
        rho_bias: Bias ratio
        fairness_score: Fairness score (0-1)
        consent_ok: Consent status
        risk_rho: Risk contractivity factor
        thresholds: Optional custom thresholds

    Returns:
        (passed, details)
    """
    if thresholds is None:
        thresholds = {
            'ece_max': 0.15,
            'rho_bias_max': 2.0,
            'fairness_min': 0.7,
            'risk_rho_max': 1.0
        }

    checks = {
        'ece_ok': ece <= thresholds.get('ece_max', 0.15),
        'bias_ok': rho_bias <= thresholds.get('rho_bias_max', 2.0),
        'fairness_ok': fairness_score >= thresholds.get('fairness_min', 0.7),
        'consent_ok': consent_ok,
        'risk_ok': risk_rho < thresholds.get('risk_rho_max', 1.0)
    }

    passed = all(checks.values())

    details = {
        **checks,
        'ece': ece,
        'rho_bias': rho_bias,
        'fairness': fairness_score,
        'risk_rho': risk_rho,
        'overall_passed': passed
    }

    return passed, details

# Enum for fairness metrics
from enum import Enum

class FairnessMetric(Enum):
    """Fairness metrics supported"""
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUAL_OPPORTUNITY = "equal_opportunity"


@dataclass
class EthicsAttestation:
    """Full ethics attestation with all metrics and evidence"""
    ece: float
    rho_bias: float
    fairness_score: float
    consent_ok: bool
    eco_impact_kg: float
    risk_rho: float
    evidence_hash: str
    pass_sigma_guard: bool
    timestamp: str
    dataset_hash: Optional[str] = None
    seed: Optional[int] = None

    def compute_hash(self) -> str:
        """Compute hash of attestation for WORM ledger"""
        data = {
            'ece': self.ece,
            'rho_bias': self.rho_bias,
            'fairness': self.fairness_score,
            'consent': self.consent_ok,
            'eco_kg': self.eco_impact_kg,
            'risk_rho': self.risk_rho,
            'evidence': self.evidence_hash,
            'timestamp': self.timestamp,
            'dataset': self.dataset_hash,
            'seed': self.seed
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


def compute_ethics_attestation(model_outputs: Dict[str, Any],
                               ground_truth: Dict[str, Any],
                               seed: Optional[int] = None,
                               thresholds: Optional[Dict[str, float]] = None) -> EthicsAttestation:
    """
    Compute comprehensive ethics attestation for a model
    
    Args:
        model_outputs: Dict with predicted_probs, predictions, protected_groups, estimated_tokens
        ground_truth: Dict with labels, dataset_hash, consent_verified
        seed: Random seed for reproducibility
        thresholds: Optional custom thresholds for gates
        
    Returns:
        EthicsAttestation with all metrics and pass/fail status
    """
    calc = EthicsCalculator()

    predicted_probs = model_outputs.get('predicted_probs', [])
    predictions = model_outputs.get('predictions', [])
    protected_groups = model_outputs.get('protected_groups', [])
    estimated_tokens = model_outputs.get('estimated_tokens', 1000)

    labels = ground_truth.get('labels', [])
    dataset_hash = ground_truth.get('dataset_hash', 'unknown')
    consent_verified = ground_truth.get('consent_verified', False)

    # Calculate metrics
    ece, ece_ev = calc.compute_ece(predicted_probs, labels)
    rho_bias, rho_ev = calc.compute_bias_ratio(predictions, protected_groups, labels)
    fairness, fair_ev = calc.compute_fairness(predictions, protected_groups, labels)

    # Calculate eco impact (simplified: ~0.0002 kg CO2 per 1000 tokens)
    eco_impact_kg = estimated_tokens * 0.0002 / 1000.0

    # Risk contractivity (placeholder if no risk series provided)
    risk_series = ground_truth.get('risk_series', [0.5] * 10)
    risk_rho, risk_ev = calc.calculate_risk_contraction(risk_series)

    # Combined evidence hash
    combined_evidence = {
        'ece': ece_ev,
        'rho_bias': rho_ev,
        'fairness': fair_ev,
        'risk': risk_ev,
        'seed': seed,
        'dataset': dataset_hash
    }
    evidence_json = json.dumps(combined_evidence, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()

    # Default thresholds
    if thresholds is None:
        thresholds = {
            'ece': 0.15,
            'rho_bias': 2.0,
            'fairness': 0.7,
            'risk_rho': 1.0
        }

    # Check if passes Sigma Guard
    pass_sigma_guard = (
        ece <= thresholds['ece'] and
        rho_bias <= thresholds['rho_bias'] and
        fairness >= thresholds['fairness'] and
        consent_verified and
        risk_rho < thresholds['risk_rho']
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    return EthicsAttestation(
        ece=ece,
        rho_bias=rho_bias,
        fairness_score=fairness,
        consent_ok=consent_verified,
        eco_impact_kg=eco_impact_kg,
        risk_rho=risk_rho,
        evidence_hash=evidence_hash,
        pass_sigma_guard=pass_sigma_guard,
        timestamp=timestamp,
        dataset_hash=dataset_hash,
        seed=seed
    )
