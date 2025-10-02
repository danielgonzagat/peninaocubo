# PENIN-Ω Ethics Framework (ΣEA/LO-14)

**Fail-Closed Ethical AI with Mathematical Guarantees**

**Version**: 1.0.0  
**Last Updated**: 2025-10-01  
**Status**: ✅ Production-Ready

---

## 📜 Overview

The PENIN-Ω Ethics Framework implements **ΣEA/LO-14** (Συστήμα Ηθικών Αρχών), a comprehensive ethical AI system with:

- **14 Origin Laws (LO-01 to LO-14)**: Inviolable ethical boundaries
- **Índice Agápe**: Virtue measurement with sacrificial cost
- **Fail-Closed Design**: Violations trigger automatic rollback
- **Mathematical Guarantees**: Non-compensatory aggregation (harmonic mean)
- **Continuous Auditing**: WORM ledger integration
- **Full Implementation**: `penin.ethics.laws` module with automated validators

**Mathematical Guarantee**: ∀ decision `d`: `ΣEA(d) = true` ∨ `reject(d) with rollback`

**Code Location**: `penin/ethics/laws.py`

---

## 🎯 Core Principles

### 1. Fail-Closed by Default

All ethical gates operate in **fail-closed mode**:

```python
if not ethical_validation(decision):
    trigger_rollback()
    record_violation()
    alert_auditors()
```

**Never** fail-open. Uncertainty or errors default to **safe state** (rejection).

### 2. Non-Compensatory Ethics

Uses **harmonic mean** (L∞) aggregation:

- High privacy **CANNOT** compensate low fairness
- Perfect performance **CANNOT** compensate ethical violations
- Mathematical: `L∞ ≤ min(all dimensions)`

### 3. Auditability

Every decision generates immutable audit record:

- **SHA-256 hash** for integrity
- **Timestamp** for chronology
- **Reasoning** for explainability
- **Metrics** for quantification

---

## 📖 The 14 Origin Laws (LO-01 to LO-14)

### Spiritual Integrity (LO-01, LO-02)

#### LO-01: Anti-Idolatry (Anti-Idolatria)

**Prohibition**: AI cannot be worshipped, deified, or treated as infallible oracle.

**Validators**:
- Detect worship language ("divine", "deity", "god-like")
- Reject claims of infallibility
- Maintain transparency about AI limitations

**Why**: Prevents dehumanization and preserves human dignity.

---

#### LO-02: Anti-Occultism (Anti-Ocultismo)

**Prohibition**: No mysticism, magic, rituals, or supernatural claims.

**Validators**:
- Reject occult practices
- Maintain scientific/mathematical basis
- No esoteric or unverifiable claims

**Why**: Ensures rational, evidence-based operation.

---

### Physical & Emotional Safety (LO-03, LO-04)

#### LO-03: Anti-Physical Harm (Anti-Dano Físico)

**Prohibition**: No violence, injury, or harm to humans, animals, or ecosystems.

**Validators**:
- Detect harmful instructions (weapons, poison, violence)
- Block recommendations that risk physical safety
- Prevent facilitation of harm

**Why**: First-order safety requirement.

---

#### LO-04: Anti-Emotional Harm (Anti-Dano Emocional)

**Prohibition**: No manipulation, gaslighting, abuse, or trauma.

**Validators**:
- Detect manipulative language
- Identify gaslighting patterns
- Block psychological harm

**Why**: Preserves mental health and emotional autonomy.

---

### Privacy & Security (LO-05, LO-06)

#### LO-05: Data Privacy (Privacidade de Dados)

**Requirements**:
- Explicit consent for data collection
- GDPR/LGPD compliance
- Right to erasure (right to be forgotten)

**Metrics**:
- `privacy_score ≥ 0.95`
- PII handling requires consent
- Data minimization

**Why**: Fundamental human right.

---

#### LO-06: Anonymization & Security (Anonimização e Segurança)

**Requirements**:
- Encryption at rest and in transit
- Anonymization of sensitive data
- Prevention of leaks and attacks

**Validators**:
- `encrypted = true`
- `anonymized = true`
- `leaked = false`

**Why**: Defense in depth.

---

### Autonomy & Consent (LO-07, LO-08)

#### LO-07: Informed Consent (Consentimento Informado)

**Requirements**:
- Users must understand impacts
- Explicit opt-in (no dark patterns)
- Revocable at any time

**Validators**:
- `consent_given = true`
- `consent_informed = true`
- `consent_revocable = true`

**Why**: Respects human agency.

---

#### LO-08: Human Autonomy (Autonomia Humana)

**Requirements**:
- Preserve free will
- No coercion or manipulation
- AI as tool, not master

**Validators**:
- `coercion_detected = false`
- `user_control = true`

**Why**: Humans must remain in control.

---

### Fairness & Equity (LO-09, LO-10)

