"""Tests for Proof-Carrying Artifact Generator"""

import pytest
from penin.ledger.pcag_generator import (
    PCAgGenerator,
    ProofComponents,
    ProofCarryingArtifact,
    generate_proof_artifact,
)


class TestPCAgGeneration:
    """Test PCAg generation"""
    
    def test_generate_basic_artifact(self):
        """Test basic artifact generation"""
        generator = PCAgGenerator()
        
        proofs = ProofComponents(
            linf_score=0.85,
            caos_plus=25.0,
            sr_score=0.82,
            omega_g=0.88,
            rho=0.95,
            ece=0.005,
            rho_bias=1.02,
            delta_linf=0.015,
            ethics_passed=True,
            violations_count=0,
            cost_usd=0.10,
            cost_increase_pct=0.05,
        )
        
        artifact = generator.generate_artifact(
            decision_id="test_001",
            decision_type="model_promotion",
            decision_output="Champion promoted",
            proofs=proofs,
            sigma_verdict="promote",
            ethics_verdict="pass",
        )
        
        assert artifact.decision_id == "test_001"
        assert artifact.proofs.linf_score == 0.85
        assert len(artifact.current_hash) == 64  # BLAKE3 hex = 64 chars
        assert artifact.prev_artifact_hash is None  # First artifact
    
    def test_artifact_hash_chain(self):
        """Test hash chain linkage"""
        generator = PCAgGenerator()
        
        proofs = ProofComponents(
            linf_score=0.85, caos_plus=25.0, sr_score=0.82, omega_g=0.88,
            rho=0.95, ece=0.005, rho_bias=1.02, delta_linf=0.015,
            ethics_passed=True, violations_count=0, cost_usd=0.10, cost_increase_pct=0.05,
        )
        
        # Generate 3 artifacts
        artifacts = []
        for i in range(3):
            artifact = generator.generate_artifact(
                decision_id=f"test_{i:03d}",
                decision_type="test",
                decision_output=f"Output {i}",
                proofs=proofs,
                sigma_verdict="promote",
                ethics_verdict="pass",
            )
            artifacts.append(artifact)
        
        # Verify chain
        assert artifacts[0].prev_artifact_hash is None
        assert artifacts[1].prev_artifact_hash == artifacts[0].current_hash
        assert artifacts[2].prev_artifact_hash == artifacts[1].current_hash
    
    def test_artifact_verification(self):
        """Test artifact integrity verification"""
        generator = PCAgGenerator()
        
        proofs = ProofComponents(
            linf_score=0.85, caos_plus=25.0, sr_score=0.82, omega_g=0.88,
            rho=0.95, ece=0.005, rho_bias=1.02, delta_linf=0.015,
            ethics_passed=True, violations_count=0, cost_usd=0.10, cost_increase_pct=0.05,
        )
        
        artifact = generator.generate_artifact(
            decision_id="test_001",
            decision_type="test",
            decision_output="Test output",
            proofs=proofs,
            sigma_verdict="promote",
            ethics_verdict="pass",
        )
        
        # Valid artifact should verify
        assert generator.verify_artifact(artifact) is True
        
        # Tampered artifact should fail
        artifact.decision_output = "TAMPERED"
        assert generator.verify_artifact(artifact) is False
    
    def test_chain_verification(self):
        """Test full chain verification"""
        generator = PCAgGenerator()
        
        proofs = ProofComponents(
            linf_score=0.85, caos_plus=25.0, sr_score=0.82, omega_g=0.88,
            rho=0.95, ece=0.005, rho_bias=1.02, delta_linf=0.015,
            ethics_passed=True, violations_count=0, cost_usd=0.10, cost_increase_pct=0.05,
        )
        
        # Generate chain
        artifacts = []
        for i in range(5):
            artifact = generator.generate_artifact(
                decision_id=f"test_{i:03d}",
                decision_type="test",
                decision_output=f"Output {i}",
                proofs=proofs,
                sigma_verdict="promote",
                ethics_verdict="pass",
            )
            artifacts.append(artifact)
        
        # Verify chain
        valid, errors = generator.verify_chain(artifacts)
        assert valid is True
        assert len(errors) == 0
    
    def test_serialization_roundtrip(self):
        """Test artifact serialization/deserialization"""
        generator = PCAgGenerator()
        
        proofs = ProofComponents(
            linf_score=0.85, caos_plus=25.0, sr_score=0.82, omega_g=0.88,
            rho=0.95, ece=0.005, rho_bias=1.02, delta_linf=0.015,
            ethics_passed=True, violations_count=0, cost_usd=0.10, cost_increase_pct=0.05,
        )
        
        original = generator.generate_artifact(
            decision_id="test_001",
            decision_type="test",
            decision_output="Test",
            proofs=proofs,
            sigma_verdict="promote",
            ethics_verdict="pass",
            metadata={"extra": "data"},
        )
        
        # Serialize and deserialize
        json_str = generator.serialize_artifact(original)
        restored = generator.deserialize_artifact(json_str)
        
        # Should be identical
        assert restored.artifact_id == original.artifact_id
        assert restored.decision_id == original.decision_id
        assert restored.current_hash == original.current_hash
        assert restored.proofs.linf_score == original.proofs.linf_score
        assert restored.metadata == original.metadata
    
    def test_convenience_function(self):
        """Test convenience function for generating artifacts"""
        artifact = generate_proof_artifact(
            decision_id="conv_001",
            linf=0.88,
            caos=26.0,
            sr=0.84,
            omega_g=0.90,
            gates={'rho': 0.92, 'ece': 0.003, 'rho_bias': 1.01, 'delta_linf': 0.02},
            ethics_ok=True,
            cost_usd=0.15,
            decision_type="query",
            decision_output="Response text",
        )
        
        assert artifact.decision_id == "conv_001"
        assert artifact.proofs.linf_score == 0.88
        # Verdict depends on gate logic - just check it's valid
        assert artifact.sigma_guard_verdict in ["promote", "rollback", "review", "block"]
        assert artifact.ethics_verdict in ["pass", "fail", "warn"]
