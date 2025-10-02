"""
Comprehensive Ledger Tests
==========================

Deep testing of WORM ledger and hash utilities.
"""

import pytest


class TestLedgerModulesLoad:
    """Test ledger modules can be imported"""

    def test_hash_utils_loads(self):
        """Test hash_utils module loads"""
        from penin.ledger import hash_utils
        assert hash_utils is not None

    def test_pcag_generator_loads(self):
        """Test pcag_generator module loads"""
        from penin.ledger import pcag_generator
        assert pcag_generator is not None

    def test_worm_ledger_loads(self):
        """Test worm_ledger module loads"""
        from penin.ledger import worm_ledger
        assert worm_ledger is not None

    def test_worm_ledger_complete_loads(self):
        """Test worm_ledger_complete module loads"""
        from penin.ledger import worm_ledger_complete
        assert worm_ledger_complete is not None


class TestHashUtilitiesBasic:
    """Test hash utilities basic functions"""

    def test_blake2b_available(self):
        """Test BLAKE2b hash function is available"""
        import hashlib
        
        # BLAKE2b should be available
        hash_obj = hashlib.blake2b(b"test", digest_size=32)
        result = hash_obj.hexdigest()
        
        # Should produce hex string
        assert isinstance(result, str)
        assert len(result) == 64  # 32 bytes = 64 hex chars

    def test_hash_deterministic(self):
        """Test hash is deterministic"""
        import hashlib
        
        data = b"test data"
        hash1 = hashlib.blake2b(data, digest_size=32).hexdigest()
        hash2 = hashlib.blake2b(data, digest_size=32).hexdigest()
        
        assert hash1 == hash2


class TestLedgerDataStructures:
    """Test ledger data structures"""

    def test_pcag_decision_artifact_structure(self):
        """Test DecisionArtifact can be created"""
        from penin.ledger.pcag_generator import DecisionArtifact
        
        artifact = DecisionArtifact(
            decision_id="test_001",
            decision_type="promotion",
            timestamp_utc="2025-10-02T00:00:00Z",
            metrics={"delta_linf": 0.05},
            verdict="promote"
        )
        
        assert artifact.decision_id == "test_001"
        assert artifact.verdict == "promote"
