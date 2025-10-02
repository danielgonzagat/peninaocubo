"""Teste para verificar HMAC no cache L2"""

import os
import tempfile
from pathlib import Path

import pytest

from penin.cache import SecureCache


def test_cache_hmac_mismatch_raises():
    """Test that HMAC mismatch raises ValueError"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # Set initial HMAC key
        os.environ["PENIN_CACHE_HMAC_KEY"] = "key1"
        cache1 = SecureCache(cache_dir=cache_dir)

        # Store some data
        cache1.set("test_key", {"data": "test_value"})
        cache1.close()

        # Change HMAC key
        os.environ["PENIN_CACHE_HMAC_KEY"] = "key2"
        cache2 = SecureCache(cache_dir=cache_dir)

        # Try to retrieve data with different key
        with pytest.raises(ValueError, match="L2 cache HMAC mismatch"):
            cache2.get("test_key")

        cache2.close()


def test_cache_hmac_valid_retrieval():
    """Test valid HMAC retrieval"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir)

        # Store data
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        cache.set("test_key", test_data)

        # Retrieve data
        retrieved_data = cache.get("test_key")
        assert retrieved_data == test_data

        cache.close()


def test_cache_serialization_deserialization():
    """Test serialization and deserialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir)

        # Test various data types
        test_cases = [
            "simple_string",
            42,
            3.14,
            True,
            None,
            [1, 2, 3],
            {"key": "value", "nested": {"inner": "data"}},
            {"unicode": "café", "emoji": "🚀"},
        ]

        for i, test_data in enumerate(test_cases):
            key = f"test_{i}"
            cache.set(key, test_data)
            retrieved = cache.get(key)
            assert retrieved == test_data

        cache.close()


def test_cache_l1_l2_promotion():
    """Test L1 to L2 cache promotion"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir, l1_size=2, l2_size=10)

        # Fill L1 cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # This should promote key1 to L2
        cache.set("key3", "value3")

        # All should still be retrievable
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        cache.close()


def test_cache_expiration():
    """Test cache expiration"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir, l1_ttl=1, l2_ttl=1)

        # Store data
        cache.set("test_key", "test_value")

        # Should be available immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration (in real test, you'd mock time)
        import time

        time.sleep(1.1)

        # Should be None after expiration
        assert cache.get("test_key") is None

        cache.close()


def test_cache_statistics():
    """Test cache statistics"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir)

        # Initial stats
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "l1_hits" in stats
        assert "l2_hits" in stats
        assert "evictions" in stats
        assert "l1_size" in stats
        assert "l2_size" in stats
        assert "hit_rate" in stats

        # Store and retrieve data
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["hit_rate"] >= 0.0

        cache.close()


def test_cache_context_manager():
    """Test cache as context manager"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        with SecureCache(cache_dir=cache_dir) as cache:
            cache.set("key", "value")
            assert cache.get("key") == "value"

        # Cache should be closed after context exit
        # (In real implementation, you'd test the connection is closed)


def test_cache_clear():
    """Test cache clear functionality"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        cache = SecureCache(cache_dir=cache_dir)

        # Store data
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Verify data is there
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Clear cache
        cache.clear()

        # Data should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None

        cache.close()
