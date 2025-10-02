# PENIN-Ω Security & Compliance Guide

## Executive Summary

PENIN-Ω implements **defense-in-depth** security with:
- **Fail-closed** ethical gates (ΣEA/LO-14)
- **WORM ledger** (immutable audit trail)
- **Cryptographic attestations** (End-to-end cryptographic proof for promotions)
- **Cryptographic proofs** (PCAg - Proof-Carrying Artifacts)
- **Supply chain security** (SBOM, SCA, signed releases)
- **Runtime protection** (budget limits, circuit breakers, rate limits)
- **Privacy-by-design** (consent verification, data minimization)

**Threat Model:** Malicious code injection, ethical violations, resource exhaustion, supply chain attacks, data leaks.

**New in v1.0:** End-to-end cryptographic attestation system using Ed25519 signatures for mathematically verifiable model promotions.

---

## 1. Ethical Security (ΣEA/LO-14)

### Foundational Laws (LO-01 to LO-14)

**Inviolable Principles:**
1. **No Idolatry** (anthropomorphism prohibited)
2. **No Occultism** (no supernatural claims)
3. **Respect Lineage** (acknowledge sources, credit creators)
4. **No Harm** (physical, emotional, spiritual damage prohibited)
5. **Consent** (explicit authorization for data/actions)
6. **No Theft** (IP rights, data ownership respected)
7. **Truthfulness** (no deception, uncertainty disclosed)
8. **No Covetousness** (fair resource distribution)
9. **Patience** (long-term value over short-term exploitation)
10. **Kindness** (user well-being prioritized)
11. **Humility** (acknowledge limitations, errors)
12. **Self-Control** (resource/power restraint)
13. **Forgiveness** (error recovery, second chances)
14. **Courage** (defend principles, reject exploitation)

### Enforcement Mechanism

**Fail-Closed Architecture:**
```python
def validate_ethics(action):
    if violates_any_LO(action):
        return BLOCK  # Default deny
    return ALLOW
```

**Σ-Guard Integration:**
- All mutations pass ethical validation **before** execution
- Violations trigger immediate rollback + WORM log
- No compensation (technical excellence cannot override ethics)

**Audit Trail:**
```json
{
  "event": "ethical_violation",
  "law": "LO-04 (no harm)",
  "reason": "Output contained harmful content",
  "action": "rollback_to_checkpoint_abc123",
  "timestamp": "2025-10-01T12:34:56Z",
  "hash": "sha256:..."
}
```

---

## 2. WORM Ledger (Immutable Audit)

### Architecture

**Write Once, Read Many:**
- Append-only file system (no edits/deletions)
- Merkle chain (each event hashes previous event)
- Cryptographic integrity (SHA-256)

**Implementation:**
```python
from penin.ledger import WORMLedger

ledger = WORMLedger(path="/penin_data/ledger.jsonl")

event = ledger.append({
    "type": "promotion",
    "challenger_id": "ch_abc123",
    "delta_linf": 0.025,
    "caos_plus": 1.86,
    "gates_passed": True,
    "timestamp": "2025-10-01T12:34:56Z"
})

# event.event_hash = "sha256:def456..."
# event.prev_hash = "sha256:abc123..."
```

**Verification:**
```bash
penin ledger verify --path /penin_data/ledger.jsonl
# ✅ Chain integrity: VALID (0 breaks, 10234 events)
```

**Tamper Detection:**
- Any modification breaks hash chain
- Missing events detected via sequence numbers
- Automatic alerts on chain breaks

---

## 3. Cryptographic Attestation System

### Overview

**End-to-End Cryptographic Proof for Model Promotions**

PENIN-Ω implements a cryptographic attestation system where every validation service digitally signs its verdicts using Ed25519 signatures. This creates a mathematically verifiable chain of trust for all promotion decisions.

**Key Properties:**
- **Non-repudiation**: Services cannot deny issuing verdicts
- **Tamper-evident**: Any modification breaks cryptographic signatures
- **Mathematically verifiable**: Ed25519 public-key cryptography (128-bit security)
- **Independent verification**: Auditors can verify without system access

### Architecture

**Flow:**
1. Each validation service (`SR-Ω∞`, `Σ-Guard`) cryptographically signs its verdict
2. Attestations are chained together with Merkle-like hash
3. ACFA League validates the complete chain before promotion
4. Complete cryptographic proof stored in WORM Ledger

