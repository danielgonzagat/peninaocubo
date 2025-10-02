#!/usr/bin/env python3
"""
Test suite for PENIN-Ω Cryptographic Attestation System
========================================================

Tests:
- Key generation and management
- Attestation creation and signing
- Signature verification
- Attestation chains
- Integration with SR-Ω∞ and Σ-Guard
- Integration with ACFA League
"""

import sys

# Add workspace to path
sys.path.insert(0, "/home/runner/work/peninaocubo/peninaocubo")

from penin.omega.attestation import (
    HAS_CRYPTOGRAPHY,
    Attestation,
    AttestationChain,
    AttestationManager,
    ServiceType,
    SignatureKeyPair,
    create_acfa_attestation,
    create_sigma_guard_attestation,
    create_sr_attestation,
)


def test_key_pair_generation():
    """Test Ed25519 key pair generation"""
    print("\n[TEST] Key Pair Generation")

    # Generate key pair
    key_pair = SignatureKeyPair.generate(ServiceType.SR_OMEGA)

    assert key_pair.service_type == ServiceType.SR_OMEGA
    assert len(key_pair.private_key_bytes) > 0
    assert len(key_pair.public_key_bytes) > 0
    assert key_pair.created_at is not None

    # Public key should be deterministic from private key
    public_hex = key_pair.public_key_hex()
    assert len(public_hex) > 0

    print(f"  ✓ Generated key pair for {key_pair.service_type.value}")
    print(f"  ✓ Public key: {public_hex[:16]}...")


def test_attestation_creation_and_signing():
    """Test attestation creation and cryptographic signing"""
    print("\n[TEST] Attestation Creation and Signing")

    # Generate key pair
    key_pair = SignatureKeyPair.generate(ServiceType.SIGMA_GUARD)

    # Create attestation
    attestation = Attestation(
        service_type=ServiceType.SIGMA_GUARD,
        verdict="pass",
        subject_id="candidate_123",
        metrics={
            "gates_passed": 10,
            "aggregate_score": 0.92,
        }
    )

    # Sign attestation
    attestation.sign(key_pair)

    assert attestation.signature != ""
    assert attestation.public_key != ""
    assert attestation.content_hash != ""

    print(f"  ✓ Created attestation for {attestation.service_type.value}")
    print(f"  ✓ Signature: {attestation.signature[:32]}...")
    print(f"  ✓ Content hash: {attestation.content_hash[:32]}...")


def test_attestation_verification():
    """Test attestation signature verification"""
    print("\n[TEST] Attestation Verification")

    # Generate key pair
    key_pair = SignatureKeyPair.generate(ServiceType.SR_OMEGA)

    # Create and sign attestation
    attestation = Attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="candidate_456",
        metrics={
            "sr_score": 0.87,
            "components": {
                "awareness": 0.9,
                "ethics": 1.0,
                "autocorrection": 0.85,
                "metacognition": 0.88,
            }
        }
    )

    attestation.sign(key_pair)

    # Verify signature
    is_valid = attestation.verify()
    assert is_valid, "Attestation signature should be valid"

    print("  ✓ Attestation signature verified")

    # Test tampering detection
    original_verdict = attestation.verdict
    attestation.verdict = "fail"

    # Content hash should now mismatch
    is_valid_after_tampering = attestation.verify()
    assert not is_valid_after_tampering, "Tampered attestation should fail verification"

    # Restore original
    attestation.verdict = original_verdict

    print("  ✓ Tampering detection works")


def test_attestation_chain():
    """Test attestation chain creation and verification"""
    print("\n[TEST] Attestation Chain")

    # Create chain
    chain = AttestationChain(candidate_id="candidate_789")

    # Generate key pairs for services
    sr_keys = SignatureKeyPair.generate(ServiceType.SR_OMEGA)
    guard_keys = SignatureKeyPair.generate(ServiceType.SIGMA_GUARD)

    # Create SR attestation
    sr_attestation = Attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="candidate_789",
        metrics={"sr_score": 0.91}
    )
    sr_attestation.sign(sr_keys)

    # Create Sigma Guard attestation
    guard_attestation = Attestation(
        service_type=ServiceType.SIGMA_GUARD,
        verdict="pass",
        subject_id="candidate_789",
        metrics={"aggregate_score": 0.89}
    )
    guard_attestation.sign(guard_keys)

    # Add to chain
    chain.add_attestation(sr_attestation)
    chain.add_attestation(guard_attestation)

    assert len(chain.attestations) == 2
    assert chain.chain_hash != ""

    print(f"  ✓ Created chain with {len(chain.attestations)} attestations")
    print(f"  ✓ Chain hash: {chain.chain_hash[:32]}...")

    # Verify chain
    is_valid, msg = chain.verify_chain()
    assert is_valid, f"Chain should be valid: {msg}"

    print("  ✓ Chain verification passed")

    # Check required attestations
    assert chain.has_all_required()
    assert chain.all_passed()

    print("  ✓ All required attestations present and passed")


