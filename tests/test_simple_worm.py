"""
Test Simple WORM Ledger
========================

Test persistent ledger with SQLite + hash chain.
"""

import pytest
import tempfile
from pathlib import Path


class TestSimpleWORMLedger:
    """Test simple WORM ledger"""

    def test_ledger_creates_db(self):
        """Test ledger creates database"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            ledger = SimpleWORMLedger(db_path=str(db_path))
            
            # DB should exist
            assert db_path.exists()

    def test_ledger_appends_entry(self):
        """Test appending entry"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            ledger = SimpleWORMLedger(db_path=str(db_path))
            
            entry_hash = ledger.append_entry(
                event_type="test",
                data={"key": "value"},
                decision="test_decision",
            )
            
            # Should return hash
            assert isinstance(entry_hash, str)
            assert len(entry_hash) == 64  # BLAKE2b-256

    def test_ledger_persistence(self):
        """Test ledger persists across instances"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            # First instance
            ledger1 = SimpleWORMLedger(db_path=str(db_path))
            ledger1.append_entry("test", {"n": 1}, "decision1")
            ledger1.append_entry("test", {"n": 2}, "decision2")
            
            # Second instance (reload)
            ledger2 = SimpleWORMLedger(db_path=str(db_path))
            
            # Should have loaded entries
            assert len(ledger2.entries) == 2
            assert ledger2.entries[0]['data']['n'] == 1

    def test_ledger_verifies_chain(self):
        """Test hash chain verification"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            ledger = SimpleWORMLedger(db_path=str(db_path))
            
            # Add entries
            for i in range(5):
                ledger.append_entry("test", {"n": i}, f"decision_{i}")
            
            # Chain should be valid
            assert ledger.verify_chain() is True

    def test_ledger_stats(self):
        """Test ledger statistics"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            ledger = SimpleWORMLedger(db_path=str(db_path))
            
            ledger.append_entry("type1", {}, "decision1")
            ledger.append_entry("type1", {}, "decision2")
            ledger.append_entry("type2", {}, "decision1")
            
            stats = ledger.stats()
            
            assert stats['total_entries'] == 3
            assert stats['event_types']['type1'] == 2
            assert stats['event_types']['type2'] == 1
            assert stats['chain_valid'] is True

    def test_ledger_get_entries(self):
        """Test filtering entries"""
        from penin.ledger.simple_worm import SimpleWORMLedger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            ledger = SimpleWORMLedger(db_path=str(db_path))
            
            ledger.append_entry("type1", {}, "decision1")
            ledger.append_entry("type2", {}, "decision2")
            ledger.append_entry("type1", {}, "decision3")
            
            # Filter by type
            type1_entries = ledger.get_entries(event_type="type1")
            assert len(type1_entries) == 2
            
            # Limit
            limited = ledger.get_entries(limit=2)
            assert len(limited) == 2
