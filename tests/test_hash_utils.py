"""
Tests for PENIN-Ω Hash Utilities

Comprehensive tests for:
- Hash computation with multiple algorithms
- Backward compatibility with SHA-256
- Hash verification
- Algorithm detection
- Performance benchmarks
- Keyed hashing
"""

import json

import pytest

from penin.ledger.hash_utils import (
    HASH_ALGORITHM,
    HASH_DIGEST_SIZE,
    HASH_VERSION,
    LEGACY_HASH_ALGORITHM,
    LEGACY_HASH_VERSION,
    benchmark_hash_algorithms,
    compute_hash,
    compute_hash_legacy,
    detect_hash_algorithm,
    hash_json,
    hash_string,
    keyed_hash,
    verify_hash,
)


class TestHashComputation:
    """Test hash computation with different algorithms."""

    def test_compute_hash_blake2b(self):
        """Test BLAKE2b hash computation."""
        data = b"test data for hashing"
        hash_value = compute_hash(data, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # 256 bits = 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_sha256(self):
        """Test SHA-256 hash computation."""
        data = b"test data for hashing"
        hash_value = compute_hash(data, algorithm="sha256")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_sha3_256(self):
        """Test SHA3-256 hash computation."""
        data = b"test data for hashing"
        hash_value = compute_hash(data, algorithm="sha3_256")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_invalid_algorithm(self):
        """Test error handling for invalid algorithm."""
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            compute_hash(b"test", algorithm="invalid")

    def test_compute_hash_deterministic(self):
        """Test that hash computation is deterministic."""
        data = b"deterministic test data"

        hash1 = compute_hash(data, algorithm="blake2b")
        hash2 = compute_hash(data, algorithm="blake2b")

        assert hash1 == hash2

    def test_compute_hash_different_algorithms(self):
        """Test that different algorithms produce different hashes."""
        data = b"test data"

        blake2b_hash = compute_hash(data, algorithm="blake2b")
        sha256_hash = compute_hash(data, algorithm="sha256")
        sha3_256_hash = compute_hash(data, algorithm="sha3_256")

        # All should be different
        assert blake2b_hash != sha256_hash
        assert blake2b_hash != sha3_256_hash
        assert sha256_hash != sha3_256_hash

    def test_compute_hash_empty_data(self):
        """Test hash computation with empty data."""
        hash_value = compute_hash(b"", algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_compute_hash_large_data(self):
        """Test hash computation with large data."""
        # Simulate large ledger entry
        large_data = b"x" * 1_000_000  # 1 MB

        hash_value = compute_hash(large_data, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestBackwardCompatibility:
    """Test backward compatibility with SHA-256."""

    def test_compute_hash_legacy(self):
        """Test legacy SHA-256 hash computation."""
        data = b"legacy test data"
        legacy_hash = compute_hash_legacy(data)

        # Should be identical to SHA-256
        sha256_hash = compute_hash(data, algorithm="sha256")
        assert legacy_hash == sha256_hash

    def test_legacy_constants(self):
        """Test legacy constants."""
        assert LEGACY_HASH_ALGORITHM == "sha256"
        assert LEGACY_HASH_VERSION == "1.0"
        assert HASH_VERSION == "2.0"

    def test_current_algorithm(self):
        """Test current algorithm is BLAKE2b."""
        assert HASH_ALGORITHM == "blake2b"
        assert HASH_DIGEST_SIZE == 32


class TestHashVerification:
    """Test hash verification."""

    def test_verify_hash_success(self):
        """Test successful hash verification."""
        data = b"verify this data"
        expected_hash = compute_hash(data, algorithm="blake2b")

        assert verify_hash(data, expected_hash, algorithm="blake2b")

    def test_verify_hash_failure(self):
        """Test failed hash verification."""
        data = b"original data"
        wrong_hash = "0" * 64

        assert not verify_hash(data, wrong_hash, algorithm="blake2b")

    def test_verify_hash_modified_data(self):
        """Test verification fails with modified data."""
        original_data = b"original data"
        modified_data = b"modified data"
        hash_value = compute_hash(original_data, algorithm="blake2b")

        assert not verify_hash(modified_data, hash_value, algorithm="blake2b")

    def test_verify_hash_different_algorithm(self):
        """Test verification with different algorithms."""
        data = b"test data"
        blake2b_hash = compute_hash(data, algorithm="blake2b")

        # Should fail if verifying with wrong algorithm
        assert not verify_hash(data, blake2b_hash, algorithm="sha256")


class TestAlgorithmDetection:
    """Test hash algorithm detection."""

    def test_detect_blake2b_256(self):
        """Test detection of BLAKE2b-256 hash."""
        hash_value = "a" * 64  # 256-bit hash
        algorithm = detect_hash_algorithm(hash_value)

        # Should return current algorithm
        assert algorithm == HASH_ALGORITHM

    def test_detect_blake2b_512(self):
        """Test detection of BLAKE2b-512 hash."""
        hash_value = "a" * 128  # 512-bit hash
        algorithm = detect_hash_algorithm(hash_value)

        assert algorithm == "blake2b"

    def test_detect_invalid_length(self):
        """Test error handling for invalid hash length."""
        with pytest.raises(ValueError, match="Unknown hash length"):
            detect_hash_algorithm("invalid")


class TestUtilityFunctions:
    """Test utility functions."""

    def test_hash_string(self):
        """Test string hashing."""
        text = "test string for hashing"
        hash_value = hash_string(text, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

        # Should be deterministic
        assert hash_string(text, algorithm="blake2b") == hash_value

    def test_hash_string_unicode(self):
        """Test string hashing with Unicode."""
        text = "测试 тест 🎉"
        hash_value = hash_string(text, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_hash_json_simple(self):
        """Test JSON hashing with simple object."""
        obj = {"key": "value", "number": 42}
        hash_value = hash_json(obj, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_hash_json_deterministic(self):
        """Test JSON hashing is deterministic regardless of key order."""
        obj1 = {"a": 1, "b": 2, "c": 3}
        obj2 = {"c": 3, "b": 2, "a": 1}

        hash1 = hash_json(obj1, algorithm="blake2b")
        hash2 = hash_json(obj2, algorithm="blake2b")

        # Should be identical due to sorted keys
        assert hash1 == hash2

    def test_hash_json_nested(self):
        """Test JSON hashing with nested objects."""
        obj = {
            "event_type": "evaluate",
            "payload": {"metrics": {"U": 0.85, "S": 0.90}, "gates": {"sigma_guard_ok": True}},
            "sequence": 12345,
        }

        hash_value = hash_json(obj, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestKeyedHashing:
    """Test keyed hashing for authentication."""

    def test_keyed_hash_blake2b(self):
        """Test BLAKE2b keyed hashing."""
        data = b"authenticated data"
        key = b"secret_key_12345"

        hash_value = keyed_hash(data, key, algorithm="blake2b")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_keyed_hash_different_keys(self):
        """Test that different keys produce different hashes."""
        data = b"data to authenticate"
        key1 = b"key_one"
        key2 = b"key_two"

        hash1 = keyed_hash(data, key1, algorithm="blake2b")
        hash2 = keyed_hash(data, key2, algorithm="blake2b")

        assert hash1 != hash2

    def test_keyed_hash_sha256_fallback(self):
        """Test HMAC fallback for SHA-256."""
        data = b"data"
        key = b"key"

        hash_value = keyed_hash(data, key, algorithm="sha256")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_keyed_hash_sha3_256_fallback(self):
        """Test HMAC fallback for SHA3-256."""
        data = b"data"
        key = b"key"

        hash_value = keyed_hash(data, key, algorithm="sha3_256")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_keyed_hash_invalid_algorithm(self):
        """Test error handling for invalid algorithm."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            keyed_hash(b"data", b"key", algorithm="invalid")


class TestPerformanceBenchmark:
    """Test performance benchmarking."""

    def test_benchmark_hash_algorithms(self):
        """Test benchmarking of hash algorithms."""
        test_data = b"test data for benchmarking"
        results = benchmark_hash_algorithms(test_data, iterations=100)

        # Check all algorithms are benchmarked
        assert "blake2b" in results
        assert "sha256" in results
        assert "sha3_256" in results

        # Check results are positive numbers
        assert all(time > 0 for time in results.values())

    def test_benchmark_realistic_data(self):
        """Test benchmarking with realistic ledger data."""
        # Simulate realistic ledger entry
        ledger_data = json.dumps(
            {
                "event_type": "evaluate",
                "event_id": "test-001",
                "timestamp": "2024-01-01T00:00:00Z",
                "payload": {"metrics": {"U": 0.85, "S": 0.90, "C": 0.75, "L": 0.80}},
                "previous_hash": "0" * 64,
                "sequence_number": 12345,
            },
            sort_keys=True,
        ).encode()

        results = benchmark_hash_algorithms(ledger_data, iterations=1000)

        # All benchmarks should complete successfully
        assert len(results) == 3


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_ledger_event_hashing(self):
        """Test hashing of a complete ledger event."""
        event_data = {
            "event_type": "promote",
            "event_id": "evt-001",
            "timestamp": "2024-01-15T10:30:00Z",
            "payload": {
                "metrics": {"U": 0.92, "S": 0.88, "C": 0.70, "L": 0.85},
                "gates": {"sigma_guard_ok": True, "ir_ic_ok": True},
                "decision": {"verdict": "promote", "reason": "metrics improved"},
            },
            "previous_hash": "0" * 64,
            "sequence_number": 100,
        }

        # Hash the event
        event_hash = hash_json(event_data, algorithm="blake2b")

        # Verify the hash
        canonical_bytes = json.dumps(event_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        assert verify_hash(canonical_bytes, event_hash, algorithm="blake2b")

    def test_hash_chain_simulation(self):
        """Test simulation of a hash chain."""
        previous_hash = None
        hashes = []

        # Create a chain of 10 events
        for i in range(10):
            event = {
                "sequence": i,
                "data": f"event_{i}",
                "previous_hash": previous_hash,
            }

            event_hash = hash_json(event, algorithm="blake2b")
            hashes.append(event_hash)
            previous_hash = event_hash

        # Verify chain integrity
        assert len(hashes) == 10
        assert len(set(hashes)) == 10  # All hashes should be unique

    def test_migration_scenario(self):
        """Test migration scenario from SHA-256 to BLAKE2b."""
        data = b"data to migrate"

        # Old system uses SHA-256
        old_hash = compute_hash(data, algorithm="sha256")
        assert len(old_hash) == 64

        # New system uses BLAKE2b
        new_hash = compute_hash(data, algorithm="blake2b")
        assert len(new_hash) == 64

        # Hashes should be different
        assert old_hash != new_hash

        # Both should verify correctly with their respective algorithms
        assert verify_hash(data, old_hash, algorithm="sha256")
        assert verify_hash(data, new_hash, algorithm="blake2b")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
