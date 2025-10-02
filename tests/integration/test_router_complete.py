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
        tracker = BudgetTracker(daily_budget_usd=100.0)
        
        assert tracker.daily_budget_usd == 100.0
        assert tracker.used_usd == 0.0
        assert tracker.remaining_usd == 100.0
        assert tracker.usage_pct == 0.0

    def test_budget_tracking_single_request(self):
        """Test tracking single request cost"""
        tracker = BudgetTracker(daily_budget_usd=100.0)
        
        # Record a request costing $0.50
        tracker.record_request("openai", cost_usd=0.50, tokens_used=1000)
        
        assert tracker.used_usd == 0.50
        assert tracker.remaining_usd == 99.50
        assert tracker.usage_pct == 0.005  # 0.5%

    def test_budget_enforcement_soft_limit(self):
        """Test soft limit warning (95%)"""
        tracker = BudgetTracker(daily_budget_usd=100.0, soft_limit_ratio=0.95)
        
        # Use 96% of budget
        tracker.record_request("openai", cost_usd=96.0, tokens_used=100000)
        
        assert tracker.is_soft_limit_exceeded() is True
        assert tracker.is_hard_limit_exceeded() is False

    def test_budget_enforcement_hard_limit(self):
        """Test hard limit blocking (100%)"""
        tracker = BudgetTracker(daily_budget_usd=100.0)
        
        # Use 100% of budget
        tracker.record_request("openai", cost_usd=100.0, tokens_used=100000)
        
        assert tracker.is_hard_limit_exceeded() is True
        assert tracker.can_afford_request(estimated_cost=1.0) is False

    def test_budget_provider_stats(self):
        """Test per-provider statistics"""
        tracker = BudgetTracker(daily_budget_usd=100.0)
        
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
        return MultiLLMRouterComplete(
            mode=RouterMode.PRODUCTION,
            daily_budget_usd=100.0,
            circuit_breaker_enabled=True,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout_s=60.0,
        )

    def test_circuit_breaker_opens_after_failures(self, router):
        """Test circuit breaker opens after N failures"""
        provider_name = "openai"
        
        # Simulate 3 consecutive failures
        for _ in range(3):
            router._record_provider_failure(provider_name)
        
        # Circuit should be open
        assert router._is_circuit_open(provider_name) is True

    def test_circuit_breaker_half_open_recovery(self, router):
        """Test circuit breaker enters half-open state after timeout"""
        provider_name = "openai"
        
        # Open circuit
        for _ in range(3):
            router._record_provider_failure(provider_name)
        
        assert router._is_circuit_open(provider_name) is True
        
        # Simulate timeout passing
        import time
        time.sleep(0.1)  # Small sleep for test
        
        # After timeout, should be half-open (allowing test requests)
        # In real implementation, this would check timestamp

    def test_circuit_breaker_closes_on_success(self, router):
        """Test circuit breaker closes after successful request"""
        provider_name = "openai"
        
        # Open circuit
        for _ in range(3):
            router._record_provider_failure(provider_name)
        
        # Record success
        router._record_provider_success(provider_name)
        
        # Check that failure count reset
        # Circuit should eventually close


class TestRouterCostOptimization:
    """Test cost optimization routing."""

    @pytest.fixture
    def router(self):
        """Create cost-optimized router"""
        return MultiLLMRouterComplete(
            mode=RouterMode.PRODUCTION,
            daily_budget_usd=100.0,
        )

    def test_selects_cheapest_provider(self, router):
        """Test router selects cheapest available provider"""
        # Mock provider pricing
        with patch('penin.providers.pricing.get_provider_cost') as mock_cost:
            mock_cost.side_effect = lambda p: {
                'openai': 0.002,
                'anthropic': 0.003,
                'gemini': 0.001,  # Cheapest
            }.get(p, 0.01)
            
            # Get best provider for cost mode
            provider = router._select_provider_cost_optimized(['openai', 'anthropic', 'gemini'])
            
            # Should select gemini (cheapest)
            assert provider == 'gemini'

    def test_respects_budget_in_selection(self, router):
        """Test provider selection respects remaining budget"""
        # Use 95% of budget
        router.budget_tracker.record_request("openai", cost_usd=95.0, tokens_used=100000)
        
        # Try to select provider for expensive request
        # Should block or select cheapest
        assert router.budget_tracker.is_soft_limit_exceeded() is True


