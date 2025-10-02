"""
Core Equations Tests
====================

Smoke tests for equations modules - verify they load and have expected structure.
"""

import pytest


class TestEquationsModulesLoad:
    """Test that equations modules can be imported"""

    def test_ir_ic_module_loads(self):
        """Test IR→IC module loads"""
        from penin.equations import ir_ic_contractive
        
        # Verify module loaded
        assert ir_ic_contractive is not None

    def test_lyapunov_module_loads(self):
        """Test Lyapunov module loads"""
        from penin.equations import lyapunov_contractive
        
        assert lyapunov_contractive is not None

    def test_death_equation_module_loads(self):
        """Test Death Equation module loads"""
        from penin.equations import death_equation
        
        assert death_equation is not None

    def test_delta_linf_module_loads(self):
        """Test ΔL∞ growth module loads"""
        from penin.equations import delta_linf_growth
        
        assert delta_linf_growth is not None

    def test_caos_plus_module_loads(self):
        """Test CAOS⁺ module loads"""
        from penin.equations import caos_plus
        
        assert caos_plus is not None

    def test_penin_equation_module_loads(self):
        """Test Penin equation module loads"""
        from penin.equations import penin_equation
        
        assert penin_equation is not None


class TestMathImplementations:
    """Test actual math implementations in penin/math/"""

    def test_linf_module_structure(self):
        """Test L∞ module has expected structure"""
        from penin.math import linf
        
        # Module loaded successfully
        assert linf is not None
        assert hasattr(linf, '__name__')

    def test_caos_plus_calculation(self):
        """Test CAOS⁺ calculation works"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # Mock CAOS inputs
        C = 0.8  # Consistency
        A = 0.6  # Autoevolução
        O = 0.4  # Incognoscível
        S = 0.7  # Silêncio
        kappa = 20.0
        
        caos = compute_caos_plus_exponential(C, A, O, S, kappa)
        
        # Should return a positive value
        assert caos > 0, f"CAOS⁺ should be positive, got {caos}"

    def test_sr_omega_infinity_module(self):
        """Test SR-Ω∞ module structure"""
        from penin.math import sr_omega_infinity
        
        # Module loaded successfully
        assert sr_omega_infinity is not None
        assert hasattr(sr_omega_infinity, '__name__')
