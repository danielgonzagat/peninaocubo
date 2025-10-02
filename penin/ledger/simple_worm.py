"""
Simple WORM Ledger
==================

Write-Once-Read-Many ledger with:
- SQLite persistent storage
- BLAKE2b hash chain
- Integrity verification
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SimpleWORMLedger:
    """
    Simple but functional WORM ledger.
    
    Features:
    - Append-only (immutable)
    - Hash chain (Merkle-like)
    - SQLite persistence
    - Integrity verification
    """
    
    def __init__(self, db_path: str = "./data/worm_ledger.db"):
        self.db_path = db_path
        self.entries = []
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Load existing entries
        self._load_entries()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data_json TEXT NOT NULL,
                decision TEXT NOT NULL,
                prev_hash TEXT,
                entry_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON ledger(timestamp);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type ON ledger(event_type);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_hash ON ledger(entry_hash);
        """)
        conn.commit()
        conn.close()
    
    def _load_entries(self):
        """Load entries from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT timestamp, event_type, data_json, decision, prev_hash, entry_hash
            FROM ledger
            ORDER BY id ASC
        """)
        
        for row in cursor.fetchall():
            entry = {
                'timestamp': row[0],
                'event_type': row[1],
                'data': json.loads(row[2]),
                'decision': row[3],
                'prev_hash': row[4],
                'entry_hash': row[5],
            }
            self.entries.append(entry)
        
        conn.close()
    
    def append_entry(
        self,
        event_type: str,
        data: Dict,
        decision: str,
    ) -> str:
        """
        Append entry to WORM ledger (immutable).
        
        Args:
            event_type: Type of event (e.g., 'evolution_cycle', 'mutation_decision')
            data: Event data (must be JSON-serializable)
            decision: Decision made (e.g., 'PROMOTE', 'REJECT')
        
        Returns:
            Entry hash (BLAKE2b-256)
        """
        
        # Get timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Serialize data
        data_json = json.dumps(data, sort_keys=True)
        
        # Get previous hash (chain)
        prev_hash = self.entries[-1]['entry_hash'] if self.entries else "GENESIS"
        
        # Compute hash (BLAKE2b for speed + security)
        hash_input = f"{timestamp}|{event_type}|{data_json}|{decision}|{prev_hash}"
        entry_hash = hashlib.blake2b(
            hash_input.encode('utf-8'),
            digest_size=32  # 256 bits
        ).hexdigest()
        
        # Insert into database
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO ledger (timestamp, event_type, data_json, decision, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, event_type, data_json, decision, prev_hash, entry_hash))
            conn.commit()
        finally:
            conn.close()
        
        # Add to cache
        entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'data': data,
            'decision': decision,
            'prev_hash': prev_hash,
            'entry_hash': entry_hash,
        }
        self.entries.append(entry)
        
        return entry_hash
    
    def verify_chain(self) -> bool:
        """
        Verify hash chain integrity.
        
        Returns:
            True if chain is valid, False otherwise
        """
        
        for i, entry in enumerate(self.entries):
            # Recompute hash
            timestamp = entry['timestamp']
            event_type = entry['event_type']
            data_json = json.dumps(entry['data'], sort_keys=True)
            decision = entry['decision']
            prev_hash = entry['prev_hash']
            
            hash_input = f"{timestamp}|{event_type}|{data_json}|{decision}|{prev_hash}"
            expected_hash = hashlib.blake2b(
                hash_input.encode('utf-8'),
                digest_size=32
            ).hexdigest()
            
            if expected_hash != entry['entry_hash']:
                print(f"❌ Chain broken at entry {i} (expected={expected_hash[:16]}, got={entry['entry_hash'][:16]})")
                return False
            
            # Verify chain link
            if i > 0:
                if prev_hash != self.entries[i-1]['entry_hash']:
                    print(f"❌ Chain link broken at entry {i}")
                    return False
        
        return True
    
    def get_entries(
        self,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get entries with optional filtering.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of entries
        
        Returns:
            List of entries
        """
        
        entries = self.entries
        
        if event_type:
            entries = [e for e in entries if e['event_type'] == event_type]
        
        if limit:
            entries = entries[-limit:]  # Get last N
        
        return entries
    
    def stats(self) -> Dict:
        """Get ledger statistics"""
        
        event_types = {}
        decisions = {}
        
        for entry in self.entries:
            event_type = entry['event_type']
            decision = entry['decision']
            
            event_types[event_type] = event_types.get(event_type, 0) + 1
            decisions[decision] = decisions.get(decision, 0) + 1
        
        return {
            'total_entries': len(self.entries),
            'event_types': event_types,
            'decisions': decisions,
            'chain_valid': self.verify_chain(),
            'db_path': self.db_path,
        }