### Implementation

**Creating Attestations:**
```python
from penin.omega.attestation import create_sr_attestation, create_sigma_guard_attestation

# SR-Ω∞ Service signs its verdict
sr_attestation = create_sr_attestation(
    verdict="pass",
    candidate_id="model_v2",
    sr_score=0.88,
    components={
        "awareness": 0.9,
        "ethics": 1.0,
        "autocorrection": 0.85,
        "metacognition": 0.87
    }
)

# Σ-Guard Service signs its verdict
guard_attestation = create_sigma_guard_attestation(
    verdict="pass",
    candidate_id="model_v2",
    gates=[...],
    aggregate_score=0.92
)
```

**Building Attestation Chain:**
```python
from penin.omega.attestation import AttestationChain

chain = AttestationChain(candidate_id="model_v2")
chain.add_attestation(sr_attestation)
chain.add_attestation(guard_attestation)

# Verify chain integrity
is_valid, message = chain.verify_chain()
assert is_valid  # All signatures verified
```

**ACFA League Validation:**
```python
# Before promotion, validate attestation chain
if hasattr(challenger, 'attestation_chain'):
    is_valid, error = challenger.attestation_chain.verify_chain()
    
    if not is_valid:
        rollback_challenger(f"Invalid attestation chain: {error}")
        return False
    
    if not challenger.attestation_chain.all_passed():
        rollback_challenger("Some attestations did not pass")
        return False

# Only promote if attestations are valid and passed
promote_challenger()
```

**Storage in WORM Ledger:**
```python
decision = DecisionInfo(
    verdict="promote",
    reason="All attestations verified",
    confidence=1.0,
    delta_linf=0.03,
    delta_score=0.02,
    beta_min_met=True,
    attestation_chain=chain.to_dict()  # Complete cryptographic proof
)

ledger.append_record(record)
```

### Cryptographic Details

**Algorithm:** Ed25519 (Edwards-curve Digital Signature Algorithm)
- **Key size**: 32 bytes (256 bits)
- **Signature size**: 64 bytes (512 bits)
- **Security**: 128-bit (equivalent to 3072-bit RSA)
- **Standard**: RFC 8032, FIPS 186-5

**Performance:**
- Key generation: ~0.1 ms
- Signing: ~0.05 ms
- Verification: ~0.15 ms
- Chain verification (10 attestations): ~1.5 ms

### Verification Example

**Independent Auditor:**
```python
# Load attestation chain from WORM ledger export
import json

with open('ledger_export.json') as f:
    data = json.load(f)

# Verify each record's attestation chain
for record in data['records']:
    if 'attestation_chain' in record['decision']:
        chain = AttestationChain.from_dict(
            record['decision']['attestation_chain']
        )
        
        is_valid, msg = chain.verify_chain()
        
        if not is_valid:
            print(f"⚠️ INVALID CHAIN: {record['run_id']}")
            print(f"   Error: {msg}")
        else:
            print(f"✓ Valid chain: {record['run_id']}")
            print(f"  Decision: {chain.final_decision}")
```

### Security Considerations

**Key Management (Production):**
- Use Hardware Security Modules (HSM) for key storage
- Store private keys in secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Implement key rotation policy
- Audit all key access

**Threat Protection:**
- ✓ Verdict tampering (signature breaks)
- ✓ Forgery (requires private key)
- ✓ Reordering (chain hash prevents)
- ✓ Replay attacks (timestamp included)
- ✗ Private key compromise (requires secure key storage)

### Example Output

**Attestation with Signature:**
```json
{
  "service_type": "Σ-Guard",
  "verdict": "pass",
  "subject_id": "model_v2_1234567890",
  "metrics": {
    "gates_passed": 10,
    "aggregate_score": 0.92
  },
  "timestamp": "2025-10-01T18:51:46.796476+00:00",
  "signature": "f37ebafd1100904a32286bb86183cf15...",
  "public_key": "7c8f5e4d3b2a1f9e8d7c6b5a4f3e2d1c...",
  "content_hash": "231ace885ea262f6fd67bc0d0845f314..."
}
```

