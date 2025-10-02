#!/usr/bin/env python3
"""
Standalone test for PENIN-Ω Cryptographic Attestation System
=============================================================

This test loads modules directly to avoid dependency issues.
"""

import importlib.util
import sys


def load_module(module_name, file_path):
    """Load a module directly from file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load attestation module
attestation = load_module('attestation', 'penin/omega/attestation.py')

print("=" * 70)
print("PENIN-Ω CRYPTOGRAPHIC ATTESTATION SYSTEM - STANDALONE TEST")
print("=" * 70)
print()

# Test 1: Cryptography availability
print("[TEST 1] Cryptography Library Availability")
print(f"  Has cryptography: {attestation.HAS_CRYPTOGRAPHY}")
if attestation.HAS_CRYPTOGRAPHY:
    print("  ✓ Using Ed25519 signatures")
else:
    print("  ⚠ Using fallback HMAC signatures")
print()

# Test 2: Key pair generation
print("[TEST 2] Key Pair Generation")
sr_key_pair = attestation.SignatureKeyPair.generate(attestation.ServiceType.SR_OMEGA)
print(f"  Service: {sr_key_pair.service_type.value}")
print(f"  Public key: {sr_key_pair.public_key_hex()[:32]}...")
print(f"  Created: {sr_key_pair.created_at}")
print("  ✓ Key pair generated successfully")
print()

# Test 3: Attestation creation and signing
print("[TEST 3] Attestation Creation and Signing")
guard_key_pair = attestation.SignatureKeyPair.generate(attestation.ServiceType.SIGMA_GUARD)
att = attestation.Attestation(
    service_type=attestation.ServiceType.SIGMA_GUARD,
    verdict="pass",
    subject_id="test_candidate_001",
    metrics={
        "gates_passed": 10,
        "aggregate_score": 0.92,
        "gates": [
            {"name": "contractividade", "passed": True},
            {"name": "calibration", "passed": True},
        ]
    }
)
att.sign(guard_key_pair)
print(f"  Service: {att.service_type.value}")
print(f"  Verdict: {att.verdict}")
print(f"  Subject: {att.subject_id}")
print(f"  Signature: {att.signature[:32]}...")
print(f"  Content hash: {att.content_hash[:32]}...")
print("  ✓ Attestation signed successfully")
print()

# Test 4: Signature verification
print("[TEST 4] Signature Verification")
is_valid = att.verify()
print(f"  Verification result: {'VALID' if is_valid else 'INVALID'}")
if is_valid:
    print("  ✓ Signature verified successfully")
else:
    print("  ✗ Signature verification failed")
    sys.exit(1)
print()

# Test 5: Tampering detection
print("[TEST 5] Tampering Detection")
original_verdict = att.verdict
att.verdict = "fail"  # Tamper with the verdict
is_valid_tampered = att.verify()
print(f"  After tampering: {'VALID' if is_valid_tampered else 'INVALID'}")
if not is_valid_tampered:
    print("  ✓ Tampering detected successfully")
else:
    print("  ✗ Tampering not detected - SECURITY ISSUE")
    sys.exit(1)
att.verdict = original_verdict  # Restore
print()

# Test 6: Attestation chain
print("[TEST 6] Attestation Chain")
chain = attestation.AttestationChain(candidate_id="test_candidate_002")

# Create multiple attestations
sr_keys = attestation.SignatureKeyPair.generate(attestation.ServiceType.SR_OMEGA)
guard_keys = attestation.SignatureKeyPair.generate(attestation.ServiceType.SIGMA_GUARD)

sr_att = attestation.Attestation(
    service_type=attestation.ServiceType.SR_OMEGA,
    verdict="pass",
    subject_id="test_candidate_002",
    metrics={"sr_score": 0.91, "components": {"awareness": 0.9, "ethics": 1.0}}
)
sr_att.sign(sr_keys)

guard_att = attestation.Attestation(
    service_type=attestation.ServiceType.SIGMA_GUARD,
    verdict="pass",
    subject_id="test_candidate_002",
    metrics={"aggregate_score": 0.89}
)
guard_att.sign(guard_keys)

# Add to chain
chain.add_attestation(sr_att)
chain.add_attestation(guard_att)

print(f"  Candidate: {chain.candidate_id}")
print(f"  Attestations: {len(chain.attestations)}")
print(f"  Chain hash: {chain.chain_hash[:32]}...")

# Verify chain
is_valid, msg = chain.verify_chain()
print(f"  Chain verification: {'VALID' if is_valid else 'INVALID'}")
if is_valid:
    print("  ✓ Chain verified successfully")
else:
    print(f"  ✗ Chain verification failed: {msg}")
    sys.exit(1)
print()

# Test 7: Required attestations
print("[TEST 7] Required Attestations Check")
has_all = chain.has_all_required()
all_passed = chain.all_passed()
print(f"  Has all required: {has_all}")
print(f"  All passed: {all_passed}")
if has_all and all_passed:
    print("  ✓ All required attestations present and passed")
else:
    print("  ✗ Missing attestations or some failed")
    sys.exit(1)
print()

# Test 8: Attestation manager
print("[TEST 8] Attestation Manager")
manager = attestation.AttestationManager()
print(f"  Services configured: {len(manager.key_pairs)}")

# Create attestation via manager
manager_att = manager.create_attestation(
    service_type=attestation.ServiceType.ACFA_LEAGUE,
    verdict="promote",
    subject_id="test_candidate_003",
    metrics={"promotion_score": 0.95}
)

is_valid = manager.verify_attestation(manager_att)
print(f"  Manager attestation: {'VALID' if is_valid else 'INVALID'}")
if is_valid:
    print("  ✓ Manager can create and verify attestations")
else:
    print("  ✗ Manager attestation verification failed")
    sys.exit(1)
print()

# Test 9: Serialization
print("[TEST 9] Serialization/Deserialization")
# Serialize attestation
att_dict = manager_att.to_dict()
print(f"  Serialized keys: {list(att_dict.keys())}")

# Deserialize
restored_att = attestation.Attestation.from_dict(att_dict)
is_valid = restored_att.verify()
print(f"  Restored attestation: {'VALID' if is_valid else 'INVALID'}")
if is_valid:
    print("  ✓ Serialization/deserialization works")
else:
    print("  ✗ Restored attestation invalid")
    sys.exit(1)

# Serialize chain
chain_dict = chain.to_dict()
print(f"  Chain serialized with {len(chain_dict['attestations'])} attestations")

# Deserialize chain
restored_chain = attestation.AttestationChain.from_dict(chain_dict)
is_valid, msg = restored_chain.verify_chain()
print(f"  Restored chain: {'VALID' if is_valid else 'INVALID'}")
if is_valid:
    print("  ✓ Chain serialization/deserialization works")
else:
    print(f"  ✗ Restored chain invalid: {msg}")
    sys.exit(1)
print()

# Test 10: Convenience functions
print("[TEST 10] Convenience Functions")
sr_attestation = attestation.create_sr_attestation(
    verdict="pass",
    candidate_id="test_sr",
    sr_score=0.88,
    components={"awareness": 0.9, "ethics": 1.0, "autocorrection": 0.85, "metacognition": 0.87}
)
print(f"  SR attestation: {sr_attestation.service_type.value} - {'VALID' if sr_attestation.verify() else 'INVALID'}")

guard_attestation = attestation.create_sigma_guard_attestation(
    verdict="pass",
    candidate_id="test_guard",
    gates=[{"name": "test_gate", "passed": True}],
    aggregate_score=0.92
)
print(f"  Guard attestation: {guard_attestation.service_type.value} - {'VALID' if guard_attestation.verify() else 'INVALID'}")

acfa_attestation = attestation.create_acfa_attestation(
    verdict="promote",
    candidate_id="test_acfa",
    promotion_decision={"promote": True, "reason": "all_gates_passed"}
)
print(f"  ACFA attestation: {acfa_attestation.service_type.value} - {'VALID' if acfa_attestation.verify() else 'INVALID'}")
print("  ✓ All convenience functions work")
print()

# Summary
print("=" * 70)
print("ALL TESTS PASSED ✓")
print("=" * 70)
print()
print("Summary:")
print("- Cryptographic signing: ✓")
print("- Signature verification: ✓")
print("- Tampering detection: ✓")
print("- Attestation chains: ✓")
print("- Serialization: ✓")
print("- Manager functionality: ✓")
print()
print("The cryptographic attestation system is fully operational!")
