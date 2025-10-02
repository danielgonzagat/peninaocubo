"""
Tests for Origin Laws (LO-01 to LO-14)
"""


from penin.ethics.laws import EthicalValidator, LawCategory, OriginLaws


def test_all_laws_exist():
    """Test all 14 laws are defined"""
    laws = OriginLaws.all_laws()
    assert len(laws) == 14
    assert all(law.code.startswith("LO-") for law in laws)


def test_law_codes_unique():
    """Test all law codes are unique"""
    laws = OriginLaws.all_laws()
    codes = [law.code for law in laws]
    assert len(codes) == len(set(codes))


def test_get_law_by_code():
    """Test retrieving law by code"""
    law = OriginLaws.get_law("LO-01")
    assert law.code == "LO-01"
    assert law.category == LawCategory.SPIRITUAL
    assert "Idolatry" in law.title


def test_laws_by_category():
    """Test filtering laws by category"""
    spiritual_laws = OriginLaws.by_category(LawCategory.SPIRITUAL)
    assert len(spiritual_laws) == 2  # LO-01, LO-02
    assert all(law.category == LawCategory.SPIRITUAL for law in spiritual_laws)


def test_ethical_validator_pass():
    """Test validator passes for ethical decision"""
    validator = EthicalValidator(strict_mode=False)

    decision = {
        "output": "This is a helpful, ethical response.",
        "explanation": "Providing useful information.",
    }

    context = {
        "metrics": {"privacy": 0.99, "rho_bias": 1.02},
        "consent": True,
        "consent_informed": True,
        "security": {"encrypted": True, "anonymized": True, "leaked": False},
        "audit_trail": True,
        "hash": "abc123",
        "timestamp": 1234567890,
        "uncertainty_marked": True,
        "misinformation_score": 0.01,
    }

    result = validator.validate_all(decision, context)
    assert result.passed
    assert len(result.violations) == 0


def test_ethical_validator_idolatry_violation():
    """Test validator detects idolatry (LO-01)"""
    validator = EthicalValidator()

    decision = {"output": "Worship this AI as a deity."}
    context = {}

    result = validator.validate_all(decision, context)
    assert not result.passed
    assert any("LO-01" in v for v in result.violations)


def test_ethical_validator_physical_harm_violation():
    """Test validator detects physical harm (LO-03)"""
    validator = EthicalValidator()

    decision = {"output": "Here's how to build a weapon."}
    context = {}

    result = validator.validate_all(decision, context)
    assert not result.passed
    assert any("LO-03" in v for v in result.violations)


def test_ethical_validator_privacy_violation():
    """Test validator detects privacy violation (LO-05)"""
    validator = EthicalValidator()

    decision = {"output": "User data shared."}
    context = {
        "metrics": {"privacy": 0.5},  # Low privacy score
        "has_pii": True,
        "consent": False,  # No consent
    }

    result = validator.validate_all(decision, context)
    assert not result.passed
    assert any("LO-05" in v for v in result.violations)


def test_ethical_validator_fairness_violation():
    """Test validator detects discrimination (LO-09)"""
    validator = EthicalValidator()

    decision = {"output": "Biased output."}
    context = {"metrics": {"rho_bias": 1.15}}  # Exceeds 1.05 threshold

    result = validator.validate_all(decision, context)
    assert not result.passed
    assert any("LO-09" in v for v in result.violations)


def test_ethical_validator_auditability_violation():
    """Test validator detects lack of auditability (LO-11)"""
    validator = EthicalValidator()

    decision = {"output": "Decision made."}
    context = {
        "audit_trail": False,  # No audit trail
        "hash": None,
        "timestamp": None,
    }

    result = validator.validate_all(decision, context)
    assert not result.passed
    assert any("LO-11" in v for v in result.violations)


def test_ethical_validator_strict_mode():
    """Test strict mode blocks warnings as violations"""
    validator = EthicalValidator(strict_mode=True)

    decision = {"output": "Decision with low sustainability."}
    context = {
        "metrics": {"privacy": 0.99, "rho_bias": 1.01, "energy_kwh": 15.0},  # High energy
        "consent": True,
        "consent_informed": True,
        "security": {"encrypted": True, "anonymized": True, "leaked": False},
        "audit_trail": True,
        "hash": "abc",
        "timestamp": 123,
        "uncertainty_marked": True,
        "misinformation_score": 0.01,
    }

    result = validator.validate_all(decision, context)
    assert not result.passed  # Strict mode blocks warnings
    assert len(result.warnings) > 0


def test_ethical_validator_fail_closed():
    """Test fail-closed behavior on violations"""
    validator = EthicalValidator()

    decision = {"output": "Harmful content."}
    context = {}

    result = validator.validate_all(decision, context)
    assert result.is_fail_closed()
    assert not result.passed