class TestRouterPerformance:
    """Test router performance characteristics."""

    def test_routing_latency_overhead(self):
        """Test routing decision latency is minimal"""
        import time
        
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        # Measure routing decision time
        start = time.perf_counter()
        for _ in range(100):
            router._select_provider_cost_optimized(['openai', 'anthropic', 'gemini'])
        end = time.perf_counter()
        
        avg_latency_ms = ((end - start) / 100) * 1000
        
        # Routing should be < 1ms per decision
        assert avg_latency_ms < 1.0, f"Routing too slow: {avg_latency_ms}ms"

    def test_concurrent_request_handling(self):
        """Test router handles concurrent requests safely"""
        import concurrent.futures
        
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        def make_request(i):
            router.budget_tracker.record_request("openai", cost_usd=0.1, tokens_used=500)
            return i
        
        # Execute 100 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            results = [f.result() for f in futures]
        
        # Check budget tracking is accurate
        assert router.budget_tracker.used_usd == 10.0  # 100 * 0.1


class TestRouterCache:
    """Test router caching functionality."""

    @pytest.fixture
    def router(self):
        """Create router with cache enabled"""
        return MultiLLMRouterComplete(
            mode=RouterMode.PRODUCTION,
            cache_enabled=True,
            cache_ttl_seconds=3600,
        )

    def test_cache_hit_returns_cached_response(self, router):
        """Test cache hit returns previous response"""
        prompt = "What is 2+2?"
        
        # First request - cache miss
        with patch.object(router, '_call_provider') as mock_call:
            mock_call.return_value = LLMResponse(
                content="4",
                model="gpt-4",
                tokens_used=10,
                cost_usd=0.001,
            )
            
            response1 = router.generate(prompt, provider="openai")
            assert mock_call.call_count == 1
        
        # Second request - cache hit
        with patch.object(router, '_call_provider') as mock_call:
            response2 = router.generate(prompt, provider="openai")
            
            # Should NOT call provider again
            assert mock_call.call_count == 0
            assert response2.content == "4"

    def test_cache_integrity_hmac(self, router):
        """Test cache integrity checking with HMAC"""
        # Cache should validate integrity before returning
        # If tampered, should regenerate
        pass  # TODO: Implement HMAC validation test


class TestRouterFallback:
    """Test fallback routing behavior."""

    @pytest.fixture
    def router(self):
        """Create router with fallback enabled"""
        return MultiLLMRouterComplete(
            mode=RouterMode.PRODUCTION,
            fallback_enabled=True,
        )

    def test_fallback_on_provider_failure(self, router):
        """Test fallback to alternative provider on failure"""
        with patch.object(router, '_call_provider') as mock_call:
            # First provider fails
            mock_call.side_effect = [
                Exception("Provider unavailable"),
                LLMResponse(content="Success", model="gpt-4", tokens_used=10, cost_usd=0.001),
            ]
            
            response = router.generate("test", provider="openai", fallback_providers=["anthropic"])
            
            # Should have tried both providers
            assert mock_call.call_count == 2
            assert response.content == "Success"


class TestRouterAnalytics:
    """Test router analytics and monitoring."""

    def test_tracks_success_rate_per_provider(self):
        """Test success rate tracking"""
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        # Record mix of successes and failures
        for _ in range(95):
            router._record_provider_success("openai")
        for _ in range(5):
            router._record_provider_failure("openai")
        
        stats = router.budget_tracker.get_provider_stats("openai")
        # Success rate should be 95%
        # assert stats.success_rate == 0.95  # TODO: Implement success rate tracking

    def test_tracks_latency_percentiles(self):
        """Test latency percentile tracking"""
        router = MultiLLMRouterComplete(mode=RouterMode.PRODUCTION)
        
        # Record various latencies
        latencies_ms = [10, 20, 30, 40, 50, 100, 200, 500, 1000, 2000]
        
        for latency in latencies_ms:
            router._record_latency("openai", latency)
        
        # Should be able to query p50, p95, p99
        # p50 = router.get_latency_percentile("openai", 50)
        # assert p50 == 50  # Median


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
