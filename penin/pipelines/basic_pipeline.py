"""
Basic Evolution Pipeline
========================

Minimal E2E pipeline: Generate → Test → Decide → Record

This is the FIRST working auto-evolution pipeline!
"""

from dataclasses import dataclass
import random
from typing import Dict, Optional
from datetime import datetime

from penin.core.caos import compute_caos_plus_exponential
from penin.router_pkg.budget_tracker import BudgetTracker


def compute_linf_simple(metrics: list, weights: list, cost: float, lambda_cost: float) -> float:
    """Simple L∞ calculation"""
    eps = 1e-9
    harmonic_denom = sum(w / max(eps, m) for w, m in zip(weights, metrics))
    harmonic = 1.0 / harmonic_denom if harmonic_denom > eps else 0.0
    import math
    return harmonic * math.exp(-lambda_cost * cost)


@dataclass
class PipelineState:
    """Current state of evolution pipeline"""
    
    # CAOS+ parameters
    c: float = 0.85
    a: float = 0.40
    o: float = 0.35
    s: float = 0.82
    kappa: float = 20.0
    
    # L∞ parameters
    metrics: list = None
    weights: list = None
    lambda_cost: float = 0.5
    
    # Scores
    current_linf: float = 0.70
    current_caos: float = 1.50
    
    # Budget
    budget_remaining: float = 10.0
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = [0.85, 0.78, 0.92]
        if self.weights is None:
            self.weights = [0.4, 0.3, 0.3]


@dataclass
class Mutation:
    """Represents a mutation to be tested"""
    
    id: str
    type: str
    description: str
    params: Dict
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class TestResults:
    """Results from testing a mutation"""
    
    caos: float
    linf: float
    delta_linf: float
    cost: float = 0.05
    
    def is_improvement(self, beta_min: float = 0.01) -> bool:
        """Check if mutation is an improvement"""
        return self.delta_linf >= beta_min


@dataclass
class GuardDecision:
    """Decision from Σ-Guard"""
    
    verdict: str  # "PASS" or "FAIL"
    gates: Dict[str, bool]
    failed_gates: list
    delta_linf: float