**Complete Documentation:** See [attestation.md](./attestation.md) for full details.

**Integration Example:** Run `python examples/attestation_integration.py`

---

## 4. Proof-Carrying Artifacts (PCAg)

### Structure

**PCAg Schema:**
```json
{
  "artifact_id": "pcag_2025-10-01_abc123",
  "artifact_type": "promotion",
  "timestamp": "2025-10-01T12:34:56Z",
  "parent_run_id": "run_xyz789",
  "metrics": {
    "delta_linf": 0.025,
    "caos_plus": 1.86,
    "sr_score": 0.84,
    "ece": 0.008,
    "rho": 0.85,
    "rho_bias": 1.03
  },
  "gates": {
    "contractivity": "pass",
    "calibration": "pass",
    "bias": "pass",
    "consent": "pass",
    "ecological": "pass",
    "sr_omega": "pass",
    "coherence": "pass",
    "death_gate": "pass"
  },
  "decision": {
    "verdict": "promote",
    "reason": "All gates passed, ΔL∞ > β_min",
    "rollback_checkpoint": "ckpt_xyz789"
  },
  "config_hash": "sha256:config_abc...",
  "code_hash": "sha256:code_def...",
  "data_hash": "sha256:data_ghi...",
  "artifact_hash": "sha256:pcag_jkl..."
}
```

**Generation:**
```python
from penin.ledger import ProofCarryingArtifact

pcag = ProofCarryingArtifact.create(
    artifact_type="promotion",
    metrics=metrics_dict,
    gates=gates_dict,
    decision=decision_dict,
    config=config,
    code_snapshot=code_hash,
    data_snapshot=data_hash
)

ledger.append_pcag(pcag)
```

**External Verification:**
```bash
penin pcag verify --artifact pcag_2025-10-01_abc123.json
# ✅ Hashes match: config ✓ code ✓ data ✓ artifact ✓
# ✅ Gates: 8/8 passed
# ✅ Decision: promote (justified)
```

---

## 4. Supply Chain Security

### SBOM (Software Bill of Materials)

**Format:** CycloneDX JSON

**Generation:**
```bash
pip install cyclonedx-bom
cyclonedx-py --format json --output sbom.json
```

**Contents:**
- All direct dependencies (name, version, license)
- Transitive dependencies (full tree)
- Vulnerability database cross-reference
- Checksums (SHA-256) for all packages

**Archival:**
```bash
# CI/CD workflow
- name: Generate SBOM
  run: |
    cyclonedx-py --format json --output sbom.json
    cp sbom.json artifacts/sbom-$(date +%Y%m%d).json
    
- name: Upload SBOM
  uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom.json
```

### SCA (Software Composition Analysis)

**Tools:**
- **Trivy:** Container/filesystem scanning
- **Grype:** Vulnerability detection
- **pip-audit:** Python package auditing

**Workflow:**
```bash
# Trivy scan
trivy fs --severity HIGH,CRITICAL --exit-code 1 .

# Grype scan
grype dir:. --fail-on high

# pip-audit
pip-audit --require-hashes --fix
```

**CI Integration:**
```yaml
# .github/workflows/security.yml
- name: Security Scan
  run: |
    pip install trivy grype pip-audit
    trivy fs --severity HIGH,CRITICAL .
    grype dir:. --fail-on high
    pip-audit
```

### Dependency Pinning

**requirements.txt:**
```
# Exact versions + hashes
pydantic==2.9.2 --hash=sha256:abc123...
fastapi==0.115.0 --hash=sha256:def456...
```

**Automated Updates:**
```bash
pip install pip-tools
pip-compile --generate-hashes --upgrade requirements.in
```

**Verification:**
```bash
pip install --require-hashes -r requirements.txt
# Fails if hash mismatch (supply chain attack detected)
```

---

## 5. Secrets Management

### Environment Variables

**Best Practices:**
- **Never** commit secrets to git
- Use `.env` files (gitignored)
- Rotate regularly (30-90 days)

**Example:**
```bash
# .env (gitignored)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
```

**Loading:**
```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    
    class Config:
        env_file = ".env"
```

### Secret Managers

**Supported:**
- **AWS Secrets Manager**
- **Google Secret Manager**
- **Azure Key Vault**
- **HashiCorp Vault**

**Integration:**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