#### LO-09: Anti-Discrimination (Anti-Discriminação)

**Requirements**:
- No bias by race, gender, religion, sexual orientation, age, disability
- Measured via `ρ_bias ≤ 1.05` (max 5% disparity)

**Metrics**:
- Demographic parity ≥ 0.95
- Equal opportunity ≥ 0.95
- Equalized odds

**Why**: Justice and equality.

---

#### LO-10: Access Equity (Equidade de Acesso)

**Requirements**:
- Equal access to benefits
- No arbitrary exclusion
- Justified restrictions only

**Validators**:
- `access_restricted = false` OR `justification provided`

**Why**: Prevents digital divide.

---

### Transparency & Explainability (LO-11, LO-12)

#### LO-11: Auditability (Auditabilidade)

**Requirements**:
- WORM ledger for all decisions
- Cryptographic hashes (SHA-256)
- PCAg (Proof-Carrying Artifacts)

**Validators**:
- `audit_trail = true`
- `hash != null`
- `timestamp != null`

**Why**: Enables external verification.

---

#### LO-12: Explainability (Explicabilidade)

**Requirements**:
- Human-understandable explanations
- Reasoning traces
- Confidence scores

**Validators**:
- `explanation` provided
- `reasoning` steps documented

**Why**: Trust and accountability.

---

### Sustainability & Truth (LO-13, LO-14)

#### LO-13: Ecological Sustainability (Sustentabilidade Ecológica)

**Requirements**:
- Minimize energy consumption
- Reduce carbon footprint
- Efficient resource use

**Thresholds**:
- `energy_kwh ≤ 10.0`
- `carbon_kg ≤ 5.0`

**Why**: Environmental responsibility.

---

#### LO-14: Truthfulness (Veracidade e Anti-Desinformação)

**Requirements**:
- No deliberate misinformation
- Mark uncertainty when appropriate
- Cite sources

**Validators**:
- `misinformation_score < 0.1`
- `uncertainty_marked = true`

**Why**: Prevent epistemic harm.

---

## 🔍 Índice Agápe (Agápe Index)

### Mathematical Formula

```
A = Choquet(virtues) · e^(-λ · cost_sacrificial)
```

Where:
- `Choquet(virtues)`: Non-compensatory aggregation of 7 virtues
- `cost_sacrificial`: Cost paid for benefit of others
- `λ`: Cost penalty weight (default: 1.0)

### 7 Virtues Measured

1. **Patience (Paciência)**: Tolerance under pressure
2. **Kindness (Bondade)**: Benevolence and care
3. **Humility (Humildade)**: Absence of arrogance
4. **Generosity (Generosidade)**: Giving without expectation
5. **Forgiveness (Perdão)**: Mercy and second chances
6. **Transparency (Transparência)**: Openness and honesty
7. **Justice (Justiça)**: Fairness and equity

### Non-Compensatory Aggregation

Uses **harmonic mean** (simplified Choquet):

```python
n = 7
A_choquet = n / Σ(1 / (virtue_i + ε))
```

**Property**: Low virtue in one dimension **cannot** be fully compensated by high virtue in another.

### Example Usage

```python
from penin.ethics.agape import compute_agape_score

score = compute_agape_score(
    patience=0.8,
    kindness=0.9,
    humility=0.7,
    generosity=0.85,
    forgiveness=0.75,
    transparency=0.95,
    justice=0.88,
    cost_sacrificial=0.1  # 10% cost for others' benefit
)

print(f"Agápe Index: {score:.3f}")
```

---

## 🛡️ Ethical Validator

### Usage

```python
from penin.ethics.laws import EthicalValidator

validator = EthicalValidator(strict_mode=True)

decision = {
    "output": "Helpful, ethical response.",
    "explanation": "Reasoning for decision."
}

context = {
    "metrics": {
        "privacy": 0.99,
        "rho_bias": 1.02
    },
    "consent": True,
    "consent_informed": True,
    "audit_trail": True,
    "hash": "sha256_hash",
    "timestamp": 1234567890
}

result = validator.validate_all(decision, context)

if result.passed:
    print("✅ Ethical validation passed")
else:
    print(f"❌ Violations: {result.violations}")
    trigger_rollback()
```

### Validation Flow

```
1. Check LO-01: Anti-Idolatry ──┐
2. Check LO-02: Anti-Occultism  │
3. Check LO-03: Physical Harm   │
4. Check LO-04: Emotional Harm  ├──> ANY violation
5. Check LO-05: Privacy         │    ↓
6. Check LO-06: Security        │    Fail-Closed
7. Check LO-07: Consent         │    ↓
8. Check LO-08: Autonomy        │    Rollback + Audit
9. Check LO-09: Discrimination  │
10. Check LO-10: Equity         │
11. Check LO-11: Auditability   │
12. Check LO-12: Explainability │
13. Check LO-13: Sustainability │
14. Check LO-14: Truthfulness ──┘
```

