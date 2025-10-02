"""
Comprehensive Utilities Tests
==============================

Testing utility functions, helpers, and edge cases across modules.
"""

import pytest


class TestCAOSUtilities:
    """Test CAOS utility functions"""

    def test_clamp01_bounds(self):
        """Test clamp01 at various bounds"""
        from penin.core.caos import clamp01
        
        assert clamp01(-1.0) == 0.0
        assert clamp01(-0.5) == 0.0
        assert clamp01(0.0) == 0.0
        assert clamp01(0.5) == 0.5
        assert clamp01(1.0) == 1.0
        assert clamp01(1.5) == 1.0
        assert clamp01(2.0) == 1.0

    def test_clamp_general(self):
        """Test general clamp function"""
        from penin.core.caos import clamp
        
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10

    def test_ema_alpha_various_halflifes(self):
        """Test EMA alpha for various half-lives"""
        from penin.core.caos import compute_ema_alpha
        
        # Shorter half-life = higher alpha (faster adaptation)
        alpha_3 = compute_ema_alpha(3)
        alpha_10 = compute_ema_alpha(10)
        
        assert 0 < alpha_3 < 1
        assert 0 < alpha_10 < 1
        assert alpha_3 > alpha_10  # Shorter half-life = higher alpha


class TestCAOSDataClasses:
    """Test CAOS dataclasses"""

    def test_caos_components_to_dict(self):
        """Test CAOSComponents to_dict"""
        from penin.core.caos import CAOSComponents
        
        components = CAOSComponents(C=0.8, A=0.6, O=0.4, S=0.7)
        d = components.to_dict()
        
        assert d == {"C": 0.8, "A": 0.6, "O": 0.4, "S": 0.7}

    def test_consistency_metrics_creation(self):
        """Test ConsistencyMetrics dataclass"""
        from penin.core.caos import ConsistencyMetrics
        
        metrics = ConsistencyMetrics(
            pass_at_k=0.9,
            ece=0.01,
            external_verification=0.85
        )
        
        assert metrics.pass_at_k == 0.9
        assert metrics.ece == 0.01

    def test_autoevolution_metrics_creation(self):
        """Test AutoevolutionMetrics dataclass"""
        from penin.core.caos import AutoevolutionMetrics
        
        metrics = AutoevolutionMetrics(
            delta_linf=0.05,
            cost_normalized=0.02
        )
        
        assert metrics.delta_linf == 0.05

    def test_incognoscible_metrics_creation(self):
        """Test IncognoscibleMetrics dataclass"""
        from penin.core.caos import IncognoscibleMetrics
        
        metrics = IncognoscibleMetrics(
            epistemic_uncertainty=0.3
        )
        
        assert metrics.epistemic_uncertainty == 0.3

    def test_silence_metrics_creation(self):
        """Test SilenceMetrics dataclass"""
        from penin.core.caos import SilenceMetrics
        
        metrics = SilenceMetrics(
            noise_ratio=0.1
        )
        
        assert metrics.noise_ratio == 0.1


class TestCAOSConfig:
    """Test CAOS configuration"""

    def test_caos_config_defaults(self):
        """Test CAOSConfig default values"""
        from penin.core.caos import CAOSConfig
        
        config = CAOSConfig()
        
        assert config.kappa >= 20.0  # Should be at least 20
        assert hasattr(config, 'formula')

    def test_caos_config_custom_values(self):
        """Test CAOSConfig with custom values"""
        from penin.core.caos import CAOSConfig, CAOSFormula
        
        config = CAOSConfig(
            kappa=25.0,
            formula=CAOSFormula.EXPONENTIAL,
            ema_half_life=5
        )
        
        assert config.kappa == 25.0
        assert config.formula == CAOSFormula.EXPONENTIAL
        assert config.ema_half_life == 5


class TestRouterUtilities:
    """Test router utility functions"""

    def test_budget_tracker_repr(self):
        """Test BudgetTracker string representation"""
        from penin.router_pkg.budget_tracker import BudgetTracker
        
        tracker = BudgetTracker(daily_limit_usd=100.0)
        
        repr_str = repr(tracker)
        assert "BudgetTracker" in repr_str

    def test_circuit_breaker_repr(self):
        """Test CircuitBreaker string representation"""
        from penin.router_pkg.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker()
        
        repr_str = repr(breaker)
        assert "CircuitBreaker" in repr_str
        assert "closed" in repr_str.lower()


class TestAutoregenerationModules:
    """Test autoregen modules"""

    def test_continuous_learning_loads(self):
        """Test continuous_learning module loads"""
        from penin.autoregen import continuous_learning
        assert continuous_learning is not None

    def test_data_stream_loads(self):
        """Test data_stream module loads"""
        from penin.autoregen import data_stream
        assert data_stream is not None

    def test_autoregen_package_structure(self):
        """Test autoregen package structure"""
        from penin import autoregen
        
        # Should have expected modules
        assert hasattr(autoregen, 'ContinuousLearner')
        assert hasattr(autoregen, 'DataStreamProcessor')
