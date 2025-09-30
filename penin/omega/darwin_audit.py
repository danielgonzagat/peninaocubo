"""
Darwinian Audit - Evolution scoring with non-compensatory selection
Implements fitness evaluation for variant selection
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class Variant:
    """Evolutionary variant with fitness metrics"""
    id: str
    generation: int
    fitness_score: float
    life_ok: bool
    caos_phi: float
    sr: float
    G: float
    L_inf: float
    mutations: List[str]
    parent_id: Optional[str] = None
    timestamp: float = 0.0


def darwinian_score(
    life_ok: bool,
    caos_phi: float,
    sr: float,
    G: float,
    L_inf: float
) -> float:
    """
    Compute Darwinian fitness score (non-compensatory)
    
    If Life Equation fails, score is 0 (variant dies).
    Otherwise, score is the product of key metrics with min dominance.
    
    Parameters:
    -----------
    life_ok: Life Equation gate result
    caos_phi: CAOS⁺ phi value
    sr: Self-reflexivity score
    G: Global coherence
    L_inf: L∞ performance metric
    
    Returns:
    --------
    Darwinian fitness score [0, 1]
    """
    if not life_ok:
        return 0.0
    
    # Non-compensatory: dominated by worst component
    min_component = min(caos_phi, sr, G)
    
    # Scale by performance
    return min_component * L_inf


def select_survivors(
    variants: List[Variant],
    survival_rate: float = 0.5,
    min_fitness: float = 0.3
) -> List[Variant]:
    """
    Select surviving variants based on fitness
    
    Parameters:
    -----------
    variants: List of variants to evaluate
    survival_rate: Fraction of variants to keep
    min_fitness: Minimum fitness threshold
    
    Returns:
    --------
    List of surviving variants
    """
    # Filter by minimum fitness
    viable = [v for v in variants if v.fitness_score >= min_fitness]
    
    if not viable:
        return []
    
    # Sort by fitness (descending)
    viable.sort(key=lambda v: v.fitness_score, reverse=True)
    
    # Keep top fraction
    n_survivors = max(1, int(len(viable) * survival_rate))
    
    return viable[:n_survivors]


def tournament_selection(
    variants: List[Variant],
    tournament_size: int = 3,
    n_winners: int = 1
) -> List[Variant]:
    """
    Tournament selection for breeding
    
    Parameters:
    -----------
    variants: Pool of variants
    tournament_size: Number of variants per tournament
    n_winners: Number of winners to select
    
    Returns:
    --------
    Tournament winners
    """
    if len(variants) <= n_winners:
        return variants
    
    winners = []
    
    for _ in range(n_winners):
        # Random tournament
        import random
        tournament = random.sample(variants, min(tournament_size, len(variants)))
        
        # Winner is highest fitness
        winner = max(tournament, key=lambda v: v.fitness_score)
        winners.append(winner)
    
    return winners


def fitness_pressure(
    generation: int,
    initial_pressure: float = 0.3,
    max_pressure: float = 0.9,
    generations_to_max: int = 100
) -> float:
    """
    Compute adaptive fitness pressure that increases over time
    
    Parameters:
    -----------
    generation: Current generation number
    initial_pressure: Starting selection pressure
    max_pressure: Maximum selection pressure
    generations_to_max: Generations to reach maximum
    
    Returns:
    --------
    Current fitness pressure [initial, max]
    """
    if generation >= generations_to_max:
        return max_pressure
    
    # Linear increase
    t = generation / generations_to_max
    return initial_pressure + (max_pressure - initial_pressure) * t


def diversity_bonus(
    variant: Variant,
    population: List[Variant],
    diversity_weight: float = 0.1
) -> float:
    """
    Compute diversity bonus for maintaining variation
    
    Parameters:
    -----------
    variant: Variant to evaluate
    population: Current population
    diversity_weight: Weight for diversity bonus
    
    Returns:
    --------
    Adjusted fitness with diversity bonus
    """
    if len(population) <= 1:
        return variant.fitness_score
    
    # Compute distance from population mean
    mean_phi = sum(v.caos_phi for v in population) / len(population)
    mean_sr = sum(v.sr for v in population) / len(population)
    mean_G = sum(v.G for v in population) / len(population)
    
    # Distance from mean (normalized)
    distance = (
        abs(variant.caos_phi - mean_phi) +
        abs(variant.sr - mean_sr) +
        abs(variant.G - mean_G)
    ) / 3.0
    
    # Add diversity bonus
    bonus = distance * diversity_weight
    
    return min(1.0, variant.fitness_score + bonus)


def lineage_trace(
    variant: Variant,
    population: Dict[str, Variant],
    max_depth: int = 10
) -> List[str]:
    """
    Trace lineage of a variant back through parents
    
    Parameters:
    -----------
    variant: Variant to trace
    population: Dictionary of all variants by ID
    max_depth: Maximum generations to trace back
    
    Returns:
    --------
    List of ancestor IDs from variant to root
    """
    lineage = [variant.id]
    current = variant
    
    for _ in range(max_depth):
        if current.parent_id is None:
            break
        
        if current.parent_id in population:
            current = population[current.parent_id]
            lineage.append(current.id)
        else:
            break
    
    return lineage


def mutation_impact_analysis(
    variant: Variant,
    parent: Optional[Variant]
) -> Dict[str, float]:
    """
    Analyze impact of mutations from parent to variant
    
    Parameters:
    -----------
    variant: Current variant
    parent: Parent variant (if exists)
    
    Returns:
    --------
    Dictionary of metric changes
    """
    if parent is None:
        return {
            "fitness_delta": 0.0,
            "phi_delta": 0.0,
            "sr_delta": 0.0,
            "G_delta": 0.0,
            "L_inf_delta": 0.0,
            "improvement": False
        }
    
    return {
        "fitness_delta": variant.fitness_score - parent.fitness_score,
        "phi_delta": variant.caos_phi - parent.caos_phi,
        "sr_delta": variant.sr - parent.sr,
        "G_delta": variant.G - parent.G,
        "L_inf_delta": variant.L_inf - parent.L_inf,
        "improvement": variant.fitness_score > parent.fitness_score
    }


class EvolutionTracker:
    """Track evolutionary progress across generations"""
    
    def __init__(self):
        self.generations: List[List[Variant]] = []
        self.best_ever: Optional[Variant] = None
        self.statistics: List[Dict[str, float]] = []
    
    def add_generation(self, variants: List[Variant]):
        """Add a new generation"""
        self.generations.append(variants)
        
        # Update best ever
        if variants:
            gen_best = max(variants, key=lambda v: v.fitness_score)
            if self.best_ever is None or gen_best.fitness_score > self.best_ever.fitness_score:
                self.best_ever = gen_best
        
        # Compute statistics
        if variants:
            stats = {
                "generation": len(self.generations) - 1,
                "population_size": len(variants),
                "mean_fitness": sum(v.fitness_score for v in variants) / len(variants),
                "max_fitness": max(v.fitness_score for v in variants),
                "min_fitness": min(v.fitness_score for v in variants),
                "survival_rate": sum(1 for v in variants if v.life_ok) / len(variants),
                "mean_phi": sum(v.caos_phi for v in variants) / len(variants),
                "mean_sr": sum(v.sr for v in variants) / len(variants),
                "mean_G": sum(v.G for v in variants) / len(variants)
            }
            self.statistics.append(stats)
    
    def get_trend(self, metric: str = "mean_fitness", window: int = 5) -> str:
        """
        Get trend for a metric (improving/stable/degrading)
        
        Parameters:
        -----------
        metric: Metric to analyze
        window: Number of generations to consider
        
        Returns:
        --------
        Trend description
        """
        if len(self.statistics) < 2:
            return "insufficient_data"
        
        recent_stats = self.statistics[-window:]
        if len(recent_stats) < 2:
            return "insufficient_data"
        
        values = [s.get(metric, 0) for s in recent_stats]
        
        # Check trend
        if all(values[i] >= values[i-1] for i in range(1, len(values))):
            return "improving"
        elif all(values[i] <= values[i-1] for i in range(1, len(values))):
            return "degrading"
        else:
            # Check if relatively stable
            mean_val = sum(values) / len(values)
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            
            if variance < 0.001:
                return "stable"
            else:
                return "oscillating"


def quick_test():
    """Quick test of Darwinian audit system"""
    # Create test variants
    variants = [
        Variant(
            id="v1",
            generation=1,
            fitness_score=0.0,  # Will be computed
            life_ok=True,
            caos_phi=0.7,
            sr=0.8,
            G=0.85,
            L_inf=0.6,
            mutations=["init"],
            timestamp=time.time()
        ),
        Variant(
            id="v2",
            generation=1,
            fitness_score=0.0,
            life_ok=True,
            caos_phi=0.8,
            sr=0.75,
            G=0.9,
            L_inf=0.65,
            mutations=["mut_A"],
            parent_id="v1",
            timestamp=time.time()
        ),
        Variant(
            id="v3",
            generation=1,
            fitness_score=0.0,
            life_ok=False,  # Failed Life Equation
            caos_phi=0.9,
            sr=0.7,
            G=0.8,
            L_inf=0.7,
            mutations=["mut_B"],
            parent_id="v1",
            timestamp=time.time()
        )
    ]
    
    # Compute fitness scores
    for v in variants:
        v.fitness_score = darwinian_score(v.life_ok, v.caos_phi, v.sr, v.G, v.L_inf)
    
    # Test selection
    survivors = select_survivors(variants, survival_rate=0.5)
    
    # Test tournament
    winners = tournament_selection(variants, tournament_size=2, n_winners=1)
    
    # Test evolution tracker
    tracker = EvolutionTracker()
    tracker.add_generation(variants)
    
    # Test mutation impact
    impact = mutation_impact_analysis(variants[1], variants[0])
    
    # Test fitness pressure
    pressure_early = fitness_pressure(10)
    pressure_late = fitness_pressure(90)
    
    return {
        "variant_count": len(variants),
        "v3_fitness": variants[2].fitness_score,  # Should be 0 (life_ok=False)
        "survivors": len(survivors),
        "best_fitness": max(v.fitness_score for v in variants),
        "tournament_winner": winners[0].id if winners else None,
        "fitness_improvement": impact["improvement"],
        "pressure_early": pressure_early,
        "pressure_late": pressure_late,
        "trend": tracker.get_trend("mean_fitness")
    }


if __name__ == "__main__":
    result = quick_test()
    print("Darwinian Audit Test:")
    print(f"  Variants: {result['variant_count']}")
    print(f"  V3 fitness (life_ok=False): {result['v3_fitness']}")
    print(f"  Survivors: {result['survivors']}")
    print(f"  Best fitness: {result['best_fitness']:.3f}")
    print(f"  Tournament winner: {result['tournament_winner']}")
    print(f"  Fitness improved: {result['fitness_improvement']}")
    print(f"  Selection pressure: early={result['pressure_early']:.2f}, late={result['pressure_late']:.2f}")
    print(f"  Trend: {result['trend']}")