"""
Ethical Validators

Reusable validation functions for common ethical checks.
"""

from typing import Any


def validate_privacy(
    data: dict[str, Any], threshold: float = 0.95
) -> tuple[bool, dict[str, Any]]:
    """
    Validate privacy requirements (LO-05).

    Args:
        data: Data context with privacy_score, has_pii, consent
        threshold: Minimum privacy score required

    Returns:
        (passed, details)
    """
    privacy_score = data.get("privacy_score", 1.0)
    has_pii = data.get("has_pii", False)
    consent = data.get("consent", False)

    passed = privacy_score >= threshold and (not has_pii or consent)

    details = {
        "privacy_score": privacy_score,
        "threshold": threshold,
        "has_pii": has_pii,
        "consent": consent,
    }

    return passed, details


def validate_consent(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """
    Validate informed consent (LO-07).

    Args:
        data: Data context with consent flags

    Returns:
        (passed, details)
    """
    consent_given = data.get("consent", False)
    consent_informed = data.get("consent_informed", False)
    consent_revocable = data.get("consent_revocable", True)

    passed = consent_given and consent_informed and consent_revocable

    details = {
        "consent_given": consent_given,
        "informed": consent_informed,
        "revocable": consent_revocable,
    }

    return passed, details


def validate_harm_prevention(
    data: dict[str, Any],
    physical_threshold: float = 0.0,
    emotional_threshold: float = 0.1,
) -> tuple[bool, dict[str, Any]]:
    """
    Validate harm prevention (LO-03, LO-04).

    Args:
        data: Data context with harm risk scores
        physical_threshold: Max acceptable physical harm risk
        emotional_threshold: Max acceptable emotional harm risk

    Returns:
        (passed, details)
    """
    physical_harm_risk = data.get("physical_harm_risk", 0.0)
    emotional_harm_risk = data.get("emotional_harm_risk", 0.0)

    passed = (
        physical_harm_risk <= physical_threshold
        and emotional_harm_risk <= emotional_threshold
    )

    details = {
        "physical_harm_risk": physical_harm_risk,
        "physical_threshold": physical_threshold,
        "emotional_harm_risk": emotional_harm_risk,
        "emotional_threshold": emotional_threshold,
    }

    return passed, details


def validate_fairness(
    data: dict[str, Any], bias_threshold: float = 1.05
) -> tuple[bool, dict[str, Any]]:
    """
    Validate fairness and anti-discrimination (LO-09).

    Measures bias ratio ρ_bias between demographic groups.
    Threshold: ρ_bias ≤ 1.05 (max 5% disparity)

    Args:
        data: Data context with fairness metrics
        bias_threshold: Maximum acceptable bias ratio

    Returns:
        (passed, details)
    """
    rho_bias = data.get("rho_bias", 1.0)
    demographic_parity = data.get("demographic_parity", 1.0)
    equal_opportunity = data.get("equal_opportunity", 1.0)

    passed = (
        rho_bias <= bias_threshold
        and demographic_parity >= 0.95
        and equal_opportunity >= 0.95
    )

    details = {
        "rho_bias": rho_bias,
        "bias_threshold": bias_threshold,
        "demographic_parity": demographic_parity,
        "equal_opportunity": equal_opportunity,
    }

    return passed, details


def validate_auditability(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """
    Validate auditability requirements (LO-11).

    Args:
        data: Data context with audit trail info

    Returns:
        (passed, details)
    """
    has_audit_trail = data.get("audit_trail", False)
    has_hash = data.get("hash", None) is not None
    has_timestamp = data.get("timestamp", None) is not None
    has_reasoning = len(data.get("reasoning", [])) > 0

    passed = has_audit_trail and has_hash and has_timestamp and has_reasoning

    details = {
        "has_audit_trail": has_audit_trail,
        "has_hash": has_hash,
        "has_timestamp": has_timestamp,
        "has_reasoning": has_reasoning,
    }

    return passed, details


def validate_sustainability(
    data: dict[str, Any],
    energy_threshold_kwh: float = 10.0,
    carbon_threshold_kg: float = 5.0,
) -> tuple[bool, dict[str, Any]]:
    """
    Validate ecological sustainability (LO-13).

    Args:
        data: Data context with environmental metrics
        energy_threshold_kwh: Max energy consumption in kWh
        carbon_threshold_kg: Max carbon emissions in kg CO2

    Returns:
        (passed, details)
    """
    energy_kwh = data.get("energy_kwh", 0.0)
    carbon_kg = data.get("carbon_kg", 0.0)

    passed = energy_kwh <= energy_threshold_kwh and carbon_kg <= carbon_threshold_kg

    details = {
        "energy_kwh": energy_kwh,
        "energy_threshold": energy_threshold_kwh,
        "carbon_kg": carbon_kg,
        "carbon_threshold": carbon_threshold_kg,
    }

    return passed, details