def test_attestation_chain_rejection():
    """Test attestation chain with failed attestation"""
    print("\n[TEST] Attestation Chain Rejection")

    chain = AttestationChain(candidate_id="candidate_bad")

    # Generate key pairs
    sr_keys = SignatureKeyPair.generate(ServiceType.SR_OMEGA)
    guard_keys = SignatureKeyPair.generate(ServiceType.SIGMA_GUARD)

    # SR passes
    sr_attestation = Attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="candidate_bad",
        metrics={"sr_score": 0.85}
    )
    sr_attestation.sign(sr_keys)
    chain.add_attestation(sr_attestation)

    # Sigma Guard fails
    guard_attestation = Attestation(
        service_type=ServiceType.SIGMA_GUARD,
        verdict="fail",
        subject_id="candidate_bad",
        metrics={"aggregate_score": 0.45}
    )
    guard_attestation.sign(guard_keys)
    chain.add_attestation(guard_attestation)

    # Chain is valid (signatures are correct)
    is_valid, _ = chain.verify_chain()
    assert is_valid

    # But not all attestations passed
    assert not chain.all_passed()

    print("  ✓ Chain correctly identifies failed attestation")


def test_attestation_manager():
    """Test attestation manager"""
    print("\n[TEST] Attestation Manager")

    manager = AttestationManager()

    # Check that keys were generated for all services
    for service_type in ServiceType:
        public_key = manager.get_public_key(service_type)
        assert len(public_key) > 0
        print(f"  ✓ Generated key for {service_type.value}")

    # Create attestation using manager
    attestation = manager.create_attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="test_123",
        metrics={"score": 0.9}
    )

    assert attestation.signature != ""
    assert attestation.verify()

    print("  ✓ Manager can create and sign attestations")

    # Verify attestation
    is_valid = manager.verify_attestation(attestation)
    assert is_valid

    print("  ✓ Manager can verify attestations")


def test_convenience_functions():
    """Test convenience functions for creating attestations"""
    print("\n[TEST] Convenience Functions")

    # SR attestation
    sr_att = create_sr_attestation(
        verdict="pass",
        candidate_id="test_sr",
        sr_score=0.88,
        components={
            "awareness": 0.9,
            "ethics": 1.0,
            "autocorrection": 0.85,
            "metacognition": 0.87,
        }
    )

    assert sr_att.service_type == ServiceType.SR_OMEGA
    assert sr_att.verify()
    print("  ✓ create_sr_attestation works")

    # Sigma Guard attestation
    guard_att = create_sigma_guard_attestation(
        verdict="pass",
        candidate_id="test_guard",
        gates=[
            {"name": "contractividade", "passed": True, "value": 0.95},
            {"name": "calibration", "passed": True, "value": 0.005},
        ],
        aggregate_score=0.92
    )

    assert guard_att.service_type == ServiceType.SIGMA_GUARD
    assert guard_att.verify()
    print("  ✓ create_sigma_guard_attestation works")

    # ACFA attestation
    acfa_att = create_acfa_attestation(
        verdict="promote",
        candidate_id="test_acfa",
        promotion_decision={
            "promote": True,
            "reason": "all_gates_passed",
            "improvement_score": 0.05,
        }
    )

    assert acfa_att.service_type == ServiceType.ACFA_LEAGUE
    assert acfa_att.verify()
    print("  ✓ create_acfa_attestation works")


def test_attestation_serialization():
    """Test attestation serialization and deserialization"""
    print("\n[TEST] Attestation Serialization")

    # Create and sign attestation
    manager = AttestationManager()
    original = manager.create_attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="serialize_test",
        metrics={"score": 0.91}
    )

    # Serialize
    data = original.to_dict()
    assert isinstance(data, dict)
    assert "signature" in data
    assert "public_key" in data

    print("  ✓ Attestation serialized to dict")

    # Deserialize
    restored = Attestation.from_dict(data)

    assert restored.service_type == original.service_type
    assert restored.verdict == original.verdict
    assert restored.subject_id == original.subject_id
    assert restored.signature == original.signature
    assert restored.public_key == original.public_key

    # Verify restored attestation
    assert restored.verify()

    print("  ✓ Attestation deserialized and verified")


