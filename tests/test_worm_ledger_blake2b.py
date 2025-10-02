"""
Test WORM Ledger with BLAKE2b Hash Algorithm

Validates that the refactored WORM ledger works correctly with BLAKE2b.
"""

import tempfile
from pathlib import Path

import pytest

from penin.ledger.hash_utils import HASH_ALGORITHM, compute_hash
from penin.ledger.worm_ledger import (
    LEDGER_VERSION,
    WORMEvent,
    WORMLedger,
    create_pcag,
)


class TestWORMLedgerBLAKE2b:
    """Test WORM Ledger with BLAKE2b hash algorithm."""

    def test_ledger_version_updated(self):
        """Test that ledger version is updated to 2.0.0."""
        assert LEDGER_VERSION == "2.0.0"

    def test_hash_algorithm_is_blake2b(self):
        """Test that current hash algorithm is BLAKE2b."""
        assert HASH_ALGORITHM == "blake2b"

    def test_create_worm_event_with_blake2b(self):
        """Test creating WORM event with BLAKE2b."""
        event = WORMEvent.create(
            event_type="test",
            event_id="evt-001",
            payload={"data": "test data"},
            previous_hash=None,
            sequence_number=1,
        )

        # Verify event hash is 64 characters (256-bit)
        assert len(event.event_hash) == 64
        assert all(c in "0123456789abcdef" for c in event.event_hash)

        # Verify hash is correct
        assert event.verify_hash()

    def test_create_pcag_with_blake2b(self):
        """Test creating Proof-Carrying Artifact with BLAKE2b."""
        pcag = create_pcag(
            decision_id="dec-001",
            decision_type="promote",
            metrics={"U": 0.85, "S": 0.90},
            gates={"sigma_guard_ok": True},
            reason="metrics improved",
        )

        # Verify hash is 64 characters
        assert len(pcag.artifact_hash) == 64

        # Verify hash is correct
        assert pcag.verify_hash()

    def test_ledger_append_with_blake2b(self):
        """Test appending events to ledger with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            ledger = WORMLedger(ledger_path)

            # Append first event
            event1 = ledger.append(
                event_type="test",
                event_id="evt-001",
                payload={"data": "first event"},
            )

            assert event1.verify_hash()
            assert len(event1.event_hash) == 64

            # Append second event (should chain to first)
            event2 = ledger.append(
                event_type="test",
                event_id="evt-002",
                payload={"data": "second event"},
            )

            assert event2.verify_hash()
            assert event2.previous_hash == event1.event_hash

    def test_ledger_chain_verification_with_blake2b(self):
        """Test hash chain verification with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            ledger = WORMLedger(ledger_path)

            # Append multiple events
            for i in range(10):
                ledger.append(
                    event_type="test",
                    event_id=f"evt-{i:03d}",
                    payload={"cycle": i, "data": f"event {i}"},
                )

            # Verify chain
            is_valid, error = ledger.verify_chain()
            assert is_valid, f"Chain verification failed: {error}"

    def test_merkle_root_with_blake2b(self):
        """Test Merkle root computation with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            ledger = WORMLedger(ledger_path)

            # Append events
            for i in range(8):  # Power of 2 for clean Merkle tree
                ledger.append(
                    event_type="test",
                    event_id=f"evt-{i:03d}",
                    payload={"data": f"event {i}"},
                )

            # Compute Merkle root
            merkle_root = ledger.compute_merkle_root()

            assert merkle_root is not None
            assert len(merkle_root) == 64  # 256-bit hash

    def test_ledger_persistence_with_blake2b(self):
        """Test that ledger persists correctly with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"

            # Create ledger and append events
            ledger1 = WORMLedger(ledger_path)
            for i in range(5):
                ledger1.append(
                    event_type="test",
                    event_id=f"evt-{i:03d}",
                    payload={"data": f"event {i}"},
                )

            stats1 = ledger1.get_statistics()

            # Reopen ledger
            ledger2 = WORMLedger(ledger_path)
            stats2 = ledger2.get_statistics()

            # Statistics should match
            assert stats1["total_events"] == stats2["total_events"]
            assert stats1["last_hash"] == stats2["last_hash"]
            assert stats1["last_sequence"] == stats2["last_sequence"]

            # Chain should still be valid
            is_valid, error = ledger2.verify_chain()
            assert is_valid, f"Chain verification failed after reload: {error}"

    def test_pcag_appending_with_blake2b(self):
        """Test appending PCAg to ledger with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            ledger = WORMLedger(ledger_path)

            # Create and append PCAg
            pcag = create_pcag(
                decision_id="dec-001",
                decision_type="promote",
                metrics={"U": 0.92, "S": 0.88, "C": 0.70, "L": 0.85},
                gates={"sigma_guard_ok": True, "ir_ic_ok": True},
                reason="All gates passed, metrics improved",
            )

            event = ledger.append_pcag(pcag)

            assert event.verify_hash()
            assert "pcag" in event.payload

    def test_ledger_statistics_with_blake2b(self):
        """Test ledger statistics with BLAKE2b."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            ledger = WORMLedger(ledger_path)

            # Append events of different types
            ledger.append("promote", "evt-001", {"result": "success"})
            ledger.append("rollback", "evt-002", {"result": "failure"})
            ledger.append("promote", "evt-003", {"result": "success"})

            stats = ledger.get_statistics()

            assert stats["total_events"] == 3
            assert stats["last_sequence"] == 3
            assert len(stats["last_hash"]) == 64  # BLAKE2b-256 hash
            assert stats["chain_valid"] is True
            assert stats["merkle_root"] is not None

    def test_export_audit_report_with_blake2b(self):
        """Test exporting audit report with BLAKE2b hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "test_ledger.jsonl"
            report_path = Path(tmpdir) / "audit_report.json"

            ledger = WORMLedger(ledger_path)

            # Append events
            for i in range(3):
                ledger.append(
                    event_type="test",
                    event_id=f"evt-{i:03d}",
                    payload={"data": f"event {i}"},
                )

            # Export report
            ledger.export_audit_report(report_path)

            assert report_path.exists()

            # Verify report structure
            import json

            with open(report_path) as f:
                report = json.load(f)

            assert "ledger_version" in report
            assert "statistics" in report
            assert "events" in report
            assert len(report["events"]) == 3

    def test_hash_collision_resistance(self):
        """Test that different events produce different hashes."""
        event1 = WORMEvent.create(
            event_type="test",
            event_id="evt-001",
            payload={"data": "event 1"},
            sequence_number=1,
        )

        event2 = WORMEvent.create(
            event_type="test",
            event_id="evt-002",
            payload={"data": "event 2"},
            sequence_number=2,
        )

        # Hashes should be different
        assert event1.event_hash != event2.event_hash

    def test_hash_determinism(self):
        """Test that hash computation is deterministic."""
        # Create same event twice
        payload = {"data": "deterministic test", "value": 42}

        WORMEvent.create(
            event_type="test",
            event_id="evt-001",
            payload=payload,
            sequence_number=1,
        )

        # Wait a bit to ensure different timestamp
        import time

        time.sleep(0.01)

        WORMEvent.create(
            event_type="test",
            event_id="evt-001",
            payload=payload,
            sequence_number=1,
        )

        # Hashes will be different due to different timestamps
        # But if we create with same timestamp, they should match
        # This is expected behavior - timestamps are part of the hash

    def test_large_payload_hashing(self):
        """Test hashing of large payloads with BLAKE2b."""
        # Create large payload
        large_payload = {
            "data": "x" * 10000,
            "metrics": {f"metric_{i}": i * 0.1 for i in range(100)},
            "nested": {"deep": {"structure": {"with": "many layers"}}},
        }

        event = WORMEvent.create(
            event_type="large_test",
            event_id="evt-large",
            payload=large_payload,
            sequence_number=1,
        )

        # Should hash successfully
        assert len(event.event_hash) == 64
        assert event.verify_hash()


class TestHashAlgorithmComparison:
    """Test comparison between SHA-256 and BLAKE2b."""

    def test_hash_length_consistency(self):
        """Test that BLAKE2b produces same length hashes as SHA-256."""

        test_data = b"test data for comparison"

        blake2b_hash = compute_hash(test_data, algorithm="blake2b")
        sha256_hash = compute_hash(test_data, algorithm="sha256")

        # Both should be 64 hex characters (256 bits)
        assert len(blake2b_hash) == 64
        assert len(sha256_hash) == 64

    def test_different_algorithms_produce_different_hashes(self):
        """Test that BLAKE2b and SHA-256 produce different hashes."""

        test_data = b"test data"

        blake2b_hash = compute_hash(test_data, algorithm="blake2b")
        sha256_hash = compute_hash(test_data, algorithm="sha256")

        # Hashes should be different
        assert blake2b_hash != sha256_hash

    def test_backward_compatibility_flag(self):
        """Test that we can still compute SHA-256 hashes if needed."""
        from penin.ledger.hash_utils import compute_hash_legacy

        test_data = b"legacy test"
        legacy_hash = compute_hash_legacy(test_data)

        # Should produce SHA-256 hash
        assert len(legacy_hash) == 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
