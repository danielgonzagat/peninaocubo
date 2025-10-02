"""
Tests for BudgetTracker
"""


import pytest

from penin.router_pkg.budget_tracker import BudgetTracker, ProviderStats


class TestBudgetTracker:
    """Test suite for BudgetTracker"""

    def test_initialization(self):
        """Test basic initialization"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        assert tracker.daily_limit_usd == 100.0
        assert tracker.spend_today_usd == 0.0
        assert tracker.tokens_consumed == 0
        assert tracker.requests_count == 0
        assert not tracker.is_soft_limit_reached()
        assert not tracker.is_hard_limit_reached()

    def test_invalid_initialization(self):
        """Test invalid parameters"""
        with pytest.raises(ValueError, match="daily_limit_usd must be positive"):
            BudgetTracker(daily_limit_usd=-10.0)

        with pytest.raises(ValueError, match="soft_limit_ratio must be in"):
            BudgetTracker(daily_limit_usd=100.0, soft_limit_ratio=1.5)

    def test_can_proceed_within_limit(self):
        """Test can_proceed when within limits"""
        tracker = BudgetTracker(daily_limit_usd=10.0)

        assert tracker.can_proceed(cost_usd=5.0) is True
        assert tracker.can_proceed(cost_usd=9.0) is True

    def test_can_proceed_exceeds_hard_limit(self):
        """Test can_proceed when exceeding hard limit"""
        tracker = BudgetTracker(daily_limit_usd=10.0)

        # Spend up to 9.0
        tracker.track_request("openai", tokens=1000, cost_usd=9.0, success=True)

        # Try to spend 2.0 more (would exceed 10.0)
        assert tracker.can_proceed(cost_usd=2.0) is False
        assert tracker.hard_limit_triggered is True

    def test_soft_limit_warning(self):
        """Test soft limit warning"""
        tracker = BudgetTracker(daily_limit_usd=10.0, soft_limit_ratio=0.9)

        # Spend 8.5 (85%, below soft limit)
        assert tracker.can_proceed(cost_usd=8.5) is True
        assert not tracker.soft_limit_triggered

        # Track it
        tracker.track_request("openai", tokens=1000, cost_usd=8.5, success=True)

        # Now check 1.0 more (would bring to 9.5, above 9.0 soft limit)
        assert tracker.can_proceed(cost_usd=1.0) is True
        assert tracker.soft_limit_triggered  # Should trigger warning

    def test_track_request_basic(self):
        """Test basic request tracking"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        tracker.track_request(
            provider="openai", tokens=1500, cost_usd=0.05, success=True
        )

        assert tracker.spend_today_usd == 0.05
        assert tracker.tokens_consumed == 1500
        assert tracker.requests_count == 1

        usage = tracker.get_usage()
        assert usage["spend_today"] == 0.05
        assert usage["tokens"] == 1500
        assert usage["requests"] == 1

    def test_track_multiple_providers(self):
        """Test tracking from multiple providers"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        tracker.track_request("openai", tokens=1000, cost_usd=0.03, success=True)
        tracker.track_request("anthropic", tokens=1500, cost_usd=0.05, success=True)
        tracker.track_request("openai", tokens=800, cost_usd=0.02, success=False)

        assert tracker.spend_today_usd == 0.10
        assert tracker.tokens_consumed == 3300
        assert tracker.requests_count == 3

        # Check provider stats
        openai_stats = tracker.get_provider_stats("openai")
        assert openai_stats.requests_total == 2
        assert openai_stats.requests_success == 1
        assert openai_stats.requests_failed == 1
        assert openai_stats.success_rate() == 0.5
        assert openai_stats.cost_total_usd == 0.05

        anthropic_stats = tracker.get_provider_stats("anthropic")
        assert anthropic_stats.requests_total == 1
        assert anthropic_stats.success_rate() == 1.0

    def test_get_usage_percent(self):
        """Test usage percentage calculation"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        assert tracker.get_usage_percent() == 0.0

        tracker.track_request("openai", tokens=1000, cost_usd=50.0, success=True)
        assert tracker.get_usage_percent() == 50.0

        tracker.track_request("anthropic", tokens=500, cost_usd=25.0, success=True)
        assert tracker.get_usage_percent() == 75.0

    def test_get_remaining_budget(self):
        """Test remaining budget calculation"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        assert tracker.get_remaining_budget() == 100.0

        tracker.track_request("openai", tokens=1000, cost_usd=30.0, success=True)
        assert tracker.get_remaining_budget() == 70.0

        tracker.track_request("anthropic", tokens=500, cost_usd=50.0, success=True)
        assert tracker.get_remaining_budget() == 20.0

    def test_manual_reset(self):
        """Test manual reset"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        tracker.track_request("openai", tokens=1000, cost_usd=50.0, success=True)
        assert tracker.spend_today_usd == 50.0

        tracker.reset()

        assert tracker.spend_today_usd == 0.0
        assert tracker.tokens_consumed == 0
        assert tracker.requests_count == 0
        assert len(tracker.provider_stats) == 0
        assert not tracker.soft_limit_triggered
        assert not tracker.hard_limit_triggered

    def test_request_history(self):
        """Test request history audit trail"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        tracker.track_request("openai", tokens=1000, cost_usd=0.03, success=True)
        tracker.track_request("anthropic", tokens=1500, cost_usd=0.05, success=True)

        assert len(tracker.request_history) == 2

        first = tracker.request_history[0]
        assert first.provider == "openai"
        assert first.tokens == 1000
        assert first.cost_usd == 0.03
        assert first.success is True

        second = tracker.request_history[1]
        assert second.provider == "anthropic"

    def test_export_metrics(self):
        """Test Prometheus metrics export"""
        tracker = BudgetTracker(daily_limit_usd=100.0)

        tracker.track_request("openai", tokens=1000, cost_usd=30.0, success=True)
        tracker.track_request("anthropic", tokens=500, cost_usd=20.0, success=True)

        metrics = tracker.export_metrics()

        assert metrics["penin_budget_daily_usd"] == 100.0
        assert metrics["penin_daily_spend_usd"] == 50.0
        assert metrics["penin_daily_remaining_usd"] == 50.0
        assert metrics["penin_budget_usage_percent"] == 50.0
        assert metrics["penin_tokens_consumed_total"] == 1500.0
        assert metrics["penin_requests_total"] == 2.0

        # Check provider-specific metrics exist
        assert 'penin_provider_requests_total{provider="openai"}' in metrics
        assert 'penin_provider_cost_usd{provider="openai"}' in metrics

    def test_repr(self):
        """Test string representation"""
        tracker = BudgetTracker(daily_limit_usd=100.0)
        tracker.track_request("openai", tokens=1000, cost_usd=25.0, success=True)

        repr_str = repr(tracker)
        assert "BudgetTracker" in repr_str
        assert "25.00" in repr_str
        assert "100.00" in repr_str
        assert "25.0%" in repr_str


class TestProviderStats:
    """Test ProviderStats dataclass"""

    def test_success_rate_zero_requests(self):
        """Test success rate with zero requests"""
        stats = ProviderStats()
        assert stats.success_rate() == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = ProviderStats(
            requests_total=10, requests_success=7, requests_failed=3
        )
        assert stats.success_rate() == 0.7

    def test_avg_cost_per_request_zero(self):
        """Test average cost with zero requests"""
        stats = ProviderStats()
        assert stats.avg_cost_per_request() == 0.0

    def test_avg_cost_per_request_calculation(self):
        """Test average cost calculation"""
        stats = ProviderStats(requests_total=10, cost_total_usd=5.0)
        assert stats.avg_cost_per_request() == 0.5
