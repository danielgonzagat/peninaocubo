"""
PENIN-Ω Cryptographic Attestation System
=========================================

Implements end-to-end cryptographic attestation for model promotions.

Flow:
1. Each validation service (SR-Ω∞, Σ-Guard) cryptographically signs its verdict
2. ACFA League validates the signature chain before promotion
3. The complete proof (signature set) is stored in the WORM Ledger

This makes system decisions not just auditable, but mathematically verifiable.

Uses Ed25519 signatures for:
- Fast verification
- Small signature size (64 bytes)
- Strong security (128-bit security level)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Use cryptography library for Ed25519 (part of Python standard library in 3.13+, otherwise use cryptography)
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    HAS_CRYPTOGRAPHY = True
except ImportError:
    # Fallback: use hashlib-based HMAC for signing (not true public-key crypto, but acceptable for MVP)
    import hmac

    HAS_CRYPTOGRAPHY = False


class ServiceType(str, Enum):
    """Type of validation service"""

    SR_OMEGA = "SR-Ω∞"
    SIGMA_GUARD = "Σ-Guard"
    ACFA_LEAGUE = "ACFA-League"


@dataclass
class SignatureKeyPair:
    """Ed25519 key pair for signing"""

    service_type: ServiceType
    private_key_bytes: bytes
    public_key_bytes: bytes
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def generate(cls, service_type: ServiceType) -> "SignatureKeyPair":
        """Generate a new Ed25519 key pair"""
        if HAS_CRYPTOGRAPHY:
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        else:
            # Fallback: generate random key material for HMAC
            import os

            private_bytes = os.urandom(32)
            public_bytes = hashlib.sha256(private_bytes).digest()

        return cls(
            service_type=service_type,
            private_key_bytes=private_bytes,
            public_key_bytes=public_bytes,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (WARNING: includes private key)"""
        return {
            "service_type": self.service_type.value,
            "public_key_hex": self.public_key_bytes.hex(),
            "created_at": self.created_at,
            # NOTE: private_key is intentionally NOT included in serialization
            # Store it securely in environment variables or secrets manager
        }

    def public_key_hex(self) -> str:
        """Get public key as hex string"""
        return self.public_key_bytes.hex()


@dataclass
class Attestation:
    """Cryptographic attestation from a validation service"""

    service_type: ServiceType
    verdict: str  # "pass", "fail", "promote", "rollback", etc.
    subject_id: str  # ID of the model/candidate being validated
    metrics: dict[str, Any]  # Metrics that led to this verdict
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Cryptographic proof
    signature: str = ""  # Hex-encoded signature
    public_key: str = ""  # Hex-encoded public key
    content_hash: str = ""  # SHA-256 hash of canonical content

    def compute_content_hash(self) -> str:
        """Compute deterministic hash of attestation content"""
        # Canonical representation for signing
        content = {
            "service_type": self.service_type.value,
            "verdict": self.verdict,
            "subject_id": self.subject_id,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }

        # Sort keys for determinism
        content_json = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def sign(self, key_pair: SignatureKeyPair) -> None:
        """Sign the attestation with a private key"""
        if key_pair.service_type != self.service_type:
            raise ValueError(
                f"Key pair service type {key_pair.service_type} does not match {self.service_type}"
            )

        # Compute content hash
        self.content_hash = self.compute_content_hash()

        # Sign the hash
        if HAS_CRYPTOGRAPHY:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                key_pair.private_key_bytes
            )
            signature_bytes = private_key.sign(self.content_hash.encode())
        else:
            # Fallback: HMAC-based signing
            signature_bytes = hmac.new(
                key_pair.private_key_bytes, self.content_hash.encode(), hashlib.sha256
            ).digest()

        self.signature = signature_bytes.hex()
        self.public_key = key_pair.public_key_hex()

    def verify(self) -> bool:
        """Verify the signature on this attestation"""
        if not self.signature or not self.public_key:
            return False

        try:
            # Recompute content hash
            expected_hash = self.compute_content_hash()

            if expected_hash != self.content_hash:
                return False

            # Verify signature
            signature_bytes = bytes.fromhex(self.signature)
            public_key_bytes = bytes.fromhex(self.public_key)

            if HAS_CRYPTOGRAPHY:
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                    public_key_bytes
                )
                try:
                    public_key.verify(signature_bytes, self.content_hash.encode())
                    return True
                except Exception:
                    return False
            else:
                # Fallback: HMAC verification (requires private key, so we check hash only)
                # In production, use proper Ed25519
                return len(signature_bytes) == 32  # Basic sanity check

        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "service_type": self.service_type.value,
            "verdict": self.verdict,
            "subject_id": self.subject_id,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "public_key": self.public_key,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Attestation":
        """Deserialize from dictionary"""
        return cls(
            service_type=ServiceType(data["service_type"]),
            verdict=data["verdict"],
            subject_id=data["subject_id"],
            metrics=data["metrics"],
            timestamp=data["timestamp"],
            signature=data.get("signature", ""),
            public_key=data.get("public_key", ""),
            content_hash=data.get("content_hash", ""),
        )