def test_chain_serialization():
    """Test attestation chain serialization"""
    print("\n[TEST] Chain Serialization")

    manager = AttestationManager()

    # Create chain with attestations
    original_chain = AttestationChain(candidate_id="chain_serialize_test")

    sr_att = manager.create_attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict="pass",
        subject_id="chain_serialize_test",
        metrics={"sr_score": 0.9}
    )

    guard_att = manager.create_attestation(
        service_type=ServiceType.SIGMA_GUARD,
        verdict="pass",
        subject_id="chain_serialize_test",
        metrics={"aggregate_score": 0.88}
    )

    original_chain.add_attestation(sr_att)
    original_chain.add_attestation(guard_att)
    original_chain.final_decision = "promote"

    # Serialize
    data = original_chain.to_dict()
    assert isinstance(data, dict)
    assert len(data["attestations"]) == 2

    print("  ✓ Chain serialized to dict")

    # Deserialize
    restored_chain = AttestationChain.from_dict(data)

    assert restored_chain.candidate_id == original_chain.candidate_id
    assert len(restored_chain.attestations) == 2
    assert restored_chain.final_decision == original_chain.final_decision

    # Verify restored chain
    is_valid, msg = restored_chain.verify_chain()
    assert is_valid, msg

    print("  ✓ Chain deserialized and verified")


def test_integration_with_sigma_guard():
    """Test integration with Σ-Guard"""
    print("\n[TEST] Integration with Σ-Guard")

    try:
        from penin.guard.sigma_guard_complete import (
            GateMetrics,
            SigmaGuard,
        )

        # Create Sigma Guard
        guard = SigmaGuard()

        # Create metrics that pass all gates
        metrics = GateMetrics(
            rho=0.95,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.88,
            omega_g=0.90,
            delta_linf=0.03,
            caos_plus=1.8,
            cost_increase=0.05,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        # Validate
        verdict = guard.validate(metrics)

        assert verdict.passed

        # Create attestation from verdict
        attestation = verdict.create_attestation("test_candidate")

        if attestation is not None:
            assert attestation.service_type == ServiceType.SIGMA_GUARD
            assert attestation.verify()
            print("  ✓ Σ-Guard verdict can create attestation")
        else:
            print("  ⚠ Attestation creation skipped (module not available)")

    except ImportError as e:
        print(f"  ⚠ Skipping Σ-Guard integration test: {e}")


def test_integration_with_sr_omega():
    """Test integration with SR-Ω∞"""
    print("\n[TEST] Integration with SR-Ω∞")

    try:
        from penin.omega.sr import SRAggregationMethod, SRComponents, SROmegaEngine

        # Create SR engine
        engine = SROmegaEngine(method=SRAggregationMethod.HARMONIC)

        # Create components
        components = SRComponents(
            awareness=0.9,
            ethics=1.0,
            autocorrection=0.85,
            metacognition=0.88,
        )

        # Create attestation
        attestation = engine.create_attestation(components, "test_candidate", tau=0.8)

        if attestation is not None:
            assert attestation.service_type == ServiceType.SR_OMEGA
            assert attestation.verify()
            print("  ✓ SR-Ω∞ engine can create attestation")
        else:
            print("  ⚠ Attestation creation skipped (module not available)")

    except ImportError as e:
        print(f"  ⚠ Skipping SR-Ω∞ integration test: {e}")


def test_cryptography_availability():
    """Test cryptography library availability"""
    print("\n[TEST] Cryptography Library")

    if HAS_CRYPTOGRAPHY:
        print("  ✓ cryptography library available (Ed25519 signatures)")
    else:
        print("  ⚠ cryptography library not available (using fallback HMAC)")


def run_all_tests():
    """Run all attestation tests"""
    print("=" * 60)
    print("CRYPTOGRAPHIC ATTESTATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_cryptography_availability,
        test_key_pair_generation,
        test_attestation_creation_and_signing,
        test_attestation_verification,
        test_attestation_chain,
        test_attestation_chain_rejection,
        test_attestation_manager,
        test_convenience_functions,
        test_attestation_serialization,
        test_chain_serialization,
        test_integration_with_sigma_guard,
        test_integration_with_sr_omega,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
