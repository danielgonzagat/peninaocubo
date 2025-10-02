"""
PENIN-Ω Runners Module
=====================

Implements the main evolution cycle orchestrator that coordinates all components:
mutators, evaluators, guards, scoring, and deployment decisions.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

from .acfa import LeagueConfig, LeagueOrchestrator, run_full_deployment_cycle
from .caos import quick_caos_phi
from .ethics_metrics import EthicsCalculator, EthicsGate
from .evaluators import TaskBattery, TaskBatteryConfig
from .guards import quick_sigma_guard_check_simple
from .ledger import WORMLedger

# Import other omega modules
from .mutators import MutationConfig, ParameterMutator
from .scoring import quick_harmonic, quick_score_gate
from .sr import quick_sr_harmonic
from .tuner import create_penin_tuner


@dataclass
class EvolutionConfig:
    """Configuration for evolution cycles"""

    n_challengers: int = 8
    budget_minutes: int = 30
    provider_id: str = "openai"
    dry_run: bool = False
    seed: int = 42

    # Evaluation settings
    max_tasks_per_metric: int = 3
    evaluation_timeout_s: int = 60

    # Deployment settings
    auto_deploy: bool = True
    shadow_duration_s: int = 300
    canary_duration_s: int = 600

    # Tuning settings
    enable_auto_tuning: bool = True
    tuning_learning_rate: float = 0.01


@dataclass
class CycleResult:
    """Result of an evolution cycle"""

    cycle_id: str
    timestamp: float
    config: EvolutionConfig

    # Generated variants
    challengers: list[dict[str, Any]]

    # Evaluation results
    evaluation_results: dict[str, Any]

    # Scoring results
    scoring_results: dict[str, Any]

    # Gate results
    gate_results: dict[str, Any]

    # Final decision
    decision: str  # 'promote', 'canary', 'reject'
    decision_reason: str

    # Best challenger
    best_challenger: dict[str, Any] | None

    # Performance metrics
    total_duration_s: float
    cost_usd: float

    # Evidence
    evidence_hash: str


class EvolutionRunner:
    """Main evolution cycle orchestrator"""

    def __init__(self, config: EvolutionConfig = None):
        self.config = config or EvolutionConfig()

        # Initialize components
        self.mutator = ParameterMutator(MutationConfig(seed=self.config.seed))
        self.evaluator = TaskBattery(
            TaskBatteryConfig(
                seed=self.config.seed,
                max_tasks_per_metric=self.config.max_tasks_per_metric,
            )
        )
        self.ethics_calculator = EthicsCalculator()
        self.ethics_gate = EthicsGate()
        self.league = LeagueOrchestrator(
            LeagueConfig(
                shadow_duration_s=self.config.shadow_duration_s,
                canary_duration_s=self.config.canary_duration_s,
            )
        )

        # Initialize tuner if enabled
        self.tuner = create_penin_tuner() if self.config.enable_auto_tuning else None

        # Initialize WORM ledger
        self.ledger = WORMLedger("evolution_cycles.db")

        print(f"🚀 Evolution runner initialized (seed={self.config.seed})")

    async def evolve_one_cycle(self, base_config: dict[str, Any] = None) -> CycleResult:
        """
        Execute one complete evolution cycle

        Args:
            base_config: Base configuration to mutate from

        Returns:
            CycleResult with all cycle information
        """
        cycle_start = time.time()
        cycle_id = f"cycle_{int(cycle_start)}"

        print(f"\n🔄 Starting evolution cycle {cycle_id}")
        print("=" * 60)

        # Default base config if none provided
        if base_config is None:
            base_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500,
                "model": "gpt-4",
            }

        try:
            # Step 1: Generate challengers
            print("🧬 Step 1: Generating challengers...")
            challengers = await self._generate_challengers(base_config)
            print(f"   Generated {len(challengers)} challengers")

            # Step 2: Evaluate challengers
            print("📊 Step 2: Evaluating challengers...")
            evaluation_results = await self._evaluate_challengers(challengers)
            print(f"   Evaluated {len(evaluation_results)} challengers")

            # Step 3: Apply gates and scoring
            print("🛡️  Step 3: Applying gates and scoring...")
            scoring_results, gate_results = await self._score_and_gate_challengers(
                challengers, evaluation_results
            )

            # Step 4: Select best challenger
            print("🏆 Step 4: Selecting best challenger...")
            best_challenger, decision, decision_reason = self._select_best_challenger(
                challengers, scoring_results, gate_results
            )

            # Step 5: Deploy if not dry run
            if not self.config.dry_run and self.config.auto_deploy and best_challenger:
                print("🚀 Step 5: Deploying challenger...")
                deployment_success = await self._deploy_challenger(best_challenger)
                if deployment_success:
                    decision = "promoted"
                else:
                    decision = "deployment_failed"

            # Step 6: Update tuner
            if self.tuner:
                print("🎯 Step 6: Updating tuner...")
                cycle_metrics = self._extract_cycle_metrics(
                    evaluation_results, scoring_results
                )
                updated_params = self.tuner.update_from_cycle_result(cycle_metrics)
                print(f"   Updated {len(updated_params)} parameters")

            # Create result
            total_duration = time.time() - cycle_start
            cost_usd = self._estimate_cycle_cost(challengers, evaluation_results)

            result = CycleResult(
                cycle_id=cycle_id,
                timestamp=cycle_start,
                config=self.config,
                challengers=challengers,
                evaluation_results=evaluation_results,
                scoring_results=scoring_results,
                gate_results=gate_results,
                decision=decision,
                decision_reason=decision_reason,
                best_challenger=best_challenger,
                total_duration_s=total_duration,
                cost_usd=cost_usd,
                evidence_hash=self._compute_evidence_hash(
                    cycle_id, challengers, evaluation_results
                ),
            )

            # Record in WORM ledger
            self._record_cycle_result(result)

            print(f"\n✅ Cycle {cycle_id} completed in {total_duration:.1f}s")
            print(f"   Decision: {decision} ({decision_reason})")
            print(f"   Cost: ${cost_usd:.4f}")

            return result

        except Exception as e:
            print(f"❌ Cycle {cycle_id} failed: {e}")
            # Create failure result
            result = CycleResult(
                cycle_id=cycle_id,
                timestamp=cycle_start,
                config=self.config,
                challengers=[],
                evaluation_results={},
                scoring_results={},
                gate_results={},
                decision="failed",
                decision_reason=str(e),
                best_challenger=None,
                total_duration_s=time.time() - cycle_start,
                cost_usd=0.0,
                evidence_hash="",
            )

            self._record_cycle_result(result)
            raise

    async def _generate_challengers(
        self, base_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate challenger configurations"""
        mutation_results = self.mutator.mutate_parameters(
            base_config, self.config.n_challengers
        )

        challengers = []
        for i, result in enumerate(mutation_results):
            challenger = {
                "challenger_id": f"challenger_{i:03d}",
                "config": result.mutated_config,
                "mutation_type": result.mutation_type,
                "config_hash": result.config_hash,
                "seed_used": result.seed_used,
            }
            challengers.append(challenger)

        return challengers

    async def _evaluate_challengers(
        self, challengers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Evaluate all challengers using the task battery"""
        evaluation_results = {}

        for challenger in challengers:
            challenger_id = challenger["challenger_id"]

            # Create mock model function for evaluation
            def mock_model_fn(input_text: str) -> str:
                # In a real implementation, this would call the actual model
                # For now, return a simple response based on config
                config = challenger["config"]
                temp = config.get("temperature", 0.7)

                # Simulate different responses based on temperature
                if temp < 0.3:
                    return "42"  # Deterministic
                elif temp > 1.0:
                    return "The answer varies depending on context and interpretation"  # Creative
                else:
                    return "42 is the answer"  # Balanced

            # Evaluate using task battery
            try:
                eval_result = self.evaluator.evaluate_all_metrics(mock_model_fn)
                evaluation_results[challenger_id] = eval_result
            except Exception as e:
                print(f"   ⚠️  Evaluation failed for {challenger_id}: {e}")
                evaluation_results[challenger_id] = {
                    "aggregate_scores": {
                        "U": {"mean": 0},
                        "S": {"mean": 0},
                        "C": {"mean": 0},
                        "L": {"mean": 0},
                    },
                    "overall_score": 0.0,
                    "error": str(e),
                }

        return evaluation_results

    async def _score_and_gate_challengers(
        self, challengers: list[dict[str, Any]], evaluation_results: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Apply scoring and gates to challengers"""
        scoring_results = {}
        gate_results = {}

        for challenger in challengers:
            challenger_id = challenger["challenger_id"]
            eval_result = evaluation_results.get(challenger_id, {})

            if "aggregate_scores" in eval_result:
                # Extract USCL scores
                u_score = eval_result["aggregate_scores"]["U"]["mean"]
                s_score = eval_result["aggregate_scores"]["S"]["mean"]
                c_score = eval_result["aggregate_scores"]["C"]["mean"]
                l_score = eval_result["aggregate_scores"]["L"]["mean"]

                # Calculate L∞ harmonic score
                linf_score = quick_harmonic([u_score, s_score, c_score, l_score])

                # Calculate CAOS+ phi
                caos_phi = quick_caos_phi(
                    c_score, 0.8, 0.9, s_score
                )  # Mock A, O values

                # Calculate SR score
                sr_score = quick_sr_harmonic(0.9, True, 0.8, 0.85)  # Mock values

                # Apply score gate
                gate_passed, gate_details = quick_score_gate(
                    u_score, s_score, c_score, l_score
                )

                # Ethics check (simplified)
                ethics_passed = True  # Would do real ethics check here

                # Sigma guard check
                sigma_guard_passed = quick_sigma_guard_check_simple(
                    ece=0.05, rho_bias=1.02, fairness=0.9, consent=True, eco_ok=True
                )

                scoring_results[challenger_id] = {
                    "u_score": u_score,
                    "s_score": s_score,
                    "c_score": c_score,
                    "l_score": l_score,
                    "linf_score": linf_score,
                    "caos_phi": caos_phi,
                    "sr_score": sr_score,
                }

                gate_results[challenger_id] = {
                    "score_gate_passed": gate_passed,
                    "score_gate_details": gate_details,
                    "ethics_passed": ethics_passed,
                    "sigma_guard_passed": sigma_guard_passed,
                    "all_gates_passed": gate_passed
                    and ethics_passed
                    and sigma_guard_passed,
                }
            else:
                # Failed evaluation
                scoring_results[challenger_id] = {
                    "u_score": 0,
                    "s_score": 0,
                    "c_score": 0,
                    "l_score": 0,
                    "linf_score": 0,
                    "caos_phi": 0,
                    "sr_score": 0,
                }
                gate_results[challenger_id] = {
                    "score_gate_passed": False,
                    "ethics_passed": False,
                    "sigma_guard_passed": False,
                    "all_gates_passed": False,
                }

        return scoring_results, gate_results

    def _select_best_challenger(
        self,
        challengers: list[dict[str, Any]],
        scoring_results: dict[str, Any],
        gate_results: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str, str]:
        """Select the best challenger based on scores and gates"""

        # Filter challengers that passed all gates
        valid_challengers = []
        for challenger in challengers:
            challenger_id = challenger["challenger_id"]
            if gate_results.get(challenger_id, {}).get("all_gates_passed", False):
                challenger["linf_score"] = scoring_results[challenger_id]["linf_score"]
                valid_challengers.append(challenger)

        if not valid_challengers:
            return None, "reject", "no_challengers_passed_gates"

        # Select challenger with highest L∞ score
        best_challenger = max(valid_challengers, key=lambda c: c["linf_score"])

        # Determine decision based on score improvement
        linf_score = best_challenger["linf_score"]
        if linf_score > 0.8:
            decision = "promote"
            reason = f"high_linf_score_{linf_score:.3f}"
        elif linf_score > 0.6:
            decision = "canary"
            reason = f"moderate_linf_score_{linf_score:.3f}"
        else:
            decision = "reject"
            reason = f"low_linf_score_{linf_score:.3f}"

        return best_challenger, decision, reason

    async def _deploy_challenger(self, challenger: dict[str, Any]) -> bool:
        """Deploy challenger using league orchestrator"""
        try:
            success = await run_full_deployment_cycle(self.league, challenger["config"])
            return success
        except Exception as e:
            print(f"   ❌ Deployment failed: {e}")
            return False

    def _extract_cycle_metrics(
        self, evaluation_results: dict[str, Any], scoring_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract metrics for tuner update"""
        if not evaluation_results or not scoring_results:
            return {}

        # Get metrics from best performer
        best_eval = max(
            evaluation_results.values(), key=lambda x: x.get("overall_score", 0)
        )

        return {
            "linf_score": best_eval.get("overall_score", 0),
            "U_score": best_eval["aggregate_scores"]["U"]["mean"],
            "S_score": best_eval["aggregate_scores"]["S"]["mean"],
            "C_score": best_eval["aggregate_scores"]["C"]["mean"],
            "L_score": best_eval["aggregate_scores"]["L"]["mean"],
            "caos_phi": 0.5,  # Would extract from scoring results
            "cost_over_budget": False,  # Would check actual budget
            "recent_promotion_rate": 0.1,  # Would track from history
            "ethics_passed": True,
        }

    def _estimate_cycle_cost(
        self, challengers: list[dict[str, Any]], evaluation_results: dict[str, Any]
    ) -> float:
        """Estimate total cost of the cycle"""
        # Simple estimation based on number of challengers and evaluations
        base_cost_per_challenger = 0.01  # $0.01 per challenger
        evaluation_cost = len(challengers) * self.config.max_tasks_per_metric * 0.001

        return base_cost_per_challenger * len(challengers) + evaluation_cost

    def _compute_evidence_hash(
        self,
        cycle_id: str,
        challengers: list[dict[str, Any]],
        evaluation_results: dict[str, Any],
    ) -> str:
        """Compute evidence hash for the cycle"""
        evidence_data = {
            "cycle_id": cycle_id,
            "challenger_hashes": [c.get("config_hash", "") for c in challengers],
            "evaluation_summary": {
                cid: result.get("overall_score", 0)
                for cid, result in evaluation_results.items()
            },
        }

        import hashlib

        evidence_str = json.dumps(evidence_data, sort_keys=True)
        return hashlib.sha256(evidence_str.encode()).hexdigest()

    def _record_cycle_result(self, result: CycleResult):
        """Record cycle result in WORM ledger"""
        try:
            record_data = {
                "event_type": "EVOLUTION_CYCLE",
                "cycle_id": result.cycle_id,
                "timestamp": result.timestamp,
                "decision": result.decision,
                "decision_reason": result.decision_reason,
                "n_challengers": len(result.challengers),
                "best_challenger_id": (
                    result.best_challenger["challenger_id"]
                    if result.best_challenger
                    else None
                ),
                "duration_s": result.total_duration_s,
                "cost_usd": result.cost_usd,
                "evidence_hash": result.evidence_hash,
            }

            self.ledger.record(record_data)
            print("   📝 Recorded cycle result in WORM ledger")

        except Exception as e:
            print(f"   ⚠️  Failed to record in WORM ledger: {e}")


# Utility functions
async def run_evolution_cycles(
    n_cycles: int = 5, config: EvolutionConfig = None
) -> list[CycleResult]:
    """Run multiple evolution cycles"""
    runner = EvolutionRunner(config)
    results = []

    for i in range(n_cycles):
        print(f"\n🔄 Running cycle {i + 1}/{n_cycles}")
        try:
            result = await runner.evolve_one_cycle()
            results.append(result)
        except Exception as e:
            print(f"❌ Cycle {i + 1} failed: {e}")
            break

    return results


# Example usage
if __name__ == "__main__":

    async def demo():
        config = EvolutionConfig(
            n_challengers=3, budget_minutes=5, dry_run=True, max_tasks_per_metric=2
        )

        results = await run_evolution_cycles(2, config)

        print(f"\n📊 Completed {len(results)} cycles")
        for result in results:
            print(f"  {result.cycle_id}: {result.decision} ({result.decision_reason})")

    asyncio.run(demo())