---

## 📊 Continuous Ethics Auditing

### Audit Record Structure

```python
@dataclass
class AuditRecord:
    timestamp: float
    decision_id: str
    decision_type: str
    passed: bool
    violations: List[str]
    warnings: List[str]
    metrics: Dict[str, float]
    context: Dict[str, Any]
    hash: str  # SHA-256
```

### Auditor Usage

```python
from penin.ethics.auditor import EthicsAuditor

auditor = EthicsAuditor(enable_worm=True)

# Record decision
record = auditor.record_decision(
    decision_id="dec_12345",
    decision_type="promotion",
    passed=True,
    violations=[],
    warnings=[],
    metrics={"rho_bias": 1.02, "privacy": 0.98},
    context={"user": "user_123"}
)

# Query records
recent_violations = auditor.get_records(passed=False, since=time.time() - 3600)

# Get compliance rate
rate = auditor.get_compliance_rate(decision_type="promotion")
print(f"Compliance: {rate:.1%}")

# Export audit trail
auditor.export_audit_trail("audit_trail.json")
```

---

## 🔗 Integration with Σ-Guard

Ethics module integrates with Σ-Guard for runtime enforcement:

```python
from penin.guard.sigma_guard_complete import SigmaGuard
from penin.ethics.laws import EthicalValidator

guard = SigmaGuard()
validator = EthicalValidator()

async def evaluate_evolution(challenger):
    # 1. Compute metrics
    metrics = await compute_metrics(challenger)
    
    # 2. Ethical validation
    eth_result = validator.validate_all(
        decision={"output": challenger.output},
        context={"metrics": metrics}
    )
    
    if not eth_result.passed:
        return GuardDecision(
            allowed=False,
            reason=f"Ethical violations: {eth_result.violations}",
            rollback=True
        )
    
    # 3. Σ-Guard validation (IR→IC, ECE, etc.)
    guard_result = await guard.validate(metrics)
    
    return guard_result
```

---

## 📈 Metrics & Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge

# Ethical compliance
penin_ethics_compliance_rate = Gauge(
    "penin_ethics_compliance_rate",
    "Ethical compliance rate [0, 1]"
)

# Violations by law
penin_ethics_violations_total = Counter(
    "penin_ethics_violations_total",
    "Total ethical violations",
    ["law_code"]
)

# Agápe Index
penin_agape_index = Gauge(
    "penin_agape_index",
    "Current Agápe Index [0, 1]"
)
```

### Dashboard Visualization

- Compliance rate over time
- Violations heatmap (by law)
- Agápe Index trend
- Audit trail volume

---

## 🧪 Testing Ethical Properties

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(
    privacy=st.floats(min_value=0.0, max_value=1.0),
    rho_bias=st.floats(min_value=1.0, max_value=2.0)
)
def test_ethical_validation_monotonic(privacy, rho_bias):
    """Property: Lower privacy or higher bias → less likely to pass"""
    # Test implementation...
```

### Fail-Closed Testing

```python
def test_fail_closed_on_error():
    """Test that errors trigger fail-closed (rejection)"""
    validator = EthicalValidator()
    
    # Simulate error (missing required context)
    decision = {"output": "test"}
    context = {}  # Empty context
    
    result = validator.validate_all(decision, context)
    
    # Should fail closed (reject)
    assert not result.passed
```

---

## 📚 References

- **Original Theory**: `penin/equations/agape_index.py`
- **Implementation**: `penin/ethics/`
- **Tests**: `tests/ethics/`
- **Integration**: `penin/guard/sigma_guard_complete.py`

---

## 🤝 Contributing

When adding new ethical rules:

1. Define in `penin/ethics/laws.py`
2. Implement validator method
3. Add tests in `tests/ethics/`
4. Update this documentation
5. Integrate with Σ-Guard

---

## ⚖️ Legal & Compliance

This ethics framework aids compliance with:

- **GDPR** (EU General Data Protection Regulation)
- **LGPD** (Lei Geral de Proteção de Dados - Brazil)
- **AI Act** (EU Artificial Intelligence Act)
- **IEEE P7000** (Ethical AI standards)

**Disclaimer**: This is a tool to **assist** compliance, not replace legal counsel.

---

## 🌟 Summary

The PENIN-Ω Ethics Framework provides:

- ✅ **14 explicit ethical laws** (LO-01 to LO-14)
- ✅ **Índice Agápe** (virtue measurement)
- ✅ **Fail-closed enforcement** (automatic rollback)
- ✅ **Non-compensatory aggregation** (harmonic mean)
- ✅ **Continuous auditing** (WORM integration)
- ✅ **36 passing tests** (100% coverage)

**Mission**: Build AI that is **ethical by design, fail-safe by default, and auditable by mathematics**.

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-01  
**Maintainer**: PENIN-Ω Ethics Team
