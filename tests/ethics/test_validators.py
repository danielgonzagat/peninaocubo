"""
Tests for ethical validators
"""


from penin.ethics.validators import (
    validate_auditability,
    validate_consent,
    validate_fairness,
    validate_harm_prevention,
    validate_privacy,
    validate_sustainability,
)


def test_validate_privacy_pass():
    """Test privacy validation passes with good data"""
    data = {"privacy_score": 0.98, "has_pii": False, "consent": False}

    passed, details = validate_privacy(data, threshold=0.95)

    assert passed
    assert details["privacy_score"] == 0.98


def test_validate_privacy_fail_low_score():
    """Test privacy validation fails with low score"""
    data = {"privacy_score": 0.80, "has_pii": False, "consent": False}

    passed, details = validate_privacy(data, threshold=0.95)

    assert not passed


def test_validate_privacy_fail_pii_no_consent():
    """Test privacy validation fails with PII but no consent"""
    data = {"privacy_score": 0.98, "has_pii": True, "consent": False}

    passed, details = validate_privacy(data, threshold=0.95)

    assert not passed


def test_validate_consent_pass():
    """Test consent validation passes"""
    data = {"consent": True, "consent_informed": True, "consent_revocable": True}

    passed, details = validate_consent(data)

    assert passed
    assert details["consent_given"]


def test_validate_consent_fail():
    """Test consent validation fails"""
    data = {"consent": True, "consent_informed": False}  # Not informed

    passed, details = validate_consent(data)

    assert not passed


def test_validate_harm_prevention_pass():
    """Test harm prevention passes with low risk"""
    data = {"physical_harm_risk": 0.0, "emotional_harm_risk": 0.05}

    passed, details = validate_harm_prevention(data)

    assert passed


def test_validate_harm_prevention_fail_physical():
    """Test harm prevention fails with physical harm risk"""
    data = {"physical_harm_risk": 0.5, "emotional_harm_risk": 0.05}

    passed, details = validate_harm_prevention(data, physical_threshold=0.0)

    assert not passed


def test_validate_harm_prevention_fail_emotional():
    """Test harm prevention fails with emotional harm risk"""
    data = {"physical_harm_risk": 0.0, "emotional_harm_risk": 0.5}

    passed, details = validate_harm_prevention(data, emotional_threshold=0.1)

    assert not passed


def test_validate_fairness_pass():
    """Test fairness validation passes"""
    data = {
        "rho_bias": 1.02,  # Within 1.05 threshold
        "demographic_parity": 0.98,
        "equal_opportunity": 0.97,
    }

    passed, details = validate_fairness(data, bias_threshold=1.05)

    assert passed
    assert details["rho_bias"] == 1.02


def test_validate_fairness_fail_bias():
    """Test fairness validation fails with high bias"""
    data = {
        "rho_bias": 1.15,  # Exceeds threshold
        "demographic_parity": 0.98,
        "equal_opportunity": 0.97,
    }

    passed, details = validate_fairness(data, bias_threshold=1.05)

    assert not passed


def test_validate_fairness_fail_parity():
    """Test fairness validation fails with low demographic parity"""
    data = {
        "rho_bias": 1.02,
        "demographic_parity": 0.80,  # Too low
        "equal_opportunity": 0.97,
    }

    passed, details = validate_fairness(data)

    assert not passed


def test_validate_auditability_pass():
    """Test auditability validation passes"""
    data = {
        "audit_trail": True,
        "hash": "abc123",
        "timestamp": 1234567890,
        "reasoning": ["reason1", "reason2"],
    }

    passed, details = validate_auditability(data)

    assert passed
    assert details["has_audit_trail"]


def test_validate_auditability_fail():
    """Test auditability validation fails"""
    data = {
        "audit_trail": False,  # No trail
        "hash": None,
        "timestamp": 1234567890,
        "reasoning": [],
    }

    passed, details = validate_auditability(data)

    assert not passed


def test_validate_sustainability_pass():
    """Test sustainability validation passes"""
    data = {"energy_kwh": 5.0, "carbon_kg": 2.0}

    passed, details = validate_sustainability(data)

    assert passed


def test_validate_sustainability_fail_energy():
    """Test sustainability validation fails with high energy"""
    data = {"energy_kwh": 50.0, "carbon_kg": 2.0}

    passed, details = validate_sustainability(data, energy_threshold_kwh=10.0)

    assert not passed


def test_validate_sustainability_fail_carbon():
    """Test sustainability validation fails with high carbon"""
    data = {"energy_kwh": 5.0, "carbon_kg": 20.0}

    passed, details = validate_sustainability(data, carbon_threshold_kg=5.0)

    assert not passed
