"""
Comprehensive CAOS Core Tests
==============================

Deep testing of penin/core/caos.py - the critical evolution engine.
Tests all functions, edge cases, and error paths.
"""

import pytest


class TestCAOSConfiguration:
    """Test CAOS configuration and initialization"""

    def test_caos_config_creation(self):
        """Test creating CAOS configuration"""
        from penin.core.caos import CAOSConfig
        
        config = CAOSConfig()
        
        # Should have default values
        assert config is not None
        assert hasattr(config, 'kappa')
        
    def test_caos_config_custom_kappa(self):
        """Test CAOS config with custom kappa"""
        from penin.core.caos import CAOSConfig
        
        config = CAOSConfig(kappa=25.0)
        
        assert config.kappa == 25.0


class TestCAOSExponentialComputation:
    """Test CAOS+ exponential computation"""

    def test_caos_plus_basic(self):
        """Test basic CAOS+ calculation"""
        from penin.core.caos import compute_caos_plus_exponential
        
        C = 0.8  # Consistency
        A = 0.6  # Auto-evolution
        O = 0.4  # Incognoscível
        S = 0.7  # Silêncio
        kappa = 20.0
        
        result = compute_caos_plus_exponential(C, A, O, S, kappa)
        
        # Should be positive and reasonable
        assert result > 0
        assert result > 1.0  # With kappa=20, should amplify
        
    def test_caos_plus_zero_inputs(self):
        """Test CAOS+ with zero inputs"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # All zeros
        result = compute_caos_plus_exponential(0, 0, 0, 0, kappa=20.0)
        
        # Should handle gracefully (1^0 = 1)
        assert result >= 0
        
    def test_caos_plus_perfect_inputs(self):
        """Test CAOS+ with perfect inputs (all 1.0)"""
        from penin.core.caos import compute_caos_plus_exponential
        
        result = compute_caos_plus_exponential(1.0, 1.0, 1.0, 1.0, kappa=20.0)
        
        # (1 + 20*1*1)^(1*1) = 21^1 = 21
        assert 20 < result < 22
        
    def test_caos_plus_varying_kappa(self):
        """Test CAOS+ with different kappa values"""
        from penin.core.caos import compute_caos_plus_exponential
        
        C, A, O, S = 0.8, 0.6, 0.4, 0.7
        
        result_low = compute_caos_plus_exponential(C, A, O, S, kappa=10.0)
        result_high = compute_caos_plus_exponential(C, A, O, S, kappa=30.0)
        
        # Higher kappa should give higher result
        assert result_high > result_low


class TestCAOSLinearComputation:
    """Test CAOS+ linear/simple computation"""

    def test_caos_plus_simple_basic(self):
        """Test simple CAOS+ calculation"""
        from penin.core.caos import compute_caos_plus_simple
        
        C = 0.8
        A = 0.6
        O = 0.4
        S = 0.7
        kappa = 20.0
        
        result = compute_caos_plus_simple(C, A, O, S, kappa)
        
        # Should be positive
        assert result > 0
        
    def test_caos_plus_simple_vs_exponential(self):
        """Compare simple and exponential CAOS+"""
        from penin.core.caos import compute_caos_plus_simple, compute_caos_plus_exponential
        
        C, A, O, S, kappa = 0.8, 0.6, 0.4, 0.7, 20.0
        
        simple = compute_caos_plus_simple(C, A, O, S, kappa)
        exponential = compute_caos_plus_exponential(C, A, O, S, kappa)
        
        # Both should be positive
        assert simple > 0
        assert exponential > 0


class TestCAOSComponentCalculation:
    """Test CAOS component calculations"""

    def test_consistency_calculation(self):
        """Test C (Consistency) component"""
        from penin.core.caos import compute_C_consistency
        
        # Mock metrics
        pass_at_k = 0.9
        ece = 0.02  # Low ECE is good
        external_verification = 0.85
        
        C = compute_C_consistency(pass_at_k, ece, external_verification)
        
        # Should be in [0, 1]
        assert 0 <= C <= 1
        # With good metrics, should be high
        assert C > 0.5
        
    def test_consistency_perfect(self):
        """Test consistency with perfect metrics"""
        from penin.core.caos import compute_C_consistency
        
        C = compute_C_consistency(
            pass_at_k=1.0,
            ece=0.0,
            external_verification=1.0
        )
        
        # Should be very high
        assert C > 0.9
        
    def test_consistency_poor(self):
        """Test consistency with poor metrics"""
        from penin.core.caos import compute_C_consistency
        
        C = compute_C_consistency(
            pass_at_k=0.3,
            ece=0.5,  # High ECE is bad
            external_verification=0.2
        )
        
        # Should be low
        assert C < 0.5


class TestCAOSSilenceCalculation:
    """Test S (Silence) component"""

    def test_silence_calculation(self):
        """Test basic silence calculation"""
        from penin.core.caos import compute_S_silence
        
        noise = 0.1  # Low noise is good
        redundancy = 0.2
        entropy_norm = 0.3
        
        S = compute_S_silence(noise, redundancy, entropy_norm)
        
        # Should be in [0, 1]
        assert 0 <= S <= 1
        
    def test_silence_perfect(self):
        """Test silence with zero noise/redundancy/entropy"""
        from penin.core.caos import compute_S_silence
        
        S = compute_S_silence(0.0, 0.0, 0.0)
        
        # Perfect silence
        assert S > 0.9
        
    def test_silence_noisy(self):
        """Test silence with high noise"""
        from penin.core.caos import compute_S_silence
        
        S = compute_S_silence(0.9, 0.8, 0.7)
        
        # Should be low
        assert S < 0.5


class TestCAOSAutoEvolutionCalculation:
    """Test A (Auto-evolution) component"""

    def test_autoevolution_calculation(self):
        """Test auto-evolution calculation"""
        from penin.core.caos import compute_A_autoevolution
        
        delta_linf = 0.05  # 5% improvement
        cost_norm = 0.02  # Low cost
        
        A = compute_A_autoevolution(delta_linf, cost_norm)
        
        # Should be in [0, 1]
        assert 0 <= A <= 1
        
    def test_autoevolution_high_gain(self):
        """Test auto-evolution with high gain, low cost"""
        from penin.core.caos import compute_A_autoevolution
        
        A = compute_A_autoevolution(0.10, 0.01)
        
        # Should be high (but clamped to 1.0)
        assert 0 <= A <= 1.0
        
    def test_autoevolution_zero_gain(self):
        """Test auto-evolution with no improvement"""
        from penin.core.caos import compute_A_autoevolution
        
        A = compute_A_autoevolution(0.0, 0.02)
        
        # Should be zero
        assert A == 0


class TestCAOSIncognosibleCalculation:
    """Test O (Incognoscível) component"""

    def test_incognoscivel_calculation(self):
        """Test incognoscível (epistemic uncertainty) calculation"""
        from penin.core.caos import compute_O_unknowable
        
        epistemic = 0.4
        ood = 0.3
        disagreement = 0.2
        
        O = compute_O_unknowable(epistemic, ood, disagreement)
        
        # Should be in [0, 1]
        assert 0 <= O <= 1
        
    def test_incognoscivel_high_uncertainty(self):
        """Test with high uncertainty (more exploration needed)"""
        from penin.core.caos import compute_O_unknowable
        
        O = compute_O_unknowable(0.9, 0.8, 0.7)
        
        # High uncertainty = high O
        assert O > 0.5
        
    def test_incognoscivel_low_uncertainty(self):
        """Test with low uncertainty (confident)"""
        from penin.core.caos import compute_O_unknowable
        
        O = compute_O_unknowable(0.1, 0.1, 0.05)
        
        # Low uncertainty = low O
        assert O < 0.5


class TestCAOSIntegration:
    """Integration tests for CAOS system"""

    def test_caos_full_pipeline(self):
        """Test complete CAOS calculation pipeline"""
        from penin.core.caos import (
            compute_C_consistency,
            compute_A_autoevolution,
            compute_O_unknowable,
            compute_S_silence,
            compute_caos_plus_exponential
        )
        
        # Calculate components
        C = compute_C_consistency(0.9, 0.01, 0.85)
        A = compute_A_autoevolution(0.05, 0.02)
        O = compute_O_unknowable(0.3, 0.2, 0.1)
        S = compute_S_silence(0.1, 0.15, 0.2)
        
        # Compute CAOS+
        caos = compute_caos_plus_exponential(C, A, O, S, kappa=20.0)
        
        # Should be positive and amplified
        assert caos > 1.0
        
    def test_caos_worst_case(self):
        """Test CAOS with worst possible inputs"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # All zeros or very low
        result = compute_caos_plus_exponential(0.01, 0.01, 0.01, 0.01, kappa=20.0)
        
        # Should still be computable
        assert result >= 0
        
    def test_caos_boundary_values(self):
        """Test CAOS at boundary values"""
        from penin.core.caos import compute_caos_plus_exponential
        
        # Test at boundaries
        result_min = compute_caos_plus_exponential(0.0, 0.0, 0.0, 0.0, kappa=1.0)
        result_max = compute_caos_plus_exponential(1.0, 1.0, 1.0, 1.0, kappa=50.0)
        
        assert result_min >= 0
        assert result_max > result_min
        
    def test_phi_caos_saturation(self):
        """Test phi_caos with saturation"""
        from penin.core.caos import phi_caos
        
        # Test with moderate inputs
        result = phi_caos(c=0.8, a=0.6, o=0.4, s=0.7, kappa=20.0, gamma=0.8)
        
        # phi_caos uses tanh saturation, so should be in reasonable range
        assert result > 0
        assert result < 100  # Saturated
