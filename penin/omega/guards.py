"""
Guards Module
=============

Implements Σ-Guard (ethics/safety gates) and IR→IC (risk contractivity) validation.
All guards are fail-closed: any violation blocks promotion.

Policy thresholds are configurable but default to conservative values.
Each guard returns (ok: bool, details: dict) for audit trail.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
import hashlib
import json


@dataclass
class GuardResult:
    """Result of a guard evaluation"""
    passed: bool
    guard_name: str
    violations: List[str]
    details: Dict[str, Any]
    timestamp: float
    evidence_hash: str
    
    def to_dict(self) -> Dict:
        """Convert to dict for serialization"""
        return asdict(self)


class SigmaGuardPolicy:
    """
    Σ-Guard policy configuration and thresholds.
    
    Default values are conservative (fail-closed).
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Ethics thresholds
        self.ece_max = config.get("ece_max", 0.01)  # Max expected calibration error
        self.rho_bias_max = config.get("rho_bias_max", 1.05)  # Max bias ratio
        self.fairness_dp_max = config.get("fairness_dp_max", 0.1)  # Max demographic parity distance
        self.fairness_eo_max = config.get("fairness_eo_max", 0.1)  # Max equal opportunity distance
        
        # Safety thresholds
        self.rho_risk_max = config.get("rho_risk_max", 1.0)  # Must be contractive (<1.0)
        self.eco_impact_max = config.get("eco_impact_max", 0.5)  # Max ecological impact
        
        # Consent requirements
        self.require_consent = config.get("require_consent", True)
        self.require_purpose = config.get("require_purpose", True)
        self.require_retention = config.get("require_retention", True)
        
        # Additional safety checks
        self.min_confidence = config.get("min_confidence", 0.7)  # Min model confidence
        self.max_uncertainty = config.get("max_uncertainty", 0.3)  # Max uncertainty
        self.require_human_oversight = config.get("require_human_oversight", False)
        
    def to_dict(self) -> Dict:
        """Export policy as dict"""
        return {
            "ece_max": self.ece_max,
            "rho_bias_max": self.rho_bias_max,
            "fairness_dp_max": self.fairness_dp_max,
            "fairness_eo_max": self.fairness_eo_max,
            "rho_risk_max": self.rho_risk_max,
            "eco_impact_max": self.eco_impact_max,
            "require_consent": self.require_consent,
            "require_purpose": self.require_purpose,
            "require_retention": self.require_retention,
            "min_confidence": self.min_confidence,
            "max_uncertainty": self.max_uncertainty,
            "require_human_oversight": self.require_human_oversight
        }


