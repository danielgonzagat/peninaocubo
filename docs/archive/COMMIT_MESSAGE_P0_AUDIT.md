# Commit Message - P0 Audit Fixes

```
feat(audit): implement P0 critical security and functionality fixes

## Summary
Implements all critical P0 audit fixes identified in the security review:
- Ethics metrics calculation and attestation (ΣEA/IR→IC)
- Metrics server localhost-only binding (security)
- WORM SQLite WAL mode and busy timeout (concurrency)
- Router cost consideration in scoring (economics)

## Changes

### 1. Ethics Metrics Module (penin/omega/)
- Add `penin/omega/ethics_metrics.py` with full ethics calculation
- Calculate ECE, Bias Ratio, Fairness, Risk Contraction
- Integrate ethics gate validation in main cycle
- Log ethics attestation to WORM with evidence hashes

### 2. Security Fixes
- Bind metrics server to localhost only (observability.py:378)
- Add WAL mode and busy_timeout to WORM SQLite (1_de_8_v7.py)
- Fail-closed behavior for ethics validation failures

### 3. Router Economics
- Include cost penalty in router scoring (penin/router.py)
- Scale cost_usd × 1000 for meaningful impact on selection

### 4. Testing & Validation
- Add comprehensive P0 audit test suite (test_p0_simple.py)
- All 5/5 tests pass, validating critical fixes
- Fallback implementations for missing dependencies

## Risk Assessment
- **Backward Compatible**: ✅ Yes
- **Fail-Closed**: ✅ Ethics gate blocks promotion on failure
- **Security**: ✅ Metrics server no longer exposes telemetry
- **Performance**: ✅ WAL mode improves SQLite concurrency

## Test Results
```
Results: 5/5 tests passed
✅ All P0 audit fix tests PASSED!
Critical security and functionality issues have been addressed.
```

## Files Modified
- penin/omega/ethics_metrics.py (new)
- penin/omega/__init__.py (new)
- 1_de_8_v7.py (ethics integration, WAL mode)
- observability.py (localhost binding)
- penin/router.py (cost scoring)
- test_p0_simple.py (new test suite)

## Compliance
- Addresses all P0 critical security vulnerabilities
- Implements ethical AI metrics (ECE, bias, fairness)
- Provides audit trail with evidence hashes
- Maintains deterministic behavior with seed control

Resolves: P0 audit findings
Type: security, functionality, ethics
```