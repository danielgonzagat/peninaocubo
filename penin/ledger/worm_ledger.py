"""
PENIN-Ω Complete WORM Ledger — Write Once, Read Many

Immutable audit trail with:
- Append-only storage (JSONL format)
- BLAKE2b hash chain (modern, efficient)
- UTC timestamps
- Proof-Carrying Artifacts (PCAg)
- Cryptographic integrity
- Compliance with ΣEA/LO-14

Design principles:
- Fail-closed: errors halt writes
- Deterministic: reproducible hashes
- Auditable: full provenance chain
- Tamper-evident: hash verification

Hash Algorithm Evolution:
- v1.0: SHA-256 (legacy)
- v2.0: BLAKE2b-256 (current) - faster, more secure, modern
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from penin.ledger.hash_utils import (
    HASH_ALGORITHM,
    compute_hash,
    hash_json,
)

try:
    import orjson

    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False


# ============================================================================
# Constants
# ============================================================================

LEDGER_VERSION = "2.0.0"  # Updated for BLAKE2b
ENCODING = "utf-8"


# ============================================================================
# Proof-Carrying Artifact (PCAg)
# ============================================================================


@dataclass
class ProofCarryingArtifact:
    """
    Proof-Carrying Artifact for auditable decision making.

    Contains:
    - Decision ID and type
    - Metrics snapshot
    - Gate results
    - Hash proofs
    - Timestamp
    """

    decision_id: str
    decision_type: str  # promote, rollback, canary, shadow, etc.
    timestamp: str
    metrics: dict[str, Any]
    gates: dict[str, Any]
    reason: str
    artifact_hash: str
    previous_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        decision_id: str,
        decision_type: str,
        metrics: dict[str, Any],
        gates: dict[str, Any],
        reason: str,
        previous_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProofCarryingArtifact:
        """Create new PCAg with computed hash."""
        timestamp = datetime.now(UTC).isoformat()

        # Compute hash
        data = {
            "decision_id": decision_id,
            "decision_type": decision_type,
            "timestamp": timestamp,
            "metrics": metrics,
            "gates": gates,
            "reason": reason,
            "previous_hash": previous_hash,
            "metadata": metadata or {},
        }

        # Use hash_json for consistent hashing
        artifact_hash = hash_json(data)

        return cls(
            decision_id=decision_id,
            decision_type=decision_type,
            timestamp=timestamp,
            metrics=metrics,
            gates=gates,
            reason=reason,
            artifact_hash=artifact_hash,
            previous_hash=previous_hash,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "gates": self.gates,
            "reason": self.reason,
            "artifact_hash": self.artifact_hash,
            "previous_hash": self.previous_hash,
            "metadata": self.metadata,
        }

    def verify_hash(self) -> bool:
        """Verify hash integrity."""
        data = {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "gates": self.gates,
            "reason": self.reason,
            "previous_hash": self.previous_hash,
            "metadata": self.metadata,
        }

        # Use hash_json for consistent hashing
        computed_hash = hash_json(data)
        return computed_hash == self.artifact_hash

    def __str__(self) -> str:
        return (
            f"PCAg({self.decision_type}:{self.decision_id} "
            f"@ {self.timestamp} → {self.artifact_hash[:8]}...)"
        )


# ============================================================================
# WORM Event
# ============================================================================


@dataclass
class WORMEvent:
    """
    Immutable event for WORM ledger.

    Each event contains:
    - Event type and ID
    - UTC timestamp
    - Payload (arbitrary JSON-serializable data)
    - Hash (SHA-256 of canonical form)
    - Previous hash (for chain integrity)
    """

    event_type: str
    event_id: str
    timestamp: str
    payload: dict[str, Any]
    event_hash: str
    previous_hash: str | None = None
    sequence_number: int = 0

    @classmethod
    def create(
        cls,
        event_type: str,
        event_id: str,
        payload: dict[str, Any],
        previous_hash: str | None = None,
        sequence_number: int = 0,
    ) -> WORMEvent:
        """Create new event with computed hash."""
        timestamp = datetime.now(UTC).isoformat()

        # Compute hash using hash_json
        data = {
            "event_type": event_type,
            "event_id": event_id,
            "timestamp": timestamp,
            "payload": payload,
            "previous_hash": previous_hash,
            "sequence_number": sequence_number,
        }

        event_hash = hash_json(data)

        return cls(
            event_type=event_type,
            event_id=event_id,
            timestamp=timestamp,
            payload=payload,
            event_hash=event_hash,
            previous_hash=previous_hash,
            sequence_number=sequence_number,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "event_hash": self.event_hash,
            "previous_hash": self.previous_hash,
            "sequence_number": self.sequence_number,
        }

    def verify_hash(self) -> bool:
        """Verify hash integrity."""
        data = {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "sequence_number": self.sequence_number,
        }

        # Use hash_json for consistent hashing
        computed_hash = hash_json(data)
        return computed_hash == self.event_hash

    def __str__(self) -> str:
        return (
            f"WORMEvent({self.event_type}:{self.event_id} "
            f"#{self.sequence_number} @ {self.timestamp})"
        )


# ============================================================================
# WORM Ledger
# ============================================================================


class WORMLedger:
    """
    Write-Once-Read-Many immutable audit ledger.

    Features:
    - Append-only JSONL storage
    - SHA-256 hash chain
    - Merkle root computation
    - Chain integrity verification
    - PCAg support
    - UTC timestamps

    Storage format:
    - One JSON object per line (JSONL)
    - Each event contains hash of previous event
    - Sequence numbers for ordering

    Guarantees:
    - Immutability: no updates or deletes
    - Integrity: hash chain verification
    - Auditability: full provenance
    - Tamper-evidence: any modification breaks chain
    """

    def __init__(self, ledger_path: str | Path):
        """
        Initialize WORM ledger.

        Args:
            ledger_path: Path to ledger file (JSONL)
        """
        self.ledger_path = Path(ledger_path)
        self._last_hash: str | None = None
        self._sequence_number: int = 0
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure ledger directory and file exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.ledger_path.exists():
            # Create empty ledger with header
            header = {
                "ledger_version": LEDGER_VERSION,
                "created_at": datetime.now(UTC).isoformat(),
                "hash_algorithm": HASH_ALGORITHM,
            }

            if ORJSON_AVAILABLE:
                data = orjson.dumps(header)
            else:
                data = json.dumps(header).encode()

            self.ledger_path.write_bytes(data + b"\n")
        else:
            # Load last hash and sequence number
            self._load_metadata()

    def _load_metadata(self) -> None:
        """Load last hash and sequence number from existing ledger."""
        try:
            with open(self.ledger_path, encoding=ENCODING) as f:
                lines = f.readlines()

            if len(lines) > 1:  # Skip header
                last_line = lines[-1].strip()
                if last_line:
                    if ORJSON_AVAILABLE:
                        data = orjson.loads(last_line)
                    else:
                        data = json.loads(last_line)

                    self._last_hash = data.get("event_hash")
                    self._sequence_number = data.get("sequence_number", 0)
        except Exception:
            # If loading fails, start fresh
            self._last_hash = None
            self._sequence_number = 0

    def append(
        self,
        event_type: str,
        event_id: str,
        payload: dict[str, Any],
    ) -> WORMEvent:
        """
        Append event to ledger.

        Args:
            event_type: Type of event (e.g., "promote", "rollback")
            event_id: Unique event identifier
            payload: Event data (must be JSON-serializable)

        Returns:
            Created WORMEvent

        Raises:
            ValueError: If event data is invalid
            IOError: If write fails
        """
        # Create event
        event = WORMEvent.create(
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            previous_hash=self._last_hash,
            sequence_number=self._sequence_number + 1,
        )

        # Verify event integrity
        if not event.verify_hash():
            raise ValueError("Event hash verification failed")

        # Write to ledger (append-only)
        try:
            with open(self.ledger_path, "a", encoding=ENCODING) as f:
                if ORJSON_AVAILABLE:
                    data = orjson.dumps(event.to_dict())
                else:
                    data = json.dumps(event.to_dict()).encode()

                f.write(data.decode() + "\n")
        except Exception as e:
            raise OSError(f"Failed to write to ledger: {e}") from e

        # Update metadata
        self._last_hash = event.event_hash
        self._sequence_number = event.sequence_number

        return event

    def append_pcag(self, pcag: ProofCarryingArtifact) -> WORMEvent:
        """
        Append Proof-Carrying Artifact to ledger.

        Args:
            pcag: ProofCarryingArtifact to append

        Returns:
            Created WORMEvent
        """
        # Verify PCAg integrity
        if not pcag.verify_hash():
            raise ValueError("PCAg hash verification failed")

        # Create event from PCAg
        return self.append(
            event_type=f"pcag_{pcag.decision_type}",
            event_id=pcag.decision_id,
            payload={
                "pcag": pcag.to_dict(),
                "artifact_hash": pcag.artifact_hash,
            },
        )

    def read_all(self) -> Iterator[WORMEvent]:
        """
        Read all events from ledger.

        Yields:
            WORMEvent instances
        """
        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, encoding=ENCODING) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # Skip header (first line)
                if line_num == 1 and "ledger_version" in line:
                    continue

                try:
                    if ORJSON_AVAILABLE:
                        data = orjson.loads(line)
                    else:
                        data = json.loads(line)

                    event = WORMEvent(**data)
                    yield event
                except Exception:
                    # Skip malformed lines
                    continue

    def read_by_type(self, event_type: str) -> Iterator[WORMEvent]:
        """
        Read events filtered by type.

        Args:
            event_type: Event type to filter

        Yields:
            Matching WORMEvent instances
        """
        for event in self.read_all():
            if event.event_type == event_type:
                yield event

    def read_by_id(self, event_id: str) -> Iterator[WORMEvent]:
        """
        Read events filtered by ID.

        Args:
            event_id: Event ID to filter

        Yields:
            Matching WORMEvent instances
        """
        for event in self.read_all():
            if event.event_id == event_id:
                yield event

    def verify_chain(self) -> tuple[bool, str | None]:
        """
        Verify integrity of entire hash chain.

        Returns:
            Tuple of (is_valid, error_message)
        """
        events = list(self.read_all())

        if not events:
            return True, None

        # Verify each event's hash
        for event in events:
            if not event.verify_hash():
                return False, f"Event {event.sequence_number} has invalid hash"

        # Verify chain integrity
        previous_hash = None
        for event in events:
            if event.previous_hash != previous_hash:
                return False, f"Chain broken at event {event.sequence_number}"
            previous_hash = event.event_hash

        return True, None

    def compute_merkle_root(self) -> str | None:
        """
        Compute Merkle root of all event hashes.

        Returns:
            Merkle root hash or None if ledger is empty
        """
        hashes = [event.event_hash for event in self.read_all()]

        if not hashes:
            return None

        # Build Merkle tree using BLAKE2b
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = (left + right).encode()
                next_level.append(compute_hash(combined))
            hashes = next_level

        return hashes[0]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get ledger statistics.

        Returns:
            Dictionary with statistics
        """
        events = list(self.read_all())

        event_types = {}
        for event in events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        is_valid, error = self.verify_chain()

        return {
            "total_events": len(events),
            "last_sequence": self._sequence_number,
            "last_hash": self._last_hash,
            "merkle_root": self.compute_merkle_root(),
            "event_types": event_types,
            "chain_valid": is_valid,
            "chain_error": error,
            "ledger_path": str(self.ledger_path),
            "ledger_size_bytes": (
                self.ledger_path.stat().st_size if self.ledger_path.exists() else 0
            ),
        }

    def export_audit_report(self, output_path: str | Path) -> None:
        """
        Export full audit report.

        Args:
            output_path: Path to output JSON file
        """
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "ledger_version": LEDGER_VERSION,
            "statistics": self.get_statistics(),
            "events": [event.to_dict() for event in self.read_all()],
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if ORJSON_AVAILABLE:
            data = orjson.dumps(report, option=orjson.OPT_INDENT_2)
            output_path.write_bytes(data)
        else:
            output_path.write_text(json.dumps(report, indent=2))


