"""
Enhanced cache module with HMAC integrity protection.
Uses orjson for serialization instead of pickle for security.
"""

import os
import time
import sqlite3
import hmac
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from collections import OrderedDict

import orjson


class SecureCache:
    """
    Multi-level cache with HMAC integrity protection.
    L1: In-memory LRU cache
    L2: SQLite with orjson + HMAC
    """
    
    def __init__(
        self,
        l1_size: int = 1000,
        l2_size: int = 10000,
        l1_ttl: int = 60,
        l2_ttl: int = 3600,
        cache_dir: Optional[Path] = None,
    ):
        self.l1_size = l1_size
        self.l2_size = l2_size
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        
        # L1: In-memory cache
        self.l1_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # L2: SQLite cache with HMAC
        if cache_dir is None:
            cache_dir = Path.home() / ".penin" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.l2_db_path = cache_dir / "l2_cache.db"
        self.l2_db = sqlite3.connect(str(self.l2_db_path), check_same_thread=False)
        self._init_l2_db()
        
        # HMAC key for integrity
        self._hmac_key = self._get_hmac_key()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "evictions": 0,
        }
    
    def _get_hmac_key(self) -> bytes:
        """Get HMAC key from environment or use default for dev."""
        key = os.getenv("PENIN_CACHE_HMAC_KEY", "penin-dev-key-change-me")
        return key.encode("utf-8")
    
    def _init_l2_db(self):
        """Initialize L2 SQLite database."""
        cursor = self.l2_db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access ON cache(access_count)")
        self.l2_db.commit()
    
    def _serialize(self, obj: Any) -> bytes:
        """Serialize object with HMAC for integrity."""
        data = orjson.dumps(obj)
        mac = hmac.new(self._hmac_key, data, hashlib.sha256).digest()
        return mac + data
    
    def _deserialize(self, b: bytes) -> Any:
        """Deserialize and verify HMAC."""
        if len(b) < 32:
            raise ValueError("Invalid cache data: too short for HMAC")
        
        mac, data = b[:32], b[32:]
        expected_mac = hmac.new(self._hmac_key, data, hashlib.sha256).digest()
        
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("L2 cache HMAC mismatch")
        
        return orjson.loads(data)
    
    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2)."""
        # Check L1
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not self._is_expired(entry["timestamp"], self.l1_ttl):
                self.l1_cache.move_to_end(key)
                self.stats["hits"] += 1
                self.stats["l1_hits"] += 1
                return entry["value"]
            else:
                del self.l1_cache[key]
        
        # Check L2
        cursor = self.l2_db.cursor()
        cursor.execute(
            "SELECT value, timestamp FROM cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            value_bytes, timestamp = row
            if not self._is_expired(timestamp, self.l2_ttl):
                try:
                    value = self._deserialize(value_bytes)
                    # Promote to L1
                    self._promote_to_l1(key, value)
                    # Update access count
                    cursor.execute(
                        "UPDATE cache SET access_count = access_count + 1 WHERE key = ?",
                        (key,)
                    )
                    self.l2_db.commit()
                    self.stats["hits"] += 1
                    self.stats["l2_hits"] += 1
                    return value
                except ValueError as e:
                    # Remove corrupted entry and re-raise for caller visibility
                    cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                    self.l2_db.commit()
                    raise
            else:
                # Expired
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                self.l2_db.commit()
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        # Add to L1
        self._promote_to_l1(key, value)
        
        # Add to L2
        value_bytes = self._serialize(value)
        cursor = self.l2_db.cursor()
        
        # Check if we need to evict
        cursor.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        
        if count >= self.l2_size:
            # Evict oldest entries (10% of cache)
            evict_count = max(1, self.l2_size // 10)
            cursor.execute("""
                DELETE FROM cache 
                WHERE key IN (
                    SELECT key FROM cache 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                )
            """, (evict_count,))
            self.stats["evictions"] += evict_count
        
        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, timestamp, access_count)
            VALUES (?, ?, ?, 0)
        """, (key, value_bytes, time.time()))
        self.l2_db.commit()
    
    def _promote_to_l1(self, key: str, value: Any):
        """Promote entry to L1 cache."""
        if len(self.l1_cache) >= self.l1_size:
            # Evict LRU
            evicted_key, _ = self.l1_cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        self.l1_cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self.l1_cache.move_to_end(key)
    
    def clear(self):
        """Clear all cache levels."""
        self.l1_cache.clear()
        cursor = self.l2_db.cursor()
        cursor.execute("DELETE FROM cache")
        self.l2_db.commit()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cursor = self.l2_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache")
        l2_count = cursor.fetchone()[0]
        
        return {
            **self.stats,
            "l1_size": len(self.l1_cache),
            "l2_size": l2_count,
            "hit_rate": self.stats["hits"] / max(1, self.stats["hits"] + self.stats["misses"]),
        }
    
    def close(self):
        """Close database connection."""
        self.l2_db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()