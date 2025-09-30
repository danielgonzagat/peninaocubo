"""
Darwinian Audit - Evolutionary Selection with Auditability
===========================================================

Implements Darwinian selection mechanisms with full audit trail.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time


@dataclass
class Variant:
    """Evolutionary variant"""
    id: str
    generation: int
    fitness: float
    traits: Dict[str, Any]
    parent_id: Optional[str] = None
    mutations: List[str] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.mutations is None:
            self.mutations = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def darwinian_score(
    life_ok: bool,
    caos_phi: float,
    sr: float,
    G: float,
    L_inf: float
) -> float:
    """
    Calculate Darwinian fitness score (non-compensatory).
    
    Args:
        life_ok: Life Equation verdict
        caos_phi: CAOS⁺ value
        sr: SR-Ω∞ value
        G: Global coherence
        L_inf: L∞ score
    
    Returns:
        Darwinian fitness score
    """
    if not life_ok:
        return 0.0
    
    # Non-compensatory: dominance by worst component
    min_component = min(caos_phi, sr, G)
    
    # Scale by L∞
    return min_component * L_inf


class Population:
    """Manages population of variants"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.variants: List[Variant] = []
        self.generation = 0
        self.history: List[Dict[str, Any]] = []
        
    def add_variant(self, variant: Variant) -> bool:
        """Add a variant to the population"""
        # Check if we need to make room
        if len(self.variants) >= self.max_size:
            # Remove weakest variant
            self.variants.sort(key=lambda v: v.fitness)
            self.variants.pop(0)
        
        self.variants.append(variant)
        
        # Record in history
        self.history.append({
            "action": "add",
            "variant_id": variant.id,
            "generation": self.generation,
            "timestamp": time.time()
        })
        
        return True
    
    def select_parents(self, n: int = 2) -> List[Variant]:
        """
        Select parents for reproduction (fitness-proportional).
        
        Args:
            n: Number of parents to select
        
        Returns:
            List of selected variants
        """
        if len(self.variants) < n:
            return self.variants.copy()
        
        # Sort by fitness
        sorted_variants = sorted(self.variants, key=lambda v: v.fitness, reverse=True)
        
        # Tournament selection
        selected = []
        for _ in range(n):
            # Take top 20% for tournament
            tournament_size = max(2, len(sorted_variants) // 5)
            tournament = sorted_variants[:tournament_size]
            
            # Select from tournament
            import random
            selected.append(random.choice(tournament))
        
        return selected
    
    def evolve(self) -> Optional[Variant]:
        """
        Evolve the population by one generation.
        
        Returns:
            Best new variant or None
        """
        if len(self.variants) < 2:
            return None
        
        # Select parents
        parents = self.select_parents(2)
        
        # Create offspring
        offspring_traits = {}
        
        # Crossover
        for key in parents[0].traits:
            if key in parents[1].traits:
                # Average for numeric traits
                if isinstance(parents[0].traits[key], (int, float)):
                    offspring_traits[key] = (
                        parents[0].traits[key] + parents[1].traits[key]
                    ) / 2
                else:
                    # Random selection for non-numeric
                    import random
                    offspring_traits[key] = random.choice([
                        parents[0].traits[key],
                        parents[1].traits[key]
                    ])
            else:
                offspring_traits[key] = parents[0].traits[key]
        
        # Mutation
        mutations = []
        import random
        for key in offspring_traits:
            if random.random() < 0.1:  # 10% mutation rate
                if isinstance(offspring_traits[key], (int, float)):
                    # Gaussian mutation
                    offspring_traits[key] *= random.gauss(1.0, 0.1)
                    mutations.append(f"mutated_{key}")
        
        # Create new variant
        offspring = Variant(
            id=f"gen{self.generation}_var{len(self.variants)}",
            generation=self.generation,
            fitness=0.0,  # Will be evaluated externally
            traits=offspring_traits,
            parent_id=parents[0].id,
            mutations=mutations
        )
        
        self.generation += 1
        
        # Record evolution
        self.history.append({
            "action": "evolve",
            "generation": self.generation,
            "parents": [p.id for p in parents],
            "offspring": offspring.id,
            "mutations": mutations,
            "timestamp": time.time()
        })
        
        return offspring
    
    def cull_weak(self, threshold: float = 0.5):
        """Remove variants below fitness threshold"""
        before_count = len(self.variants)
        self.variants = [v for v in self.variants if v.fitness >= threshold]
        culled = before_count - len(self.variants)
        
        if culled > 0:
            self.history.append({
                "action": "cull",
                "culled_count": culled,
                "threshold": threshold,
                "generation": self.generation,
                "timestamp": time.time()
            })
        
        return culled
    
    def get_best(self) -> Optional[Variant]:
        """Get the fittest variant"""
        if not self.variants:
            return None
        return max(self.variants, key=lambda v: v.fitness)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get population statistics"""
        if not self.variants:
            return {
                "size": 0,
                "generation": self.generation,
                "avg_fitness": 0.0,
                "max_fitness": 0.0,
                "min_fitness": 0.0
            }
        
        fitnesses = [v.fitness for v in self.variants]
        
        return {
            "size": len(self.variants),
            "generation": self.generation,
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "max_fitness": max(fitnesses),
            "min_fitness": min(fitnesses),
            "diversity": len(set(str(v.traits) for v in self.variants)) / len(self.variants)
        }


class DarwinianAuditor:
    """Auditable Darwinian selection system"""
    
    def __init__(self):
        self.population = Population()
        self.audit_trail: List[Dict[str, Any]] = []
        self.selection_history: List[Tuple[str, float]] = []
        
    def evaluate_variant(
        self,
        variant: Variant,
        life_ok: bool,
        metrics: Dict[str, float]
    ) -> float:
        """
        Evaluate a variant's fitness.
        
        Args:
            variant: Variant to evaluate
            life_ok: Life Equation result
            metrics: Performance metrics
        
        Returns:
            Fitness score
        """
        fitness = darwinian_score(
            life_ok=life_ok,
            caos_phi=metrics.get("phi", 0.0),
            sr=metrics.get("sr", 0.0),
            G=metrics.get("G", 0.0),
            L_inf=metrics.get("L_inf", 0.0)
        )
        
        variant.fitness = fitness
        
        # Audit trail
        self.audit_trail.append({
            "action": "evaluate",
            "variant_id": variant.id,
            "life_ok": life_ok,
            "metrics": metrics,
            "fitness": fitness,
            "timestamp": time.time()
        })
        
        return fitness
    
    def select_for_promotion(self, min_fitness: float = 0.7) -> Optional[Variant]:
        """
        Select a variant for promotion.
        
        Args:
            min_fitness: Minimum fitness for promotion
        
        Returns:
            Selected variant or None
        """
        best = self.population.get_best()
        
        if best and best.fitness >= min_fitness:
            self.selection_history.append((best.id, best.fitness))
            
            self.audit_trail.append({
                "action": "select_promotion",
                "variant_id": best.id,
                "fitness": best.fitness,
                "threshold": min_fitness,
                "timestamp": time.time()
            })
            
            return best
        
        self.audit_trail.append({
            "action": "reject_promotion",
            "reason": "insufficient_fitness",
            "best_fitness": best.fitness if best else 0.0,
            "threshold": min_fitness,
            "timestamp": time.time()
        })
        
        return None
    
    def evolve_population(self) -> Optional[Variant]:
        """Evolve the population and return new variant"""
        new_variant = self.population.evolve()
        
        if new_variant:
            self.audit_trail.append({
                "action": "evolution",
                "new_variant": new_variant.id,
                "generation": self.population.generation,
                "timestamp": time.time()
            })
        
        return new_variant
    
    def get_audit_report(self, limit: int = 100) -> Dict[str, Any]:
        """Get audit report"""
        recent_trail = self.audit_trail[-limit:] if len(self.audit_trail) > limit else self.audit_trail
        
        # Count actions
        action_counts = {}
        for entry in self.audit_trail:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_actions": len(self.audit_trail),
            "action_counts": action_counts,
            "recent_trail": recent_trail,
            "population_stats": self.population.get_stats(),
            "selection_history": self.selection_history[-10:]
        }
    
    def rollback(self, generations: int = 1) -> bool:
        """
        Rollback evolution by N generations.
        
        Args:
            generations: Number of generations to rollback
        
        Returns:
            True if successful
        """
        target_gen = max(0, self.population.generation - generations)
        
        # Remove variants from newer generations
        self.population.variants = [
            v for v in self.population.variants
            if v.generation <= target_gen
        ]
        
        self.population.generation = target_gen
        
        self.audit_trail.append({
            "action": "rollback",
            "generations": generations,
            "new_generation": target_gen,
            "timestamp": time.time()
        })
        
        return True