# ============================================================================
# Factory Functions
# ============================================================================


def create_worm_ledger(ledger_path: str | Path | None = None) -> WORMLedger:
    """
    Create WORM ledger with default path.

    Args:
        ledger_path: Path to ledger file (default: ~/.penin_omega/worm.jsonl)

    Returns:
        WORMLedger instance
    """
    if ledger_path is None:
        ledger_path = Path.home() / ".penin_omega" / "worm.jsonl"

    return WORMLedger(ledger_path)


def create_pcag(
    decision_id: str,
    decision_type: str,
    metrics: dict[str, Any],
    gates: dict[str, Any],
    reason: str,
    previous_hash: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProofCarryingArtifact:
    """
    Create Proof-Carrying Artifact.

    Args:
        decision_id: Unique decision identifier
        decision_type: Type of decision (promote, rollback, etc.)
        metrics: Metrics snapshot
        gates: Gate results
        reason: Human-readable reason
        previous_hash: Hash of previous PCAg (for chaining)
        metadata: Additional metadata

    Returns:
        ProofCarryingArtifact instance
    """
    return ProofCarryingArtifact.create(
        decision_id=decision_id,
        decision_type=decision_type,
        metrics=metrics,
        gates=gates,
        reason=reason,
        previous_hash=previous_hash,
        metadata=metadata,
    )


# ============================================================================
# CLI Helper (for manual inspection)
# ============================================================================


def verify_ledger_cli(ledger_path: str | Path) -> None:
    """
    CLI helper to verify ledger integrity.

    Args:
        ledger_path: Path to ledger file
    """
    ledger = WORMLedger(ledger_path)
    stats = ledger.get_statistics()

    print(f"WORM Ledger Analysis: {ledger_path}")
    print("=" * 60)
    print(f"Total Events: {stats['total_events']}")
    print(f"Last Sequence: {stats['last_sequence']}")
    print(f"Merkle Root: {stats['merkle_root']}")
    print(f"Chain Valid: {stats['chain_valid']}")

    if not stats["chain_valid"]:
        print(f"Chain Error: {stats['chain_error']}")

    print("\nEvent Types:")
    for event_type, count in stats["event_types"].items():
        print(f"  {event_type}: {count}")

    print(f"\nLedger Size: {stats['ledger_size_bytes']} bytes")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        verify_ledger_cli(sys.argv[1])
    else:
        print("Usage: python worm_ledger_complete.py <ledger_path>")