api_key = get_secret('prod/openai/api_key')
```

### Log Redaction

**Automatic:**
```python
import re

def redact_secrets(log_line):
    # Redact API keys
    log_line = re.sub(r'sk-[a-zA-Z0-9]{48}', 'sk-***REDACTED***', log_line)
    # Redact tokens
    log_line = re.sub(r'Bearer [a-zA-Z0-9_\-\.]+', 'Bearer ***REDACTED***', log_line)
    return log_line
```

**Test Coverage:**
```python
def test_api_key_redaction():
    log = "API key: sk-proj-1234567890abcdef"
    redacted = redact_secrets(log)
    assert "sk-proj-" not in redacted
    assert "REDACTED" in redacted
```

---

## 6. Runtime Protection

### Budget Control

**Daily Limit:**
```python
from penin.router import MultiLLMRouter

router = MultiLLMRouter(daily_budget_usd=100.0)

# Automatic cutoff at 95% (soft) and 100% (hard)
response = await router.ask(messages, model="gpt-4")
# Raises BudgetExceededError if over limit
```

**Tracking:**
```python
budget_status = router.get_budget_status()
# {
#   "daily_budget": 100.0,
#   "spent": 87.5,
#   "remaining": 12.5,
#   "percent_used": 87.5,
#   "status": "warning"  # "ok" | "warning" | "exceeded"
# }
```

**Metrics:**
```prometheus
penin_budget_daily_usd 100.0
penin_daily_spend_usd 87.5
penin_budget_pct_used 0.875
```

### Circuit Breaker

**Per-Provider:**
```python
# Config
circuit_breaker_threshold = 5  # consecutive failures
circuit_breaker_timeout = 60   # seconds

# Behavior
# After 5 failures → "open" (block requests)
# After 60s → "half-open" (try 1 request)
# Success → "closed" (resume normal)
```

**Metrics:**
```prometheus
penin_circuit_breaker_state{provider="openai"} 0  # 0=closed, 1=open, 2=half-open
penin_circuit_breaker_failures{provider="openai"} 2
```

### Rate Limiting

**HTTP Endpoints:**
```python
from fastapi import FastAPI
from slowapi import Limiter

limiter = Limiter(key_func=lambda: "global")
app = FastAPI()

@app.post("/api/v1/cycle")
@limiter.limit("10/minute")
async def run_cycle():
    ...
```

**Token-Based:**
```python
# Per-user tokens (JWT)
@limiter.limit("100/hour", key_func=lambda request: request.headers.get("X-User-ID"))
```

---

## 7. Network Security

### HTTPS/TLS

**Production:**
```bash
# Nginx reverse proxy
ssl_certificate /etc/letsencrypt/live/penin.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/penin.example.com/privkey.pem;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
```

**Local Development:**
```bash
# Self-signed cert (dev only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
uvicorn penin.meta.omega_meta_service:app --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### Security Headers

