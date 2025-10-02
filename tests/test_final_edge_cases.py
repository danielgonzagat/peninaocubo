"""
Final Edge Cases Tests
======================

Additional edge case tests to push coverage to 96%+
"""

import pytest


class TestCAOSEdgeCases:
    """Additional CAOS edge cases"""

    def test_caos_with_negative_inputs(self):
        """Test CAOS handles negative inputs (should clamp)"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # Negative values (should be clamped to 0)
        result = compute_caos_plus_exponential(-0.1, -0.2, 0.5, 0.6, kappa=20.0)
        
        # Should still compute (with clamping)
        assert result >= 0

    def test_caos_with_very_large_inputs(self):
        """Test CAOS with very large inputs"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # Values > 1.0 (should be clamped)
        result = compute_caos_plus_exponential(1.5, 1.8, 1.2, 1.3, kappa=20.0)
        
        # Should handle gracefully
        assert result > 0

    def test_caos_with_mixed_bounds(self):
        """Test CAOS with mix of in-bounds and out-of-bounds"""
        from penin.core.caos import compute_caos_plus_exponential
        
        result = compute_caos_plus_exponential(0.8, 1.5, -0.1, 0.7, kappa=20.0)
        
        # Should compute with clamping
        assert result > 0


class TestBudgetTrackerEdgeCases:
    """Additional budget tracker edge cases"""

    def test_budget_multiple_providers(self):
        """Test budget with many different providers"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        # Record from 10 different providers
        for i in range(10):
            tracker.record_request(f"provider{i}", cost_usd=1.0, tokens_used=100)
        
        # Total should be 10.0
        assert abs(tracker.used_usd - 10.0) < 0.01
        
    def test_budget_tracks_tokens(self):
        """Test budget tracks tokens correctly"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        # Record request
        tracker.record_request("openai", cost_usd=5.0, tokens_used=1000)
        
        # Check stats
        stats = tracker.get_provider_stats("openai")
        assert stats.tokens_total == 1000


class TestCircuitBreakerEdgeCases:
    """Additional circuit breaker edge cases"""

    def test_circuit_breaker_many_failures(self):
        """Test circuit breaker with many consecutive failures"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker()
        
        # Record 100 failures
        for _ in range(100):
            breaker.record_failure()
        
        # Should be open
        assert breaker.is_open

    def test_circuit_breaker_alternating(self):
        """Test circuit breaker with alternating success/failure"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker()
        breaker.config.failure_threshold = 5
        
        # Alternate: success, failure, success, failure
        for _ in range(4):
            breaker.record_success()
            breaker.record_failure()
        
        # Should still be closed (failures not consecutive)
        assert breaker.is_closed


class TestCacheEdgeCases:
    """Additional cache edge cases"""

    def test_cache_duplicate_keys(self):
        """Test cache with duplicate key (should overwrite)"""
        from penin.router_pkg.cache import LRUCache
        
        cache = LRUCache(max_size=10)
        
        # Put twice with same key
        cache.put("key", "value1")
        cache.put("key", "value2")
        
        # Should have latest value
        assert cache.get("key") == "value2"
        # Should only count as 1 entry
        assert cache.size == 1

    def test_cache_cleanup_expired(self):
        """Test cache cleanup of expired entries"""
        from penin.router_pkg.cache import LRUCache
        import time
        
        cache = LRUCache(max_size=10, default_ttl_seconds=0.01)
        
        # Add items
        for i in range(5):
            cache.put(f"key{i}", f"value{i}", ttl_seconds=0.01)
        
        # Wait for expiry
        time.sleep(0.02)
        
        # Cleanup
        removed = cache.cleanup_expired()
        
        # Should have removed all 5
        assert removed == 5


class TestAnalyticsEdgeCases:
    """Additional analytics edge cases"""

    def test_analytics_empty_provider(self):
        """Test analytics with no requests"""
        from penin.router_pkg.analytics import AnalyticsTracker
        
        tracker = AnalyticsTracker()
        
        # Query non-existent provider
        success_rate = tracker.get_success_rate("nonexistent")
        
        # Should return 0.0
        assert success_rate == 0.0

    def test_analytics_all_failures(self):
        """Test analytics with 100% failures"""
        from penin.router_pkg.analytics import AnalyticsTracker
        
        tracker = AnalyticsTracker()
        
        # Record 10 failures
        for _ in range(10):
            tracker.record_request("openai", latency_ms=100.0, success=False)
        
        # Success rate should be 0.0
        assert tracker.get_success_rate("openai") == 0.0


class TestCostOptimizerEdgeCases:
    """Additional cost optimizer edge cases"""

    def test_optimizer_single_provider(self):
        """Test optimizer with only one provider"""
        from penin.router_pkg.cost_optimizer import CostOptimizer
        
        optimizer = CostOptimizer()
        
        selected = optimizer.select_provider(
            providers=["openai"],
            provider_costs={"openai": 0.03},
            estimated_tokens=1000
        )
        
        # Should select the only option
        assert selected == "openai"

    def test_optimizer_no_affordable_providers(self):
        """Test optimizer when no providers are affordable"""
        from penin.router_pkg.cost_optimizer import CostOptimizer
        
        optimizer = CostOptimizer()
        
        selected = optimizer.select_provider(
            providers=["openai", "anthropic"],
            provider_costs={"openai": 0.1, "anthropic": 0.08},
            estimated_tokens=1000,
            budget_remaining=0.01  # Too low for either
        )
        
        # Should return None (no affordable provider)
        assert selected is None


class TestFallbackEdgeCases:
    """Additional fallback edge cases"""

    def test_fallback_all_circuits_open(self):
        """Test fallback when all circuits are open"""
        from penin.router_pkg.fallback import FallbackStrategy
        
        strategy = FallbackStrategy()
        
        # All circuits open
        open_circuits = {"openai", "anthropic", "gemini"}
        
        fallbacks = strategy.get_fallback_sequence(
            providers=["openai", "anthropic", "gemini"],
            primary_provider="openai",
            open_circuits=open_circuits
        )
        
        # Should return empty (no available fallbacks)
        assert len(fallbacks) == 0

    def test_fallback_cost_ordering(self):
        """Test fallback orders by cost"""
        from penin.router_pkg.fallback import FallbackStrategy
        
        strategy = FallbackStrategy()
        strategy.config.prefer_cheapest = True
        
        providers = ["openai", "anthropic", "gemini"]
        costs = {"openai": 0.03, "anthropic": 0.015, "gemini": 0.01}
        
        fallbacks = strategy.get_fallback_sequence(
            providers=providers,
            primary_provider="openai",
            provider_costs=costs
        )
        
        # First fallback should be cheapest (gemini)
        assert fallbacks[0] == "gemini"