class SimpleMutationGenerator:
    """
    Simple mutation generator (Ω-META lite).
    Generates parameter mutations for CAOS+ and L∞.
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
        
        self.mutation_types = [
            'adjust_caos_component',
            'adjust_linf_weights',
            'adjust_kappa',
            'adjust_lambda_cost',
        ]
    
    def generate(self, mutation_id: str) -> Mutation:
        """Generate one random mutation"""
        
        mutation_type = random.choice(self.mutation_types)
        
        if mutation_type == 'adjust_caos_component':
            component = random.choice(['c', 'a', 'o', 's'])
            delta = random.uniform(-0.08, 0.08)
            return Mutation(
                id=mutation_id,
                type='caos_component',
                description=f"Adjust {component.upper()} by {delta:+.3f}",
                params={'component': component, 'delta': delta}
            )
        
        elif mutation_type == 'adjust_linf_weights':
            idx = random.randint(0, 2)
            delta = random.uniform(-0.1, 0.1)
            return Mutation(
                id=mutation_id,
                type='linf_weight',
                description=f"Adjust weight[{idx}] by {delta:+.3f}",
                params={'index': idx, 'delta': delta}
            )
        
        elif mutation_type == 'adjust_kappa':
            delta = random.uniform(-5, 5)
            return Mutation(
                id=mutation_id,
                type='kappa',
                description=f"Adjust κ by {delta:+.1f}",
                params={'delta': delta}
            )
        
        elif mutation_type == 'adjust_lambda_cost':
            delta = random.uniform(-0.15, 0.15)
            return Mutation(
                id=mutation_id,
                type='lambda_cost',
                description=f"Adjust λ_cost by {delta:+.2f}",
                params={'delta': delta}
            )
    
    def apply_mutation(self, mutation: Mutation, state: PipelineState) -> PipelineState:
        """Apply mutation to state (returns new state)"""
        
        # Create new state (immutable)
        new_state = PipelineState(
            c=state.c,
            a=state.a,
            o=state.o,
            s=state.s,
            kappa=state.kappa,
            metrics=state.metrics.copy(),
            weights=state.weights.copy(),
            lambda_cost=state.lambda_cost,
            current_linf=state.current_linf,
            current_caos=state.current_caos,
            budget_remaining=state.budget_remaining,
        )
        
        # Apply mutation
        if mutation.type == 'caos_component':
            comp = mutation.params['component']
            delta = mutation.params['delta']
            current = getattr(new_state, comp)
            setattr(new_state, comp, max(0, min(1, current + delta)))
        
        elif mutation.type == 'linf_weight':
            idx = mutation.params['index']
            delta = mutation.params['delta']
            new_state.weights[idx] = max(0, min(1, new_state.weights[idx] + delta))
            # Renormalize weights
            total = sum(new_state.weights)
            new_state.weights = [w/total for w in new_state.weights]
        
        elif mutation.type == 'kappa':
            delta = mutation.params['delta']
            new_state.kappa = max(20, new_state.kappa + delta)  # κ ≥ 20
        
        elif mutation.type == 'lambda_cost':
            delta = mutation.params['delta']
            new_state.lambda_cost = max(0, new_state.lambda_cost + delta)
        
        return new_state


class SimpleGuard:
    """
    Simplified Σ-Guard (will enhance to full OPA/Rego later).
    Non-compensatory: ALL gates must pass.
    """
    
    def __init__(self):
        self.thresholds = {
            'beta_min': 0.01,      # ΔL∞ ≥ 1%
            'caos_min': 1.0,       # CAOS+ ≥ 1
            'linf_min': 0.5,       # L∞ ≥ 0.5
            'kappa_min': 20.0,     # κ ≥ 20
            'cost_max': 1.0,       # Cost ≤ budget
        }
    
    def evaluate(self, test_results: TestResults, state: PipelineState) -> GuardDecision:
        """Evaluate all gates (non-compensatory)"""
        
        gates = {
            'improvement': test_results.delta_linf >= self.thresholds['beta_min'],
            'caos_ok': test_results.caos >= self.thresholds['caos_min'],
            'linf_ok': test_results.linf >= self.thresholds['linf_min'],
            'kappa_ok': state.kappa >= self.thresholds['kappa_min'],
            'cost_ok': test_results.cost <= state.budget_remaining,
        }
        
        # Non-compensatory: ALL must pass
        verdict = "PASS" if all(gates.values()) else "FAIL"
        failed = [gate for gate, passed in gates.items() if not passed]
        
        return GuardDecision(
            verdict=verdict,
            gates=gates,
            failed_gates=failed,
            delta_linf=test_results.delta_linf,
        )


class BasicEvolutionPipeline:
    """
    Basic E2E Evolution Pipeline.
    
    Flow:
    1. Generate mutation (Ω-META lite)
    2. Test mutation (apply + evaluate)
    3. Decide (Σ-Guard lite)
    4. Record (WORM ledger)
    5. Promote or reject
    """
    
    def __init__(self, budget_usd: float = 10.0, seed: Optional[int] = None):
        self.state = PipelineState(budget_remaining=budget_usd)
        self.mutation_gen = SimpleMutationGenerator(seed=seed)
        self.guard = SimpleGuard()
        
        # Simple ledger
        self.ledger_entries = []
        
        # Stats
        self.cycles_run = 0
        self.mutations_promoted = 0
        self.mutations_rejected = 0
    
    def generate_mutation(self, cycle_num: int) -> Mutation:
        """Step 1: Generate mutation"""
        mutation_id = f"mut_{cycle_num:04d}"
        mutation = self.mutation_gen.generate(mutation_id)
        print(f"    🧬 Generated: {mutation.description}")
        return mutation
    
    def test_mutation(self, mutation: Mutation) -> TestResults:
        """Step 2: Test mutation in shadow mode"""
        
        # Apply mutation to get new state
        new_state = self.mutation_gen.apply_mutation(mutation, self.state)
        
        # Compute new scores
        caos_new = compute_caos_plus_exponential(
            c=new_state.c,
            a=new_state.a,
            o=new_state.o,
            s=new_state.s,
            kappa=new_state.kappa,
        )
        
        linf_new = compute_linf_simple(
            metrics=new_state.metrics,
            weights=new_state.weights,
            cost=0.05,
            lambda_cost=new_state.lambda_cost,
        )
        
        delta_linf = linf_new - self.state.current_linf
        
        print(f"    🧪 Tested: CAOS+={caos_new:.3f}, L∞={linf_new:.3f}, ΔL∞={delta_linf:+.4f}")
        
        return TestResults(
            caos=caos_new,
            linf=linf_new,
            delta_linf=delta_linf,
            cost=0.05,
        )
    
    def decide(self, test_results: TestResults) -> GuardDecision:
        """Step 3: Decide with Σ-Guard"""
        
        decision = self.guard.evaluate(test_results, self.state)
        
        if decision.verdict == "PASS":
            print(f"    ✅ Σ-Guard: PASS (all gates ✅)")
        else:
            print(f"    ❌ Σ-Guard: FAIL (gates: {', '.join(decision.failed_gates)})")
        
        return decision
    
    def record(self, mutation: Mutation, test_results: TestResults, decision: GuardDecision):
        """Step 4: Record in WORM ledger"""
        
        import hashlib
        import json
        
        entry = {
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'event_type': 'mutation_decision',
            'mutation_id': mutation.id,
            'mutation': {
                'type': mutation.type,
                'description': mutation.description,
                'params': mutation.params,
            },
            'test_results': {
                'caos': test_results.caos,
                'linf': test_results.linf,
                'delta_linf': test_results.delta_linf,
                'cost': test_results.cost,
            },
            'decision': {
                'verdict': decision.verdict,
                'gates': decision.gates,
                'failed_gates': decision.failed_gates,
            },
        }
        
        entry_hash = hashlib.blake2b(
            json.dumps(entry, sort_keys=True).encode(),
            digest_size=16
        ).hexdigest()
        
        entry['hash'] = entry_hash
        self.ledger_entries.append(entry)
        
        print(f"    📝 Recorded in ledger (hash={entry_hash[:16]}...)")
    
    def promote_or_reject(self, mutation: Mutation, test_results: TestResults, decision: GuardDecision):
        """Step 5: Promote or reject based on decision"""
        
        if decision.verdict == "PASS":
            # Promote: apply mutation permanently
            new_state = self.mutation_gen.apply_mutation(mutation, self.state)
            self.state = new_state
            self.state.current_linf = test_results.linf
            self.state.current_caos = test_results.caos
            self.mutations_promoted += 1
            print(f"    🎉 PROMOTED! New state: L∞={self.state.current_linf:.3f}, CAOS+={self.state.current_caos:.3f}")
        else:
            # Reject: rollback
            self.mutations_rejected += 1
            print(f"    🔙 REJECTED - Rolled back to previous state")
    
    def run_cycle(self, cycle_num: int) -> Dict:
        """Run one complete E2E evolution cycle"""
        
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║  Cycle {cycle_num:04d}                                           ║")
        print(f"  ╚{'═'*56}╝")
        
        # 1. Generate
        mutation = self.generate_mutation(cycle_num)
        
        # 2. Test
        test_results = self.test_mutation(mutation)
        
        # 3. Decide
        decision = self.guard.evaluate(test_results, self.state)
        
        # 4. Record
        self.record(mutation, test_results, decision)
        
        # 5. Promote or reject
        self.promote_or_reject(mutation, test_results, decision)
        
        self.cycles_run += 1
        
        return {
            'mutation': mutation,
            'test_results': test_results,
            'decision': decision,
        }
    
    def run_n_cycles(self, n: int):
        """Run N evolution cycles"""
        
        print(f"\n🚀 BASIC EVOLUTION PIPELINE")
        print(f"   Cycles: {n}")
        print(f"   Initial: L∞={self.state.current_linf:.3f}, CAOS+={self.state.current_caos:.3f}")
        print()
        
        for i in range(n):
            self.run_cycle(i + 1)
        
        # Summary
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║  SUMMARY                                             ║")
        print(f"  ╚{'═'*56}╝")
        print(f"\n  Cycles run: {self.cycles_run}")
        print(f"  Promoted: {self.mutations_promoted}")
        print(f"  Rejected: {self.mutations_rejected}")
        print(f"  Final L∞: {self.state.current_linf:.3f}")
        print(f"  Final CAOS+: {self.state.current_caos:.3f}")
        print(f"  Ledger entries: {len(self.ledger_entries)}")
        print()
        
        return {
            'cycles': self.cycles_run,
            'promoted': self.mutations_promoted,
            'rejected': self.mutations_rejected,
            'final_linf': self.state.current_linf,
            'final_caos': self.state.current_caos,
        }
