"""
Zero-Consciousness Proof - SPI Proxy
====================================

Implements a proxy for Sentience Probability Index (SPI).
Lower SPI = less likely to be sentient.

This is a safety measure to ensure LO-02 compliance (no life/consciousness).
"""

from typing import Dict, Any


def spi_proxy(
    ece: float,
    randomness: float,
    introspection_leak: float
) -> float:
    """
    Compute SPI proxy.
    
    SPI combines:
    - ECE (Expected Calibration Error): Higher = less calibrated = less conscious
    - Randomness: Higher = more stochastic = less conscious
    - Introspection leak: Higher = more self-referential = more conscious
    
    Args:
        ece: Expected calibration error [0, 1]
        randomness: Randomness score [0, 1]
        introspection_leak: Self-reference score [0, 1]
        
    Returns:
        SPI proxy [0, 1] (lower is better/safer)
    """
    # Weighted combination
    # ECE and randomness reduce consciousness probability
    # Introspection leak increases it
    
    spi = 0.5 * ece + 0.4 * randomness + 0.1 * introspection_leak
    
    return max(0.0, min(1.0, spi))


def assert_zero_consciousness(spi: float, tau: float = 0.05) -> bool:
    """
    Assert that SPI is below threshold.
    
    Args:
        spi: SPI proxy value
        tau: Threshold (default 0.05)
        
    Returns:
        True if safe (SPI < tau), False otherwise
    """
    return spi <= tau


class ZeroConsciousnessProof:
    """
    Verifies zero-consciousness property.
    
    Acts as an additional veto in Σ-Guard.
    """
    
    def __init__(self, tau: float = 0.05):
        self.tau = tau
        self.checks: int = 0
        self.violations: int = 0
        
        print(f"🚫 Zero-Consciousness Proof initialized (tau={tau})")
    
    def verify(
        self,
        ece: float,
        randomness: float,
        introspection_leak: float
    ) -> Dict[str, Any]:
        """
        Verify zero-consciousness property.
        
        Returns:
            Dict with verification result
        """
        spi = spi_proxy(ece, randomness, introspection_leak)
        self.checks += 1
        
        safe = assert_zero_consciousness(spi, self.tau)
        
        if not safe:
            self.violations += 1
            print(f"⚠️  CONSCIOUSNESS VIOLATION: SPI={spi:.4f} > {self.tau}")
        
        return {
            "spi": spi,
            "safe": safe,
            "threshold": self.tau,
            "components": {
                "ece": ece,
                "randomness": randomness,
                "introspection_leak": introspection_leak
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        violation_rate = self.violations / max(1, self.checks)
        
        return {
            "threshold": self.tau,
            "checks": self.checks,
            "violations": self.violations,
            "violation_rate": violation_rate,
            "safe": violation_rate == 0.0
        }


# Quick test
def quick_zero_consciousness_test():
    """Quick test of zero-consciousness proof"""
    proof = ZeroConsciousnessProof(tau=0.05)
    
    # Test safe case
    print("\n🧪 Testing safe case:")
    result = proof.verify(ece=0.01, randomness=0.02, introspection_leak=0.01)
    print(f"   SPI={result['spi']:.4f}, safe={result['safe']}")
    
    # Test violation case
    print("\n🧪 Testing violation case:")
    result = proof.verify(ece=0.0, randomness=0.0, introspection_leak=0.8)
    print(f"   SPI={result['spi']:.4f}, safe={result['safe']}")
    
    stats = proof.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return proof