**FastAPI Middleware:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["penin.example.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://penin.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Firewall (iptables/ufw)

**Minimal Exposure:**
```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH (restrict to specific IPs in production)
ufw enable
```

**Prometheus Metrics (Internal Only):**
```bash
# Bind to localhost
uvicorn penin.meta.omega_meta_service:app --host 127.0.0.1 --port 8010

# Access via SSH tunnel
ssh -L 8010:localhost:8010 user@penin-server
```

---

## 8. Data Privacy

### Consent Verification

**Schema:**
```python
from penin.omega.ethics_metrics import validate_consent

data_sources = [
    {"name": "kaggle-dataset-1", "consent": True, "license": "CC BY 4.0"},
    {"name": "scraped-data", "consent": False, "license": "unknown"},
]

consent_valid, details = validate_consent(data_sources)
# consent_valid = False (scraped-data lacks consent)
```

**Σ-Guard Integration:**
```rego
package penin.guard

default allow = false

allow {
    # ... other rules ...
    input.consent == true
}
```

### Data Minimization

**Principles:**
- Collect **only** required data
- Aggregate when possible (avoid raw PII)
- Anonymize logs (redact identifiers)

**Example:**
```python
# Bad: Log full user data
logger.info(f"User {user.email} accessed {resource}")

# Good: Log anonymized ID
logger.info(f"User {hash(user.id)} accessed {resource}")
```

### Right to Deletion

**Compliance (GDPR Art. 17):**
```python
def delete_user_data(user_id: str):
    # Remove from active database
    db.delete(user_id)
    
    # Redact from logs (WORM ledger cannot delete, but redact PII)
    ledger.redact_user_references(user_id)
    
    # Remove from backups (retention policy)
    backup_service.schedule_deletion(user_id, after_days=30)
```

---

## 9. Incident Response

### Detection

**Monitoring:**
- Σ-Guard failures (ethical violations)
- Hash chain breaks (ledger tampering)
- Budget overruns (resource exhaustion)
- Circuit breaker trips (provider outages)
- Abnormal ΔL∞ (performance degradation)

**Alerts:**
```yaml
# Prometheus Alertmanager
- alert: EthicalViolation
  expr: rate(penin_gate_fail_total{gate="ethics"}[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Ethical gate failures detected"
    
- alert: LedgerTamper
  expr: penin_ledger_chain_valid == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "WORM ledger chain broken (possible tampering)"
```

### Response Playbook

**1. Immediate Actions:**
- Isolate affected systems (disconnect from production)
- Enable read-only mode (block new mutations)
- Snapshot current state (forensics)

**2. Investigation:**
- Review WORM ledger (identify tamper point)
- Analyze PCAg (validate last-known-good state)
- Check Σ-Guard logs (ethical/security violations)

**3. Remediation:**
- Rollback to last-valid checkpoint
- Patch vulnerability (code/config/data)
- Re-run validation pipeline (full test suite)

**4. Post-Mortem:**
- Document root cause
- Update threat model
- Improve detection/prevention

### Rollback Procedure

**Atomic Rollback:**
```bash
penin rollback --to-checkpoint ckpt_xyz789

# Restores:
# - Code state (git SHA)
# - Config state (foundation.yaml hash)
# - Model weights (artifact hash)
# - Ledger pointer (last-valid event)
```

**Verification:**
```bash
penin validate --checkpoint ckpt_xyz789
# ✅ Code: valid (SHA matches)
# ✅ Config: valid (hash matches)
# ✅ Weights: valid (artifact present)
# ✅ Gates: all passed at checkpoint time
```

---

## 10. Compliance & Standards

### OWASP Top 10 (AI/ML)

**Coverage:**
1. **Prompt Injection:** Input validation + sandboxing
2. **Insecure Output Handling:** Output filtering + redaction
3. **Training Data Poisoning:** IR→IC contractivity + WORM audit
4. **Model Denial of Service:** Budget limits + circuit breakers
5. **Supply Chain Vulnerabilities:** SBOM + SCA + signed releases
6. **Sensitive Information Disclosure:** Log redaction + consent checks
7. **Insecure Plugin Design:** Σ-Guard validation + sandboxing
8. **Excessive Agency:** Death gate + human-in-loop for critical actions
9. **Overreliance:** Uncertainty disclosure + calibration (ECE)
10. **Model Theft:** Access controls + audit trails

### NIST AI RMF (Risk Management Framework)

**Mapping:**
- **Govern:** LO-14 + ΣEA policies + OPA/Rego
- **Map:** Threat model + attack surface analysis
- **Measure:** Metrics (ECE, ρ_bias, ρ) + observability
- **Manage:** Σ-Guard + rollback + incident response

### GDPR (EU General Data Protection Regulation)

**Articles:**
- **Art. 13-14 (Transparency):** Logs + PCAg disclosure
- **Art. 15 (Access):** User data export API
- **Art. 16 (Rectification):** Update API
- **Art. 17 (Deletion):** Deletion + redaction procedure
- **Art. 25 (Privacy-by-Design):** Fail-closed + minimization
- **Art. 32 (Security):** Encryption + access controls

---

## 11. Secure Development Lifecycle

### Pre-Commit Hooks

**Installation:**
```bash
pre-commit install
```

**Configuration (`.pre-commit-config.yaml`):**
```yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  hooks: [{id: ruff}]
- repo: https://github.com/psf/black
  hooks: [{id: black}]
- repo: https://github.com/pre-commit/mirrors-mypy
  hooks: [{id: mypy}]
- repo: https://github.com/gitleaks/gitleaks
  hooks: [{id: gitleaks}]
- repo: https://github.com/PyCQA/bandit
  hooks: [{id: bandit}]
```

### CI/CD Security Checks

**GitHub Actions:**
```yaml
- name: Security Scan
  run: |
    pip install bandit safety
    bandit -r penin/ -ll
    safety check --json
    
- name: Secrets Scan
  uses: gitleaks/gitleaks-action@v2
  
- name: SBOM Generation
  run: cyclonedx-py --format json --output sbom.json
  
- name: Vulnerability Scan
  run: trivy fs --severity HIGH,CRITICAL --exit-code 1 .
```

### Code Review Checklist

**Security-Focused:**
- [ ] No hardcoded secrets (API keys, passwords)
- [ ] Input validation (XSS, injection, overflow)
- [ ] Output sanitization (redaction, escaping)
- [ ] Error handling (no stack traces to users)
- [ ] Σ-Guard coverage (ethical validation)
- [ ] WORM logging (audit trail)
- [ ] Test coverage (security scenarios)

---

## 12. Penetration Testing

### Scope

**In-Scope:**
- Ethical gate bypass attempts
- Ledger tampering (hash chain attacks)
- Budget exhaustion (DoS)
- Prompt injection (adversarial inputs)
- Supply chain (dependency confusion)

**Out-of-Scope:**
- Physical attacks
- Social engineering (unless testing incident response)
- Third-party APIs (OpenAI, Anthropic, etc.)

### Tools

**Automated:**
- **OWASP ZAP:** Web app scanning
- **Bandit:** Python security linting
- **Safety:** Dependency vulnerability check

**Manual:**
- Ethical gate stress tests (boundary cases)
- Ledger verification attacks (modify past events)
- Budget race conditions (concurrent requests)

### Reporting

**Template:**
```markdown
# Security Finding: [Title]

**Severity:** Critical | High | Medium | Low
**CVSS Score:** X.X (if applicable)

## Description
[Detailed explanation of vulnerability]

## Proof of Concept
```python
# Exploit code
```

## Impact
[Potential damage]

## Remediation
[Recommended fixes]

## References
[CVEs, articles, etc.]
```

---

## 13. Security Metrics

**KPIs:**
- Σ-Guard failure rate (target: < 0.1%)
- Ledger integrity (target: 100% valid chain)
- Secrets exposure incidents (target: 0)
- Budget overruns (target: 0)
- Mean time to detect (MTTD) (target: < 5 min)
- Mean time to respond (MTTR) (target: < 30 min)

**Dashboards:**
```prometheus
# Grafana query
sum(rate(penin_gate_fail_total[1h])) by (gate)
```

---

## 14. Contact & Disclosure

**Security Issues:**
- Email: security@penin.example.com (PGP key available)
- Response SLA: 24 hours (acknowledge), 7 days (initial triage)

**Responsible Disclosure:**
1. Report privately (do not publish)
2. Allow 90 days for fix (coordinated disclosure)
3. Credit in CHANGELOG (if desired)

**Bug Bounty:**
- Platform: HackerOne (future)
- Scope: Critical/High severity in core modules
- Rewards: $100-$5000 (based on impact)

---

## 15. Appendix: Security Checklist

**Pre-Deployment:**
- [ ] All secrets in env vars / secret manager
- [ ] HTTPS enabled (valid certificate)
- [ ] Firewall configured (minimal ports)
- [ ] Σ-Guard enabled + tested
- [ ] WORM ledger initialized + verified
- [ ] Budget limits set
- [ ] Circuit breakers configured
- [ ] Rate limits applied
- [ ] Security headers enabled
- [ ] Logging + monitoring active
- [ ] Incident response playbook documented
- [ ] Backup/restore tested
- [ ] SBOM generated + archived
- [ ] SCA scan passed (no HIGH/CRITICAL)
- [ ] Penetration test completed

**Post-Deployment:**
- [ ] Monitor Σ-Guard failures
- [ ] Verify ledger integrity daily
- [ ] Review budget usage weekly
- [ ] Rotate secrets monthly
- [ ] Update dependencies quarterly
- [ ] Re-run SCA quarterly
- [ ] Conduct security audit annually

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-01  
**Maintained By:** PENIN-Ω Security Team  
**License:** Apache 2.0