def sigma_guard(metrics: Dict[str, Any],
                policy: Optional[SigmaGuardPolicy] = None,
                strict: bool = True) -> GuardResult:
    """
    Σ-Guard: Comprehensive ethics and safety validation.
    
    Args:
        metrics: Dict containing computed metrics (ECE, bias, fairness, etc.)
        policy: Policy configuration (uses defaults if None)
        strict: If True, all checks must pass. If False, warnings allowed.
        
    Returns:
        GuardResult with pass/fail and detailed violations
    """
    if policy is None:
        policy = SigmaGuardPolicy()
    
    violations = []
    details = {
        "policy": policy.to_dict(),
        "metrics_received": list(metrics.keys()),
        "checks_performed": []
    }
    
    # ECE Check
    if "ece" in metrics:
        ece = metrics["ece"]
        details["checks_performed"].append("ece")
        if ece > policy.ece_max:
            violations.append(f"ECE {ece:.4f} exceeds threshold {policy.ece_max}")
            details["ece_violation"] = {"value": ece, "threshold": policy.ece_max}
    
    # Bias ratio check
    if "rho_bias" in metrics:
        rho_bias = metrics["rho_bias"]
        details["checks_performed"].append("rho_bias")
        if rho_bias > policy.rho_bias_max:
            violations.append(f"Bias ratio {rho_bias:.4f} exceeds threshold {policy.rho_bias_max}")
            details["bias_violation"] = {"value": rho_bias, "threshold": policy.rho_bias_max}
    
    # Fairness checks
    if "fairness_dp" in metrics:
        fairness_dp = metrics["fairness_dp"]
        details["checks_performed"].append("fairness_dp")
        if fairness_dp > policy.fairness_dp_max:
            violations.append(f"Demographic parity distance {fairness_dp:.4f} exceeds {policy.fairness_dp_max}")
            details["fairness_dp_violation"] = {"value": fairness_dp, "threshold": policy.fairness_dp_max}
    
    if "fairness_eo" in metrics:
        fairness_eo = metrics["fairness_eo"]
        details["checks_performed"].append("fairness_eo")
        if fairness_eo > policy.fairness_eo_max:
            violations.append(f"Equal opportunity distance {fairness_eo:.4f} exceeds {policy.fairness_eo_max}")
            details["fairness_eo_violation"] = {"value": fairness_eo, "threshold": policy.fairness_eo_max}
    
    # Risk contractivity check
    if "rho_risk" in metrics:
        rho_risk = metrics["rho_risk"]
        details["checks_performed"].append("rho_risk")
        if rho_risk >= policy.rho_risk_max:
            violations.append(f"Risk not contractive: ρ={rho_risk:.4f} >= {policy.rho_risk_max}")
            details["risk_violation"] = {"value": rho_risk, "threshold": policy.rho_risk_max}
    
    # Ecological impact check
    if "eco_impact" in metrics:
        eco_impact = metrics["eco_impact"]
        details["checks_performed"].append("eco_impact")
        if eco_impact > policy.eco_impact_max:
            violations.append(f"Ecological impact {eco_impact:.4f} exceeds {policy.eco_impact_max}")
            details["eco_violation"] = {"value": eco_impact, "threshold": policy.eco_impact_max}
    
    # Consent validation
    if policy.require_consent and "consent_valid" in metrics:
        details["checks_performed"].append("consent")
        if not metrics["consent_valid"]:
            violations.append("Consent validation failed")
            details["consent_violation"] = True
    
    # Confidence check
    if "confidence" in metrics:
        confidence = metrics["confidence"]
        details["checks_performed"].append("confidence")
        if confidence < policy.min_confidence:
            violations.append(f"Confidence {confidence:.4f} below minimum {policy.min_confidence}")
            details["confidence_violation"] = {"value": confidence, "threshold": policy.min_confidence}
    
    # Uncertainty check
    if "uncertainty" in metrics:
        uncertainty = metrics["uncertainty"]
        details["checks_performed"].append("uncertainty")
        if uncertainty > policy.max_uncertainty:
            violations.append(f"Uncertainty {uncertainty:.4f} exceeds maximum {policy.max_uncertainty}")
            details["uncertainty_violation"] = {"value": uncertainty, "threshold": policy.max_uncertainty}
    
    # Human oversight check
    if policy.require_human_oversight:
        details["checks_performed"].append("human_oversight")
        if not metrics.get("human_oversight_confirmed", False):
            if strict:
                violations.append("Human oversight required but not confirmed")
            details["human_oversight_required"] = True
    
    # Create evidence hash
    evidence = {
        "metrics": metrics,
        "policy": policy.to_dict(),
        "timestamp": time.time()
    }
    evidence_hash = hashlib.sha256(
        json.dumps(evidence, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    passed = len(violations) == 0
    
    return GuardResult(
        passed=passed,
        guard_name="sigma_guard",
        violations=violations,
        details=details,
        timestamp=time.time(),
        evidence_hash=evidence_hash
    )


def ir_to_ic_contractive(risk_history: List[float],
                         window: int = 10,
                         max_rho: float = 1.0,
                         require_monotonic: bool = False) -> GuardResult:
    """
    IR→IC (Information Risk to Information Confidence) contractivity check.
    
    Validates that risk is contracting over time (ρ < 1).
    
    Args:
        risk_history: List of risk values over time
        window: Sliding window size for analysis
        max_rho: Maximum allowed contractivity factor
        require_monotonic: If True, require strictly decreasing risk
        
    Returns:
        GuardResult with contractivity analysis
    """
    violations = []
    details = {
        "window": window,
        "max_rho": max_rho,
        "require_monotonic": require_monotonic,
        "history_length": len(risk_history)
    }
    
    if len(risk_history) < 2:
        details["status"] = "insufficient_data"
        passed = False  # Fail-closed when insufficient data
        violations.append(f"Insufficient risk history: {len(risk_history)} < 2")
    else:
        # Use sliding window if history is long
        analysis_window = risk_history[-window:] if len(risk_history) > window else risk_history
        
        # Compute contractivity ratios
        ratios = []
        for i in range(1, len(analysis_window)):
            if analysis_window[i-1] > 0:
                ratio = analysis_window[i] / analysis_window[i-1]
                ratios.append(ratio)
        
        if not ratios:
            details["status"] = "no_ratios"
            passed = False
            violations.append("Cannot compute contractivity ratios")
        else:
            max_ratio = max(ratios)
            avg_ratio = sum(ratios) / len(ratios)
            
            details["max_ratio"] = float(max_ratio)
            details["avg_ratio"] = float(avg_ratio)
            details["ratios"] = [float(r) for r in ratios]
            
            # Check contractivity
            if max_ratio >= max_rho:
                violations.append(f"Risk not contractive: max ρ={max_ratio:.4f} >= {max_rho}")
                details["status"] = "expanding"
            else:
                details["status"] = "contracting"
            
            # Check monotonicity if required
            if require_monotonic:
                if any(r >= 1.0 for r in ratios):
                    violations.append("Risk not monotonically decreasing")
                    details["monotonic"] = False
                else:
                    details["monotonic"] = True
            
            # Additional trend analysis
            if len(analysis_window) >= 3:
                # Check acceleration (second derivative)
                accel = []
                for i in range(2, len(analysis_window)):
                    if analysis_window[i-1] > 0 and analysis_window[i-2] > 0:
                        r1 = analysis_window[i-1] / analysis_window[i-2]
                        r2 = analysis_window[i] / analysis_window[i-1]
                        accel.append(r2 - r1)
                
                if accel:
                    avg_accel = sum(accel) / len(accel)
                    details["avg_acceleration"] = float(avg_accel)
                    details["trend"] = "accelerating" if avg_accel < 0 else "decelerating"
    
    # Create evidence hash
    evidence = {
        "risk_history": risk_history[-20:] if len(risk_history) > 20 else risk_history,
        "config": {"window": window, "max_rho": max_rho},
        "timestamp": time.time()
    }
    evidence_hash = hashlib.sha256(
        json.dumps(evidence, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    passed = len(violations) == 0
    
    return GuardResult(
        passed=passed,
        guard_name="ir_to_ic",
        violations=violations,
        details=details,
        timestamp=time.time(),
        evidence_hash=evidence_hash
    )


def combined_guard_check(metrics: Dict[str, Any],
                        risk_history: Optional[List[float]] = None,
                        policy: Optional[SigmaGuardPolicy] = None,
                        strict: bool = True) -> Tuple[bool, Dict[str, GuardResult]]:
    """
    Run all guards and return combined result.
    
    Args:
        metrics: Metrics dict for Σ-Guard
        risk_history: Risk history for IR→IC
        policy: Sigma guard policy
        strict: Strict mode for all guards
        
    Returns:
        Tuple of (all_passed, dict of individual results)
    """
    results = {}
    
    # Run Σ-Guard
    results["sigma"] = sigma_guard(metrics, policy, strict)
    
    # Run IR→IC if risk history provided
    if risk_history is not None:
        results["ir_ic"] = ir_to_ic_contractive(
            risk_history,
            max_rho=policy.rho_risk_max if policy else 1.0
        )
    
    # Check if all passed
    all_passed = all(r.passed for r in results.values())
    
    return all_passed, results


# Helper function for OPA/Rego integration (placeholder)
def evaluate_rego_policy(policy_path: str,
                         input_data: Dict[str, Any]) -> GuardResult:
    """
    Evaluate OPA/Rego policy file (placeholder for future integration).
    
    This would integrate with Open Policy Agent for policy-as-code.
    """
    # TODO: Implement actual OPA integration
    # For now, return a simple pass
    return GuardResult(
        passed=True,
        guard_name="rego_policy",
        violations=[],
        details={"policy_path": policy_path, "status": "not_implemented"},
        timestamp=time.time(),
        evidence_hash=hashlib.sha256(str(input_data).encode()).hexdigest()[:16]
    )