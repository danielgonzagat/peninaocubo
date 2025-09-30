"""
Darwinian Audit - Non-Compensatory Fitness Scoring
==================================================

Implements darwinian fitness score using non-compensatory logic.
Only promotes challengers with higher fitness than champion.
"""

from typing import Dict, Any


def darwinian_score(
    life_ok: bool,
    caos_phi: float,
    sr: float,
    G: float,
    L_inf: float
) -> float:
    """
    Compute darwinian fitness score.
    
    Non-compensatory: bottleneck by worst component, scaled by L∞.
    
    Args:
        life_ok: Life Equation passed?
        caos_phi: CAOS⁺ phi
        sr: SR-Ω∞ score
        G: Global coherence
        L_inf: L∞ aggregate performance
        
    Returns:
        Fitness score [0, 1] (or 0 if life_ok is False)
    """
    if not life_ok:
        return 0.0
    
    # Non-compensatory: dominated by minimum
    bottleneck = min(caos_phi, sr, G)
    
    # Scale by performance
    return bottleneck * L_inf


def compare_fitness(
    challenger_fitness: float,
    champion_fitness: float,
    min_improvement: float = 0.01
) -> bool:
    """
    Decide if challenger should replace champion.
    
    Args:
        challenger_fitness: Challenger's fitness score
        champion_fitness: Champion's fitness score
        min_improvement: Minimum required improvement
        
    Returns:
        True if challenger should be promoted
    """
    improvement = challenger_fitness - champion_fitness
    return improvement >= min_improvement


class DarwinianAuditor:
    """
    Audits evolutionary candidates using darwinian fitness.
    
    Maintains champion and only promotes better challengers.
    """
    
    def __init__(self, champion_fitness: float = 0.0):
        self.champion_fitness = champion_fitness
        self.challenges: int = 0
        self.promotions: int = 0
        
        print(f"🧬 Darwinian Auditor initialized (champion_fitness={champion_fitness:.4f})")
    
    def evaluate(
        self,
        life_ok: bool,
        caos_phi: float,
        sr: float,
        G: float,
        L_inf: float
    ) -> Dict[str, Any]:
        """
        Evaluate a challenger.
        
        Returns:
            Dict with fitness, decision, and reasoning
        """
        fitness = darwinian_score(life_ok, caos_phi, sr, G, L_inf)
        self.challenges += 1
        
        should_promote = compare_fitness(fitness, self.champion_fitness)
        
        if should_promote:
            improvement = fitness - self.champion_fitness
            self.champion_fitness = fitness
            self.promotions += 1
            
            result = {
                "fitness": fitness,
                "decision": "PROMOTE",
                "improvement": improvement,
                "new_champion": True
            }
        else:
            gap = self.champion_fitness - fitness
            result = {
                "fitness": fitness,
                "decision": "REJECT",
                "gap": gap,
                "new_champion": False
            }
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get auditor statistics"""
        promotion_rate = self.promotions / max(1, self.challenges)
        
        return {
            "champion_fitness": self.champion_fitness,
            "challenges": self.challenges,
            "promotions": self.promotions,
            "promotion_rate": promotion_rate
        }


# Quick test
def quick_darwin_test():
    """Quick test of darwinian auditor"""
    auditor = DarwinianAuditor(champion_fitness=0.70)
    
    # Test challengers
    challengers = [
        {"life_ok": True, "phi": 0.7, "sr": 0.85, "G": 0.9, "L_inf": 0.95},  # Good
        {"life_ok": True, "phi": 0.6, "sr": 0.75, "G": 0.85, "L_inf": 0.90},  # Worse
        {"life_ok": True, "phi": 0.8, "sr": 0.90, "G": 0.92, "L_inf": 0.98},  # Better
        {"life_ok": False, "phi": 1.0, "sr": 1.0, "G": 1.0, "L_inf": 1.0},   # Failed gate
    ]
    
    print("\n🧬 Evaluating challengers:")
    for i, ch in enumerate(challengers):
        result = auditor.evaluate(**ch)
        print(f"   Challenger {i+1}: {result['decision']} (fitness={result['fitness']:.4f})")
    
    stats = auditor.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return auditor