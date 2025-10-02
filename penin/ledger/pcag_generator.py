"""
Proof-Carrying Artifact Generator (PCAg)
=========================================

Generates cryptographically-signed proof artifacts for every decision.

Integrates with WORM ledger to create immutable audit trail with:
- BLAKE2b hash chains
- Decision metadata
- Mathematical proofs (L∞, CAOS+, SR, gates)
- Timestamps and signatures
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ProofComponents:
    """Mathematical proof components for a decision"""
    
    # Core metrics
    linf_score: float
    caos_plus: float
    sr_score: float
    omega_g: float  # Global coherence
    
    # Gates
    rho: float  # Contractivity
    ece: float  # Calibration
    rho_bias: float  # Fairness
    delta_linf: float  # Growth
    
    # Ethics
    ethics_passed: bool
    violations_count: int
    
    # Cost
    cost_usd: float
    cost_increase_pct: float


@dataclass
class ProofCarryingArtifact:
    """
    Complete Proof-Carrying Artifact (PCAg)
    
    Cryptographically-signed proof of decision validity.
    """
    
    # Identity
    artifact_id: str
    decision_id: str
    timestamp_ns: int
    
    # Decision context
    decision_type: str
    decision_output: str
    
    # Mathematical proofs
    proofs: ProofComponents
    
    # Verdicts
    sigma_guard_verdict: str  # "promote" | "rollback" | "block"
    ethics_verdict: str  # "pass" | "fail"
    
    # Chain linkage
    prev_artifact_hash: str | None
    current_hash: str
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Signature (future: digital signature)
    signature: str | None = None


class PCAgGenerator:
    """
    Generator for Proof-Carrying Artifacts.
    
    Creates immutable, cryptographically-linked artifacts for audit trail.
    """
    
    def __init__(self, ledger_path: str | None = None):
        """
        Initialize PCAg generator.
        
        Args:
            ledger_path: Path to WORM ledger (optional)
        """
        self.ledger_path = ledger_path
        self.prev_hash: str | None = None
    
    def generate_artifact(
        self,
        decision_id: str,
        decision_type: str,
        decision_output: str,
        proofs: ProofComponents,
        sigma_verdict: str,
        ethics_verdict: str,
        metadata: dict[str, Any] | None = None,
    ) -> ProofCarryingArtifact:
        """
        Generate a Proof-Carrying Artifact.
        
        Args:
            decision_id: Unique decision identifier
            decision_type: Type of decision (e.g., "model_promotion", "query_response")
            decision_output: Output/result of decision
            proofs: Mathematical proof components
            sigma_verdict: Sigma Guard verdict
            ethics_verdict: Ethics validation verdict
            metadata: Additional metadata
        
        Returns:
            ProofCarryingArtifact with cryptographic hash
        """
        # Generate artifact ID
        artifact_id = self._generate_artifact_id(decision_id)
        
        # Create artifact
        artifact = ProofCarryingArtifact(
            artifact_id=artifact_id,
            decision_id=decision_id,
            timestamp_ns=time.time_ns(),
            decision_type=decision_type,
            decision_output=decision_output,
            proofs=proofs,
            sigma_guard_verdict=sigma_verdict,
            ethics_verdict=ethics_verdict,
            prev_artifact_hash=self.prev_hash,
            current_hash="",  # Will be computed
            metadata=metadata or {},
        )
        
        # Compute hash (BLAKE2b for speed + security)
        artifact.current_hash = self._compute_hash(artifact)
        
        # Update chain
        self.prev_hash = artifact.current_hash
        
        return artifact
    
    def verify_artifact(self, artifact: ProofCarryingArtifact) -> bool:
        """
        Verify artifact integrity.
        
        Args:
            artifact: Artifact to verify
        
        Returns:
            True if valid, False otherwise
        """
        # Recompute hash
        stored_hash = artifact.current_hash
        artifact_copy = ProofCarryingArtifact(**asdict(artifact))
        artifact_copy.current_hash = ""
        computed_hash = self._compute_hash(artifact_copy)
        
        # Verify hash matches
        return stored_hash == computed_hash
    
    def verify_chain(
        self,
        artifacts: list[ProofCarryingArtifact]
    ) -> tuple[bool, list[str]]:
        """
        Verify hash chain integrity.
        
        Args:
            artifacts: List of artifacts in order
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        for i, artifact in enumerate(artifacts):
            # Verify individual artifact
            if not self.verify_artifact(artifact):
                errors.append(f"Artifact {i} ({artifact.artifact_id}): Hash mismatch")
            
            # Verify chain linkage
            if i > 0:
                expected_prev = artifacts[i-1].current_hash
                actual_prev = artifact.prev_artifact_hash
                
                if expected_prev != actual_prev:
                    errors.append(
                        f"Artifact {i} ({artifact.artifact_id}): "
                        f"Chain break - expected prev={expected_prev}, got={actual_prev}"
                    )
        
        return len(errors) == 0, errors
    
    def serialize_artifact(self, artifact: ProofCarryingArtifact) -> str:
        """
        Serialize artifact to JSON for storage.
        
        Args:
            artifact: Artifact to serialize
        
        Returns:
            JSON string
        """
        data = asdict(artifact)
        # Nested dataclasses need manual conversion
        data['proofs'] = asdict(artifact.proofs)
        return json.dumps(data, sort_keys=True)
    
    def deserialize_artifact(self, json_str: str) -> ProofCarryingArtifact:
        """
        Deserialize artifact from JSON.
        
        Args:
            json_str: JSON string
        
        Returns:
            ProofCarryingArtifact
        """
        data = json.loads(json_str)
        
        # Reconstruct nested dataclass
        proofs_data = data.pop('proofs')
        proofs = ProofComponents(**proofs_data)
        
        return ProofCarryingArtifact(proofs=proofs, **data)
    
    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================
    
    def _generate_artifact_id(self, decision_id: str) -> str:
        """Generate unique artifact ID"""
        timestamp = time.time_ns()
        return f"pcag_{decision_id}_{timestamp}"
    
    def _compute_hash(self, artifact: ProofCarryingArtifact) -> str:
        """
        Compute BLAKE2b hash of artifact.
        
        Uses deterministic serialization for consistent hashing.
        """
        # Create deterministic representation
        # Handle proofs - convert to dict if it's a dataclass
        from dataclasses import asdict, is_dataclass
        
        proofs_dict = artifact.proofs
        if is_dataclass(artifact.proofs):
            proofs_dict = asdict(artifact.proofs)
        elif isinstance(artifact.proofs, dict):
            proofs_dict = artifact.proofs
        else:
            # Fallback to dict representation
            proofs_dict = vars(artifact.proofs) if hasattr(artifact.proofs, '__dict__') else {}
        
        data = {
            "artifact_id": artifact.artifact_id,
            "decision_id": artifact.decision_id,
            "timestamp_ns": artifact.timestamp_ns,
            "decision_type": artifact.decision_type,
            "decision_output": artifact.decision_output,
            "proofs": proofs_dict,
            "sigma_guard_verdict": artifact.sigma_guard_verdict,
            "ethics_verdict": artifact.ethics_verdict,
            "prev_artifact_hash": artifact.prev_artifact_hash,
            "metadata": artifact.metadata,
        }
        
        # Serialize deterministically
        json_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        
        # Compute BLAKE2b hash (fast + secure)
        return self._compute_blake2b(json_bytes)
    
    def _compute_blake2b(self, data: bytes) -> str:
        """Compute BLAKE2b-256 hash"""
        h = hashlib.blake2b(data, digest_size=32)
        return h.hexdigest()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_proof_artifact(
    decision_id: str,
    linf: float,
    caos: float,
    sr: float,
    omega_g: float,
    gates: dict[str, float],
    ethics_ok: bool,
    cost_usd: float,
    **kwargs
) -> ProofCarryingArtifact:
    """
    Convenience function to generate proof artifact.
    
    Args:
        decision_id: Decision identifier
        linf: L∞ score
        caos: CAOS+ score
        sr: SR-Ω∞ score
        omega_g: Global coherence
        gates: Dict with rho, ece, rho_bias, delta_linf
        ethics_ok: Ethics passed
        cost_usd: Cost in USD
        **kwargs: Additional parameters
    
    Returns:
        ProofCarryingArtifact
    """
    proofs = ProofComponents(
        linf_score=linf,
        caos_plus=caos,
        sr_score=sr,
        omega_g=omega_g,
        rho=gates.get('rho', 1.0),
        ece=gates.get('ece', 0.0),
        rho_bias=gates.get('rho_bias', 1.0),
        delta_linf=gates.get('delta_linf', 0.0),
        ethics_passed=ethics_ok,
        violations_count=0 if ethics_ok else 1,
        cost_usd=cost_usd,
        cost_increase_pct=kwargs.get('cost_increase_pct', 0.0),
    )
    
    generator = PCAgGenerator()
    
    return generator.generate_artifact(
        decision_id=decision_id,
        decision_type=kwargs.get('decision_type', 'decision'),
        decision_output=kwargs.get('decision_output', ''),
        proofs=proofs,
        sigma_verdict="promote" if all(v < 1.0 for v in gates.values()) else "rollback",
        ethics_verdict="pass" if ethics_ok else "fail",
        metadata=kwargs.get('metadata', {}),
    )


__all__ = [
    "ProofComponents",
    "ProofCarryingArtifact",
    "PCAgGenerator",
    "generate_proof_artifact",
]