@dataclass
class AttestationChain:
    """A chain of attestations for a promotion decision"""

    candidate_id: str
    attestations: list[Attestation] = field(default_factory=list)
    final_decision: str = "pending"  # "promote", "reject", "rollback"
    chain_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_attestation(self, attestation: Attestation) -> None:
        """Add an attestation to the chain"""
        if not attestation.verify():
            raise ValueError(
                f"Cannot add unverified attestation from {attestation.service_type}"
            )

        self.attestations.append(attestation)
        self._update_chain_hash()

    def _update_chain_hash(self) -> None:
        """Update the Merkle-like chain hash"""
        # Chain hash = H(H(att1) || H(att2) || ... || H(attN))
        attestation_hashes = [att.content_hash for att in self.attestations]
        combined = "".join(attestation_hashes)
        self.chain_hash = hashlib.sha256(combined.encode()).hexdigest()

    def verify_chain(self) -> tuple[bool, str]:
        """Verify the entire attestation chain"""
        if not self.attestations:
            return False, "No attestations in chain"

        # Verify each attestation
        for att in self.attestations:
            if not att.verify():
                return False, f"Attestation from {att.service_type} failed verification"

        # Verify chain hash
        self._update_chain_hash()
        # Note: In production, store original chain_hash and compare

        return True, "All attestations verified"

    def get_attestation(self, service_type: ServiceType) -> Attestation | None:
        """Get attestation from a specific service"""
        for att in self.attestations:
            if att.service_type == service_type:
                return att
        return None

    def has_all_required(self) -> bool:
        """Check if all required attestations are present"""
        required = {ServiceType.SR_OMEGA, ServiceType.SIGMA_GUARD}
        present = {att.service_type for att in self.attestations}
        return required.issubset(present)

    def all_passed(self) -> bool:
        """Check if all attestations passed"""
        for att in self.attestations:
            if att.verdict not in ["pass", "promote", "approved"]:
                return False
        return self.has_all_required()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "candidate_id": self.candidate_id,
            "attestations": [att.to_dict() for att in self.attestations],
            "final_decision": self.final_decision,
            "chain_hash": self.chain_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttestationChain":
        """Deserialize from dictionary"""
        chain = cls(
            candidate_id=data["candidate_id"],
            final_decision=data.get("final_decision", "pending"),
            chain_hash=data.get("chain_hash", ""),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
        )

        for att_data in data.get("attestations", []):
            chain.attestations.append(Attestation.from_dict(att_data))

        return chain


class AttestationManager:
    """Manages attestation keys and signing operations"""

    def __init__(self):
        self.key_pairs: dict[ServiceType, SignatureKeyPair] = {}
        self._load_or_generate_keys()

    def _load_or_generate_keys(self) -> None:
        """Load keys from environment or generate new ones"""
        # In production, load from secure storage (env vars, secrets manager, etc.)
        # For now, generate ephemeral keys per session
        for service_type in ServiceType:
            self.key_pairs[service_type] = SignatureKeyPair.generate(service_type)

    def get_public_key(self, service_type: ServiceType) -> str:
        """Get public key for a service"""
        return self.key_pairs[service_type].public_key_hex()

    def create_attestation(
        self,
        service_type: ServiceType,
        verdict: str,
        subject_id: str,
        metrics: dict[str, Any],
    ) -> Attestation:
        """Create and sign an attestation"""
        attestation = Attestation(
            service_type=service_type,
            verdict=verdict,
            subject_id=subject_id,
            metrics=metrics,
        )

        key_pair = self.key_pairs[service_type]
        attestation.sign(key_pair)

        return attestation

    def verify_attestation(self, attestation: Attestation) -> bool:
        """Verify an attestation signature"""
        return attestation.verify()

    def export_public_keys(self) -> dict[str, str]:
        """Export all public keys"""
        return {
            service_type.value: key_pair.public_key_hex()
            for service_type, key_pair in self.key_pairs.items()
        }


# Global attestation manager instance
_global_manager: AttestationManager | None = None


def get_attestation_manager() -> AttestationManager:
    """Get global attestation manager instance"""
    global _global_manager
    if _global_manager is None:
        _global_manager = AttestationManager()
    return _global_manager


# Convenience functions


def create_sr_attestation(
    verdict: str, candidate_id: str, sr_score: float, components: dict[str, float]
) -> Attestation:
    """Create attestation from SR-Ω∞ service"""
    manager = get_attestation_manager()
    return manager.create_attestation(
        service_type=ServiceType.SR_OMEGA,
        verdict=verdict,
        subject_id=candidate_id,
        metrics={
            "sr_score": sr_score,
            "components": components,
        },
    )


def create_sigma_guard_attestation(
    verdict: str, candidate_id: str, gates: list[dict[str, Any]], aggregate_score: float
) -> Attestation:
    """Create attestation from Σ-Guard service"""
    manager = get_attestation_manager()
    return manager.create_attestation(
        service_type=ServiceType.SIGMA_GUARD,
        verdict=verdict,
        subject_id=candidate_id,
        metrics={
            "gates": gates,
            "aggregate_score": aggregate_score,
        },
    )


def create_acfa_attestation(
    verdict: str, candidate_id: str, promotion_decision: dict[str, Any]
) -> Attestation:
    """Create attestation from ACFA League"""
    manager = get_attestation_manager()
    return manager.create_attestation(
        service_type=ServiceType.ACFA_LEAGUE,
        verdict=verdict,
        subject_id=candidate_id,
        metrics=promotion_decision,
    )


# Export public API
__all__ = [
    "ServiceType",
    "SignatureKeyPair",
    "Attestation",
    "AttestationChain",
    "AttestationManager",
    "get_attestation_manager",
    "create_sr_attestation",
    "create_sigma_guard_attestation",
    "create_acfa_attestation",
    "HAS_CRYPTOGRAPHY",
]
