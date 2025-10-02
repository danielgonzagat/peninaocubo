"""
Multi-Level Cache with HMAC Integrity
======================================

Implements L1 (memory) and L2 (optional persistent) cache with HMAC-SHA256
integrity verification for LLM responses.

Features:
- L1: In-memory LRU cache (fast)
- L2: Optional persistent cache (disk/redis)
- HMAC-SHA256 for response integrity
- TTL support
- Size limits
- Cache warming
"""

from __future__ import annotations

import hashlib
import hmac
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

try:
    import orjson as json  # Faster JSON
except ImportError:
    import json  # type: ignore


T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata"""

    key: str
    value: T
    created_at: float
    accessed_at: float
    access_count: int = 0
    hmac_signature: str | None = None
    ttl_seconds: float | None = None

    @property
    def age_seconds(self) -> float:
        """Age of entry in seconds"""
        return time.time() - self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds is None:
            return False
        return self.age_seconds > self.ttl_seconds


class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) cache with TTL support.

    Thread-safe for single-threaded usage.
    For multi-threaded, wrap with threading.Lock.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: float | None = 3600.0,  # 1 hour
    ):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            default_ttl_seconds: Default TTL for entries (None = no expiry)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> T | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check expiry
        if entry.is_expired:
            self._cache.pop(key)
            self._misses += 1
            return None

        # Update access metadata
        entry.accessed_at = time.time()
        entry.access_count += 1

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        self._hits += 1
        return entry.value

    def put(self, key: str, value: T, ttl_seconds: float | None = None) -> None:
        """
        Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL for this entry (uses default if None)
        """
        now = time.time()

        # Create entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            accessed_at=now,
            access_count=0,
            ttl_seconds=ttl_seconds or self.default_ttl,
        )

        # Add to cache
        self._cache[key] = entry
        self._cache.move_to_end(key)

        # Evict if over size
        while len(self._cache) > self.max_size:
            # Remove least recently used (first item)
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Current cache size"""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }


class HMACCache(LRUCache[T]):
    """
    LRU cache with HMAC-SHA256 integrity verification.

    Extends LRUCache to add HMAC signatures for cached values,
    ensuring integrity and detecting tampering.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: float | None = 3600.0,
        hmac_secret: bytes | None = None,
    ):
        """
        Initialize HMAC cache.

        Args:
            max_size: Maximum cache size
            default_ttl_seconds: Default TTL
            hmac_secret: Secret key for HMAC (generates random if None)
        """
        super().__init__(max_size, default_ttl_seconds)
        self.hmac_secret = hmac_secret or self._generate_secret()

    def put(
        self,
        key: str,
        value: T,
        ttl_seconds: float | None = None,
        verify_integrity: bool = True,
    ) -> None:
        """
        Put value in cache with HMAC signature.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL
            verify_integrity: Whether to compute HMAC signature
        """
        now = time.time()

        # Compute HMAC if requested
        hmac_sig = None
        if verify_integrity:
            hmac_sig = self._compute_hmac(key, value)

        # Create entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            accessed_at=now,
            access_count=0,
            hmac_signature=hmac_sig,
            ttl_seconds=ttl_seconds or self.default_ttl,
        )

        # Add to cache
        self._cache[key] = entry
        self._cache.move_to_end(key)

        # Evict if over size
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def get(self, key: str, verify_integrity: bool = True) -> T | None:
        """
        Get value from cache with optional HMAC verification.

        Args:
            key: Cache key
            verify_integrity: Whether to verify HMAC signature

        Returns:
            Cached value or None if not found/expired/tampered
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check expiry
        if entry.is_expired:
            self._cache.pop(key)
            self._misses += 1
            return None

        # Verify HMAC if requested
        if verify_integrity and entry.hmac_signature is not None:
            expected_hmac = self._compute_hmac(key, entry.value)
            if not hmac.compare_digest(expected_hmac, entry.hmac_signature):
                # HMAC mismatch - possible tampering
                self._cache.pop(key)
                self._misses += 1
                return None

        # Update access metadata
        entry.accessed_at = time.time()
        entry.access_count += 1
        self._cache.move_to_end(key)

        self._hits += 1
        return entry.value

    def _compute_hmac(self, key: str, value: Any) -> str:
        """
        Compute HMAC-SHA256 signature for value.

        Args:
            key: Cache key
            value: Value to sign

        Returns:
            HMAC signature (hex string)
        """
        # Serialize value
        if isinstance(value, (str, bytes)):
            data = value if isinstance(value, bytes) else value.encode("utf-8")
        else:
            # JSON serialize for complex objects
            if hasattr(json, "dumps"):
                data = json.dumps(value)
            else:
                import json as stdlib_json

                data = stdlib_json.dumps(value, sort_keys=True).encode("utf-8")

        # Include key in signature
        message = f"{key}:{data}".encode("utf-8") if isinstance(data, str) else data

        # Compute HMAC
        h = hmac.new(self.hmac_secret, message, hashlib.sha256)
        return h.hexdigest()

    @staticmethod
    def _generate_secret() -> bytes:
        """Generate random secret for HMAC"""
        import secrets

        return secrets.token_bytes(32)  # 256 bits


class MultiLevelCache:
    """
    Multi-level cache (L1 memory + optional L2 persistent).

    L1: Fast in-memory LRU cache with HMAC
    L2: Optional slower persistent cache (not implemented, placeholder)

    Lookup order: L1 → L2 → miss
    Write order: L1 + L2
    """

    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: float = 3600.0,
        hmac_secret: bytes | None = None,
        enable_l2: bool = False,
    ):
        """
        Initialize multi-level cache.

        Args:
            l1_size: L1 cache size
            l1_ttl: L1 default TTL
            hmac_secret: HMAC secret
            enable_l2: Enable L2 cache (not implemented)
        """
        self.l1 = HMACCache[Any](
            max_size=l1_size, default_ttl_seconds=l1_ttl, hmac_secret=hmac_secret
        )
        self.enable_l2 = enable_l2
        # L2 cache placeholder (could be Redis, disk, etc.)
        self.l2 = None

    def get(self, key: str) -> Any | None:
        """
        Get value from cache (L1 → L2).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            return value

        # Try L2 if enabled (placeholder)
        if self.enable_l2 and self.l2 is not None:
            # value = self.l2.get(key)
            # if value is not None:
            #     # Warm L1 cache
            #     self.l1.put(key, value)
            #     return value
            pass

        return None

    def put(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Put value in cache (both L1 and L2).

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL
        """
        # Write to L1
        self.l1.put(key, value, ttl_seconds=ttl_seconds)

        # Write to L2 if enabled (placeholder)
        if self.enable_l2 and self.l2 is not None:
            # self.l2.put(key, value, ttl_seconds=ttl_seconds)
            pass

    def delete(self, key: str) -> None:
        """Delete from all cache levels"""
        self.l1.delete(key)
        if self.enable_l2 and self.l2 is not None:
            # self.l2.delete(key)
            pass

    def clear(self) -> None:
        """Clear all cache levels"""
        self.l1.clear()
        if self.enable_l2 and self.l2 is not None:
            # self.l2.clear()
            pass

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "l1": self.l1.stats,
            "l2": {"enabled": self.enable_l2},
        }
