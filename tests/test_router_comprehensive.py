"""
Comprehensive Router Tests
==========================

Deep testing of router components and utilities.
Tests edge cases, error paths, and corner cases.
"""

import pytest


class TestRouterModeEnum:
    """Test RouterMode enum"""

    def test_router_modes_exist(self):
        """Test RouterMode enum values"""
        from penin.router import RouterMode
        
        # Should have expected modes
        assert hasattr(RouterMode, 'PRODUCTION')
        assert hasattr(RouterMode, 'DRY_RUN')
        assert hasattr(RouterMode, 'SHADOW')

    def test_router_mode_values(self):
        """Test RouterMode enum string values"""
        from penin.router import RouterMode
        
        assert RouterMode.PRODUCTION.value == "production"
        assert RouterMode.DRY_RUN.value == "dry_run"
        assert RouterMode.SHADOW.value == "shadow"


class TestBudgetTrackerEdgeCases:
    """Test BudgetTracker edge cases"""

    def test_budget_zero_limit(self):
        """Test budget tracker with zero limit"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=0.01)  # Very small limit
        
        # Small request should exceed limit
        tracker.record_request("openai", cost_usd=0.02, tokens_used=10)
        assert tracker.is_hard_limit_exceeded()

    def test_budget_very_large_limit(self):
        """Test budget tracker with very large limit"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=1000000.0)
        
        # Small request should not exceed
        tracker.record_request("openai", cost_usd=100.0, tokens_used=1000)
        assert not tracker.is_hard_limit_exceeded()
        
    def test_budget_exact_limit(self):
        """Test budget at exact limit"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        tracker.record_request("openai", cost_usd=100.0, tokens_used=10000)
        
        # At exactly 100%, should be hard limit
        assert tracker.is_hard_limit_exceeded()
        assert tracker.usage_pct == 1.0


class TestCircuitBreakerEdgeCases:
    """Test CircuitBreaker edge cases"""

    def test_circuit_breaker_rapid_open_close(self):
        """Test circuit breaker rapid state changes"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        import time
        
        breaker = CircuitBreaker()
        breaker.config.timeout_seconds = 0.01  # Very short timeout
        
        # Open circuit
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.is_open
        
        # Wait for half-open
        time.sleep(0.02)
        assert breaker.is_half_open
        
        # Success closes it
        breaker.record_success()
        assert breaker.is_closed

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker()
        
        # Cause failures
        for _ in range(5):
            breaker.record_failure()
        
        # Reset
        breaker.reset()
        
        # Should be back to initial state
        assert breaker.is_closed
        assert breaker.stats.failure_count == 0


class TestCacheEdgeCases:
    """Test Cache edge cases"""

    def test_cache_overflow_eviction(self):
        """Test cache evicts when full"""
        from penin.router_pkg.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        
        # Add 5 items (should evict 2 oldest)
        for i in range(5):
            cache.put(f"key{i}", f"value{i}")
        
        # Cache should have exactly 3 items
        assert cache.size == 3
        
        # First 2 should be evicted (0, 1)
        assert cache.get("key0") is None
        assert cache.get("key1") is None
        
        # Last 3 should exist (2, 3, 4)
        assert cache.get("key4") is not None

    def test_cache_ttl_expiry(self):
        """Test cache TTL expiration"""
        from penin.router_pkg.cache import LRUCache
        import time
        
        cache = LRUCache(max_size=10, default_ttl_seconds=0.01)
        
        # Add item with very short TTL
        cache.put("key", "value", ttl_seconds=0.01)
        
        # Should exist immediately
        assert cache.get("key") is not None
        
        # Wait for expiry
        time.sleep(0.02)
        
        # Should be expired
        assert cache.get("key") is None

    def test_cache_hmac_integrity(self):
        """Test HMAC integrity detection"""
        from penin.router_pkg.cache import HMACCache
        
        cache = HMACCache(max_size=10)
        
        # Put value with HMAC
        cache.put("key", "value", verify_integrity=True)
        
        # Get with verification should succeed
        result = cache.get("key", verify_integrity=True)
        assert result == "value"
        
        # Manually tamper with cache entry
        entry = cache._cache["key"]
        original_hmac = entry.hmac_signature
        entry.hmac_signature = "tampered_signature"
        
        # Get with verification should fail (return None)
        result_tampered = cache.get("key", verify_integrity=True)
        assert result_tampered is None


class TestRouterPackageComponents:
    """Test router_pkg components are importable"""

    def test_budget_tracker_import(self):
        """Test BudgetTracker can be imported"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        assert tracker is not None

    def test_circuit_breaker_import(self):
        """Test CircuitBreaker can be imported"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker()
        assert breaker is not None

    def test_cache_import(self):
        """Test Cache can be imported"""
        from penin.router_pkg.cache import MultiLevelCache
        
        cache = MultiLevelCache()
        assert cache is not None

    def test_analytics_import(self):
        """Test Analytics can be imported"""
        from penin.router_pkg.analytics import AnalyticsTracker
        
        tracker = AnalyticsTracker()
        assert tracker is not None

    def test_cost_optimizer_import(self):
        """Test CostOptimizer can be imported"""
        from penin.router_pkg.cost_optimizer import CostOptimizer
        
        optimizer = CostOptimizer()
        assert optimizer is not None

    def test_fallback_import(self):
        """Test Fallback can be imported"""
        from penin.router_pkg.fallback import FallbackStrategy
        
        fallback = FallbackStrategy()
        assert fallback is not None
