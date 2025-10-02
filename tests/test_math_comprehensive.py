"""
Comprehensive Math Tests
========================

Deep testing of penin/math/ modules to increase coverage.
Tests all mathematical modules can be imported and basic structure.
"""

import pytest


class TestMathModulesLoad:
    """Test all math modules can be imported"""

    def test_linf_module_loads(self):
        """Test L∞ module loads"""
        from penin.math import linf
        assert linf is not None

    def test_linf_complete_module_loads(self):
        """Test L∞ complete module loads"""
        from penin.math import linf_complete
        assert linf_complete is not None

    def test_ir_ic_contractivity_loads(self):
        """Test IR→IC contractivity module loads"""
        from penin.math import ir_ic_contractivity
        assert ir_ic_contractivity is not None

    def test_sr_omega_infinity_loads(self):
        """Test SR-Ω∞ module loads"""
        from penin.math import sr_omega_infinity
        assert sr_omega_infinity is not None

    def test_vida_morte_gates_loads(self):
        """Test Vida/Morte gates module loads"""
        from penin.math import vida_morte_gates
        assert vida_morte_gates is not None

    def test_penin_master_equation_loads(self):
        """Test Penin master equation module loads"""
        from penin.math import penin_master_equation
        assert penin_master_equation is not None

    def test_caos_plus_complete_loads(self):
        """Test CAOS+ complete module loads"""
        from penin.math import caos_plus_complete
        assert caos_plus_complete is not None

    def test_oci_loads(self):
        """Test OCI module loads"""
        from penin.math import oci
        assert oci is not None


class TestMathDataStructures:
    """Test math data structures"""

    def test_consistency_metrics_structure(self):
        """Test ConsistencyMetrics dataclass"""
        from penin.core.caos import ConsistencyMetrics
        
        metrics = ConsistencyMetrics(pass_at_k=0.9, ece=0.01)
        
        assert metrics.pass_at_k == 0.9
        assert metrics.ece == 0.01

    def test_autoevolution_metrics_structure(self):
        """Test AutoevolutionMetrics dataclass"""
        from penin.core.caos import AutoevolutionMetrics
        
        metrics = AutoevolutionMetrics(delta_linf=0.05, cost_normalized=0.02)
        
        assert metrics.delta_linf == 0.05
        assert metrics.cost_normalized == 0.02


class TestMathUtilityFunctions:
    """Test math utility functions"""

    def test_harmonic_mean_basic(self):
        """Test harmonic mean calculation"""
        from penin.core.caos import harmonic_mean
        
        # Equal values
        result = harmonic_mean(0.5, 0.5, 0.5, 0.5)
        
        # Harmonic mean of equal values = that value
        assert abs(result - 0.5) < 0.01

    def test_harmonic_mean_bottleneck(self):
        """Test harmonic mean bottleneck property"""
        from penin.core.caos import harmonic_mean
        
        # One very low value (bottleneck)
        result_bottleneck = harmonic_mean(0.9, 0.9, 0.9, 0.1)
        # All equal
        result_balanced = harmonic_mean(0.7, 0.7, 0.7, 0.7)
        
        # Bottleneck should pull down average
        assert result_bottleneck < result_balanced

    def test_geometric_mean_basic(self):
        """Test geometric mean calculation"""
        from penin.core.caos import geometric_mean
        
        # Equal values
        result = geometric_mean(0.5, 0.5, 0.5, 0.5)
        
        # Geometric mean of equal values = that value
        assert abs(result - 0.5) < 0.01

    def test_clamp_function(self):
        """Test clamp utility"""
        from penin.core.caos import clamp01
        
        # Test clamping to [0, 1]
        assert clamp01(-0.5) == 0.0
        assert clamp01(1.5) == 1.0
        assert clamp01(0.5) == 0.5

    def test_ema_alpha_calculation(self):
        """Test EMA alpha calculation"""
        from penin.core.caos import compute_ema_alpha
        
        # Half-life of 5
        alpha = compute_ema_alpha(half_life=5)
        
        # Should be between 0 and 1
        assert 0 < alpha < 1
