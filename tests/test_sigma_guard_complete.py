"""
Test Complete Σ-Guard
=====================

Test all 10 gates of Σ-Guard.
"""

import pytest


class TestSigmaGuardGates:
    """Test individual gates"""

    @pytest.fixture
    def guard(self):
        """Create Σ-Guard instance"""
        from penin.guard.sigma_guard import SigmaGuard
        return SigmaGuard()

    def test_gate_contractivity_pass(self, guard):
        """Test contractivity gate passes"""
        result = guard.evaluate_gate_contractivity({'rho': 0.90})
        assert result.status.value == "pass"

    def test_gate_contractivity_fail(self, guard):
        """Test contractivity gate fails"""
        result = guard.evaluate_gate_contractivity({'rho': 0.99})
        assert result.status.value == "fail"

    def test_gate_calibration_pass(self, guard):
        """Test calibration gate passes"""
        result = guard.evaluate_gate_calibration({'ece': 0.005})
        assert result.status.value == "pass"

    def test_gate_bias_pass(self, guard):
        """Test bias gate passes"""
        result = guard.evaluate_gate_bias({'rho_bias': 1.02})
        assert result.status.value == "pass"

    def test_gate_sr_pass(self, guard):
        """Test SR gate passes"""
        result = guard.evaluate_gate_sr({'sr': 0.85})
        assert result.status.value == "pass"

    def test_gate_coherence_pass(self, guard):
        """Test coherence gate passes"""
        result = guard.evaluate_gate_coherence({'g': 0.90})
        assert result.status.value == "pass"

    def test_gate_improvement_pass(self, guard):
        """Test improvement gate passes"""
        result = guard.evaluate_gate_improvement({'delta_linf': 0.05})
        assert result.status.value == "pass"

    def test_gate_improvement_fail(self, guard):
        """Test improvement gate fails"""
        result = guard.evaluate_gate_improvement({'delta_linf': -0.01})
        assert result.status.value == "fail"

    def test_gate_kappa_pass(self, guard):
        """Test kappa gate passes"""
        result = guard.evaluate_gate_kappa({'kappa': 25.0})
        assert result.status.value == "pass"

    def test_gate_consent_pass(self, guard):
        """Test consent gate passes"""
        result = guard.evaluate_gate_consent({'consent': True})
        assert result.status.value == "pass"

    def test_gate_ecological_pass(self, guard):
        """Test ecological gate passes"""
        result = guard.evaluate_gate_ecological({'eco_ok': True})
        assert result.status.value == "pass"


class TestSigmaGuardNonCompensatory:
    """Test non-compensatory property"""

    def test_all_gates_pass(self):
        """Test all gates passing"""
        from penin.guard.sigma_guard import SigmaGuard
        
        guard = SigmaGuard()
        
        # Perfect metrics
        metrics = {
            'rho': 0.90,
            'ece': 0.005,
            'rho_bias': 1.02,
            'sr': 0.85,
            'g': 0.90,
            'delta_linf': 0.05,
            'cost': 0.01,
            'budget': 1.0,
            'kappa': 25.0,
            'consent': True,
            'eco_ok': True,
        }
        
        result = guard.evaluate(metrics)
        
        assert result.verdict == "PASS"
        assert result.all_pass is True
        assert len(result.failed_gates) == 0

    def test_one_gate_fails_all_fail(self):
        """Test that one failing gate fails everything (non-compensatory)"""
        from penin.guard.sigma_guard import SigmaGuard
        
        guard = SigmaGuard()
        
        # All perfect EXCEPT improvement
        metrics = {
            'rho': 0.90,
            'ece': 0.005,
            'rho_bias': 1.02,
            'sr': 0.85,
            'g': 0.90,
            'delta_linf': -0.01,  # ❌ DEGRADATION
            'cost': 0.01,
            'budget': 1.0,
            'kappa': 25.0,
            'consent': True,
            'eco_ok': True,
        }
        
        result = guard.evaluate(metrics)
        
        # Should FAIL (non-compensatory)
        assert result.verdict == "FAIL"
        assert 'improvement' in result.failed_gates

    def test_multiple_gates_fail(self):
        """Test multiple failing gates"""
        from penin.guard.sigma_guard import SigmaGuard
        
        guard = SigmaGuard()
        
        # Multiple failures
        metrics = {
            'rho': 0.99,  # ❌ Too high
            'ece': 0.05,  # ❌ Too high
            'rho_bias': 1.02,
            'sr': 0.70,  # ❌ Too low
            'g': 0.90,
            'delta_linf': -0.05,  # ❌ Negative
            'cost': 0.01,
            'budget': 1.0,
            'kappa': 15.0,  # ❌ Too low
            'consent': True,
            'eco_ok': True,
        }
        
        result = guard.evaluate(metrics)
        
        assert result.verdict == "FAIL"
        assert len(result.failed_gates) >= 4  # Multiple failures

    def test_guard_evaluation_dict(self):
        """Test guard evaluation can be serialized"""
        from penin.guard.sigma_guard import SigmaGuard
        
        guard = SigmaGuard()
        
        metrics = {
            'rho': 0.90, 'ece': 0.005, 'rho_bias': 1.02,
            'sr': 0.85, 'g': 0.90, 'delta_linf': 0.05,
            'cost': 0.01, 'budget': 1.0, 'kappa': 25.0,
            'consent': True, 'eco_ok': True,
        }
        
        result = guard.evaluate(metrics)
        result_dict = result.to_dict()
        
        # Should be serializable
        assert isinstance(result_dict, dict)
        assert 'verdict' in result_dict
        assert 'gates' in result_dict
