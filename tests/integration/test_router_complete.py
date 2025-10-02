"""
Complete Multi-LLM Router Integration Tests
===========================================

Tests router with real budget tracking, circuit breakers, and cost optimization.
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from penin.router import MultiLLMRouterComplete, RouterMode
from penin.router_pkg.budget_tracker import BudgetTracker
from penin.providers.base import LLMResponse


class TestRouterBudgetTracking:
    """Test budget tracking and enforcement."""

    def test_budget_initialization(self):
        """Test budget tracker initialization"""
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        assert tracker.daily_limit_usd == 100.0
        assert tracker.used_usd == 0.0
        assert tracker.remaining_usd == 100.0
        assert tracker.usage_pct == 0.0

    def test_budget_tracking_single_request(self):
        """Test tracking single request cost"""
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        # Record a request costing $0.50
        tracker.record_request("openai", cost_usd=0.50, tokens_used=1000)
        
        assert tracker.used_usd == 0.50
        assert tracker.remaining_usd == 99.50
        assert tracker.usage_pct == 0.005  # 0.5%

    def test_budget_enforcement_soft_limit(self):
        """Test soft limit warning (95%)"""
        tracker = BudgetTracker(daily_limit_usd=100.0, soft_limit_ratio=0.95)
        
        # Use 96% of budget
        tracker.record_request("openai", cost_usd=96.0, tokens_used=100000)
        
        assert tracker.is_soft_limit_exceeded() is True
        assert tracker.is_hard_limit_exceeded() is False

    def test_budget_enforcement_hard_limit(self):
        """Test hard limit blocking (100%)"""
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        # Use 100% of budget
        tracker.record_request("openai", cost_usd=100.0, tokens_used=100000)
        
        assert tracker.is_hard_limit_exceeded() is True
        assert tracker.can_afford_request(estimated_cost=1.0) is False

    def test_budget_provider_stats(self):
        """Test per-provider statistics"""
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        # Record requests from different providers
        tracker.record_request("openai", cost_usd=10.0, tokens_used=5000)
        tracker.record_request("anthropic", cost_usd=15.0, tokens_used=6000)
        tracker.record_request("openai", cost_usd=5.0, tokens_used=2500)
        
        stats = tracker.get_provider_stats("openai")
        assert stats.requests_total == 2
        assert stats.cost_total_usd == 15.0
        assert stats.tokens_total == 7500


class TestRouterCircuitBreakers:
    """Test circuit breaker functionality."""

    @pytest.fixture
    def router(self):
        """Create router with circuit breaker config"""
        from penin.router_pkg.circuit_breaker import CircuitBreakerManager
        # Using circuit breaker manager directly for testing
        return CircuitBreakerManager()

    def test_circuit_breaker_opens_after_failures(self, router):
        """Test circuit breaker opens after N failures"""
        provider_name = "openai"
        
        # Simulate 3 consecutive failures
        for _ in range(3):
            router.record_failure(provider_name)
        
        # Circuit should be open
        assert router.get_state(provider_name).value == "open"

    def test_circuit_breaker_half_open_recovery(self, router):
        """Test circuit breaker enters half-open state after timeout"""
        from penin.router_pkg.circuit_breaker import CircuitBreakerConfig
        import time
        
        provider_name = "openai"
        # Use short timeout for testing
        router._breakers[provider_name] = router.get_breaker(provider_name)
        router._breakers[provider_name].config.timeout_seconds = 0.01
        
        # Open circuit
        for _ in range(3):
            router.record_failure(provider_name)
        
        assert router.get_state(provider_name).value == "open"
        
        # Wait for timeout
        time.sleep(0.02)
        
        # Should transition to half-open
        assert router.get_state(provider_name).value == "half_open"

    def test_circuit_breaker_closes_on_success(self, router):
        """Test circuit breaker closes after successful request"""
        import time
        provider_name = "openai"
        
        # Open circuit
        router._breakers[provider_name] = router.get_breaker(provider_name)
        router._breakers[provider_name].config.timeout_seconds = 0.01
        for _ in range(3):
            router.record_failure(provider_name)
        
        assert router.get_state(provider_name).value == "open"
        
        # Wait for half-open
        time.sleep(0.02)
        assert router.get_state(provider_name).value == "half_open"
        
        # Record success
        router.record_success(provider_name)
        
        # Circuit should close
        assert router.get_state(provider_name).value == "closed"


class TestRouterCostOptimization:
    """Test cost optimization routing."""

    @pytest.fixture
    def optimizer(self):
        """Create cost optimizer"""
        from penin.router_pkg.cost_optimizer import CostOptimizer, OptimizationStrategy
        return CostOptimizer(strategy=OptimizationStrategy.CHEAPEST)

    def test_selects_cheapest_provider(self, optimizer):
        """Test optimizer selects cheapest available provider"""
        providers = ["openai", "anthropic", "gemini"]
        costs = {"openai": 0.002, "anthropic": 0.003, "gemini": 0.001}
        
        selected = optimizer.select_provider(
            providers=providers,
            provider_costs=costs,
            estimated_tokens=1000
        )
        
        assert selected == "gemini"  # Cheapest

    def test_respects_budget_in_selection(self, optimizer):
        """Test optimizer respects remaining budget"""
        providers = ["openai", "anthropic"]
        costs = {"openai": 0.05, "anthropic": 0.02}
        
        # With $3 budget and 100k tokens, only anthropic is affordable
        selected = optimizer.select_provider(
            providers=providers,
            provider_costs=costs,
            estimated_tokens=100000,
            budget_remaining=3.0
        )
        
        assert selected == "anthropic"


class TestRouterPerformance:
    """Test router performance characteristics."""

    def test_routing_latency_overhead(self):
        """Test routing decision latency is minimal"""
        import time
        from penin.router_pkg.cost_optimizer import CostOptimizer, OptimizationStrategy
        
        optimizer = CostOptimizer(strategy=OptimizationStrategy.CHEAPEST)
        providers = ['openai', 'anthropic', 'gemini']
        costs = {'openai': 0.03, 'anthropic': 0.015, 'gemini': 0.01}
        
        # Measure routing decision time
        start = time.perf_counter()
        for _ in range(100):
            optimizer.select_provider(providers, costs, estimated_tokens=1000)
        end = time.perf_counter()
        
        avg_latency_ms = ((end - start) / 100) * 1000
        
        # Routing should be < 10ms per decision (relaxed for Python)
        assert avg_latency_ms < 10.0, f"Routing too slow: {avg_latency_ms:.3f}ms"

    def test_concurrent_request_handling(self):
        """Test budget tracker handles concurrent requests safely"""
        import concurrent.futures
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        def make_request(i):
            tracker.record_request("openai", cost_usd=0.1, tokens_used=500)
            return i
        
        # Execute 100 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            results = [f.result() for f in futures]
        
        # Check budget tracking is accurate (allow small float precision error)
        assert abs(tracker.used_usd - 10.0) < 0.01, f"Budget tracking inaccurate: {tracker.used_usd}"


class TestRouterCache:
    """Test router caching functionality."""

    @pytest.fixture
    def cache(self):
        """Create cache"""
        from penin.router_pkg.cache import MultiLevelCache
        return MultiLevelCache(l1_size=100, l1_ttl=60.0)

    def test_cache_hit_returns_cached_response(self, cache):
        """Test cache hit returns previous response"""
        key = "test_prompt"
        value = {"content": "4", "model": "gpt-4"}
        
        # Store
        cache.put(key, value)
        
        # Retrieve
        result = cache.get(key)
        assert result == value
        
        # Check hit rate
        assert cache.l1.hit_rate > 0.0

    def test_cache_integrity_hmac(self, cache):
        """Test cache integrity checking with HMAC"""
        key = "test_key"
        value = "test_value"
        
        # Put with HMAC
        cache.l1.put(key, value, verify_integrity=True)
        
        # Get with verification
        result = cache.l1.get(key, verify_integrity=True)
        assert result == value


class TestRouterFallback:
    """Test fallback routing behavior."""

    @pytest.fixture
    def fallback(self):
        """Create fallback strategy"""
        from penin.router_pkg.fallback import FallbackStrategy
        return FallbackStrategy()

    def test_fallback_on_provider_failure(self, fallback):
        """Test fallback to alternative provider on failure"""
        providers = ["openai", "anthropic", "gemini"]
        primary = "openai"
        
        # Get fallback sequence
        fallbacks = fallback.get_fallback_sequence(
            providers=providers,
            primary_provider=primary
        )
        
        # Should have alternatives (excluding primary)
        assert len(fallbacks) > 0
        assert primary not in fallbacks
        assert "anthropic" in fallbacks or "gemini" in fallbacks


class TestRouterAnalytics:
    """Test router analytics and monitoring."""

    @pytest.fixture
    def analytics(self):
        """Create analytics tracker"""
        from penin.router_pkg.analytics import AnalyticsTracker
        return AnalyticsTracker()

    def test_tracks_success_rate_per_provider(self, analytics):
        """Test success rate tracking"""
        # Record mix of successes and failures
        for _ in range(95):
            analytics.record_request("openai", latency_ms=100.0, success=True)
        for _ in range(5):
            analytics.record_request("openai", latency_ms=100.0, success=False)
        
        # Success rate should be 95%
        success_rate = analytics.get_success_rate("openai")
        assert success_rate == 0.95

    def test_tracks_latency_percentiles(self, analytics):
        """Test latency percentile tracking"""
        # Record various latencies
        latencies_ms = [10, 20, 30, 40, 50, 100, 200, 500, 1000, 2000]
        
        for latency in latencies_ms:
            analytics.record_request("openai", latency_ms=float(latency), success=True)
        
        # Get percentiles
        percentiles = analytics.get_latency_percentiles("openai")
        
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["p50"] > 0.0


# ============================================================================
# REAL API INTEGRATION TESTS (Requires API keys)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skip(reason="Requires API keys and --run-integration flag")
class TestRouterRealProviders:
    """Test router with real LLM providers (requires API keys)."""

    def test_openai_real_request(self):
        """Test real OpenAI API request"""
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        response = router.generate(
            "Say 'test' and nothing else",
            provider="openai",
            max_tokens=10,
        )
        
        assert response is not None
        assert len(response.content) > 0
        assert response.cost_usd > 0

    def test_anthropic_real_request(self):
        """Test real Anthropic API request"""
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        response = router.generate(
            "Say 'test' and nothing else",
            provider="anthropic",
            max_tokens=10,
        )
        
        assert response is not None
        assert len(response.content) > 0

    def test_cost_comparison_across_providers(self):
        """Test cost comparison for same prompt across providers"""
        import os
        if not (os.getenv("OPENAI_API_KEY") and os.getenv("ANTHROPIC_API_KEY")):
            pytest.skip("API keys not set")
        
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        prompt = "What is 2+2? Answer in one word."
        
        # Get responses from multiple providers
        responses = {}
        for provider in ["openai", "anthropic"]:
            responses[provider] = router.generate(prompt, provider=provider, max_tokens=10)
        
        # Compare costs
        costs = {p: r.cost_usd for p, r in responses.items()}
        print(f"Cost comparison: {costs}")
        
        # Cheapest should be selected in cost-optimized mode
        cheapest = min(costs, key=costs.get)
        print(f"Cheapest provider: {cheapest}")


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def mock_providers():
    """Create mock providers for testing"""
    return {
        "openai": Mock(
            name="openai",
            cost_per_token=0.000002,
            avg_latency_ms=100,
            success_rate=0.99,
        ),
        "anthropic": Mock(
            name="anthropic",
            cost_per_token=0.000003,
            avg_latency_ms=150,
            success_rate=0.98,
        ),
        "gemini": Mock(
            name="gemini",
            cost_per_token=0.000001,
            avg_latency_ms=120,
            success_rate=0.97,
        ),
    }
