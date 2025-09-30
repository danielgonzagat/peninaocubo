"""
PENIN-Ω Runners Module
=====================

Implements the main evolution cycle orchestrator that coordinates all components:
mutators, evaluators, guards, scoring, and deployment decisions.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Import other omega modules
from .mutators import ParameterMutator, MutationConfig
from .evaluators import TaskBattery, TaskBatteryConfig, quick_evaluate_model
from .ethics_metrics import EthicsCalculator, EthicsGate
from .scoring import quick_harmonic, quick_score_gate
from .caos import quick_caos_phi
from .sr import quick_sr_harmonic
from .guards import quick_sigma_guard_check_simple
from .life_eq import life_equation, LifeEquationEngine
from .acfa import LeagueOrchestrator, LeagueConfig, run_full_deployment_cycle
from .tuner import PeninOmegaTuner, create_penin_tuner
from .ledger import WORMLedger
from .life_eq import life_equation

# Import Vida+ modules
from .life_eq import life_equation, LifeVerdict
from .fractal import build_fractal, propagate_update
from .swarm import heartbeat, sample_global_state
from .caos_kratos import phi_kratos
from .market import InternalMarket
from .neural_chain import add_block
from .self_rag import ingest_text, query, self_cycle
from .api_metabolizer import record_call, suggest_replay
from .immunity import guard as immunity_guard
from .checkpoint import save_snapshot, restore_last
from .game import update_gradient, get_gradient
from .darwin_audit import audit_challenger
from .zero_consciousness import assert_zero_consciousness


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
    
    # Vida+ settings
    enable_vida_plus: bool = True
    base_alpha: float = 0.02
    life_equation_thresholds: Dict[str, float] = None
    enable_fractal_dsl: bool = True
    enable_swarm_cognitive: bool = True
    enable_caos_kratos: bool = True
    enable_marketplace: bool = True
    enable_neural_chain: bool = True
    enable_self_rag: bool = True
    enable_api_metabolizer: bool = True
    enable_immunity: bool = True
    enable_checkpoint: bool = True
    enable_game: bool = True
    enable_darwin_audit: bool = True
    enable_zero_consciousness: bool = True
    
    def __post_init__(self):
        if self.life_equation_thresholds is None:
            self.life_equation_thresholds = {
                "beta_min": 0.01,
                "theta_caos": 0.25,
                "tau_sr": 0.80,
                "theta_G": 0.85
            }


@dataclass
class CycleResult:
    """Result of an evolution cycle"""
    cycle_id: str
    timestamp: float
    config: EvolutionConfig
    
    # Generated variants
    challengers: List[Dict[str, Any]]
    
    # Evaluation results
    evaluation_results: Dict[str, Any]
    
    # Scoring results
    scoring_results: Dict[str, Any]
    
    # Gate results
    gate_results: Dict[str, Any]
    
    # Vida+ results
    life_equation_results: Dict[str, Any] = None
    fractal_propagation_results: Dict[str, Any] = None
    swarm_coherence_results: Dict[str, Any] = None
    immunity_results: Dict[str, Any] = None
    darwin_audit_results: Dict[str, Any] = None
    zero_consciousness_results: Dict[str, Any] = None
    
    # Final decision
    decision: str  # 'promote', 'canary', 'reject'
    decision_reason: str
    
    # Best challenger
    best_challenger: Optional[Dict[str, Any]]
    
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
        self.evaluator = TaskBattery(TaskBatteryConfig(
            seed=self.config.seed,
            max_tasks_per_metric=self.config.max_tasks_per_metric
        ))
        self.ethics_calculator = EthicsCalculator()
        self.ethics_gate = EthicsGate()
        self.league = LeagueOrchestrator(LeagueConfig(
            shadow_duration_s=self.config.shadow_duration_s,
            canary_duration_s=self.config.canary_duration_s
        ))
        
        # Initialize tuner if enabled
        self.tuner = create_penin_tuner() if self.config.enable_auto_tuning else None
        
        # Initialize WORM ledger
        self.ledger = WORMLedger("evolution_cycles.db")
        
        # Initialize Life Equation Engine
        self.life_engine = LifeEquationEngine(
            thresholds={
                "beta_min": 0.01,
                "theta_caos": 0.25,
                "tau_sr": 0.80,
                "theta_G": 0.85
            },
            base_alpha=0.001
        )
        
        print(f"🚀 Evolution runner initialized (seed={self.config.seed})")
        print(f"   Life Equation Engine: {self.life_engine.get_config()}")
    
    async def evolve_one_cycle(self, base_config: Dict[str, Any] = None) -> CycleResult:
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
                "model": "gpt-4"
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
            
            # Step 3.5: Apply Life Equation (+) if Vida+ enabled
            vida_plus_results = {}
            if self.config.enable_vida_plus:
                print("🌟 Step 3.5: Applying Life Equation (+)...")
                vida_plus_results = await self._apply_vida_plus_gates(
                    challengers, scoring_results, gate_results
                )
            
            # Step 4: Select best challenger
            print("🏆 Step 4: Selecting best challenger...")
            best_challenger, decision, decision_reason = self._select_best_challenger(
                challengers, scoring_results, gate_results, vida_plus_results
            )

            # Vida+ gate: apply non-compensatory Life Equation on the best challenger
            if best_challenger is not None:
                cid = best_challenger['challenger_id']
                s = scoring_results.get(cid, {})
                # Extract scores
                u = float(s.get('u_score', 0.0))
                ss = float(s.get('s_score', 0.0))
                c = float(s.get('c_score', 0.0))
                l = float(s.get('l_score', 0.0))
                linf_val = float(s.get('linf_score', 0.0))
                caos_phi = float(s.get('caos_phi', 0.0))
                sr_score = float(s.get('sr_score', 0.0))

                # Inputs for Life Equation
                ethics_input = {"ece": 0.006, "rho_bias": 1.02, "consent": True, "eco_ok": True}
                risk_history = [0.95, 0.93, 0.90]
                caos_components = (max(0.0, min(1.0, c)), 0.66, 1.0, 1.0)
                sr_components = (0.90, True, 0.80, 0.85)
                linf_metrics = {"U": u, "S": ss, "L": l, "C": max(1e-6, 1.0 - c)}
                linf_weights = {k: 1.0 for k in linf_metrics.keys()}
                linf_weights["lambda_c"] = 0.05
                cost_norm = c
                G = max(0.0, min(1.0, (caos_phi + sr_score) / 2.0))
                dL_inf = linf_val - 0.60
                verdict = life_equation(
                    base_alpha=1e-3,
                    ethics_input=ethics_input,
                    risk_history=risk_history,
                    caos_components=caos_components,
                    sr_components=sr_components,
                    linf_weights=linf_weights,
                    linf_metrics=linf_metrics,
                    cost=cost_norm,
                    G=G,
                    dL_inf=dL_inf,
                    thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
                )
                # Enforce fail-closed
                if not verdict.ok:
                    decision = "reject"
                    decision_reason = "vida_gate_failed"
            
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
                cycle_metrics = self._extract_cycle_metrics(evaluation_results, scoring_results)
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
                life_equation_results=vida_plus_results.get("life_equation", {}),
                fractal_propagation_results=vida_plus_results.get("fractal", {}),
                swarm_coherence_results=vida_plus_results.get("swarm", {}),
                immunity_results=vida_plus_results.get("immunity", {}),
                darwin_audit_results=vida_plus_results.get("darwin_audit", {}),
                zero_consciousness_results=vida_plus_results.get("zero_consciousness", {}),
                decision=decision,
                decision_reason=decision_reason,
                best_challenger=best_challenger,
                total_duration_s=total_duration,
                cost_usd=cost_usd,
                evidence_hash=self._compute_evidence_hash(cycle_id, challengers, evaluation_results)
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
                evidence_hash=""
            )
            
            # Record failure in WORM ledger
            self._record_cycle_result(result)
            raise


# Função de conveniência para compatibilidade com CLI
def quick_evolution_cycle(n_cycles: int = 1, dry_run: bool = True) -> Dict[str, Any]:
    """
    Execução rápida de ciclos evolutivos
    
    Args:
        n_cycles: Número de ciclos
        dry_run: Se True, não faz deploy real
        
    Returns:
        Relatório dos ciclos
    """
    import asyncio
    
    config = EvolutionConfig(
        n_challengers=3,
        dry_run=dry_run,
        auto_deploy=False
    )
    
    runner = EvolutionRunner(config)
    
    async def run_cycles():
        results = []
        for i in range(n_cycles):
            print(f"\n🔄 Ciclo {i+1}/{n_cycles}")
            result = await runner.evolve_one_cycle()
            results.append(result)
        return results
    
    # Executar ciclos
    results = asyncio.run(run_cycles())
    
    # Compilar relatório
    total_cost = sum(r.cost_usd for r in results)
    successful_cycles = sum(1 for r in results if r.decision != "reject")
    
    # Coletar métricas da Equação de Vida (+)
    life_metrics = []
    for result in results:
        for challenger_id, gate_result in result.gate_results.items():
            if "life_equation_details" in gate_result:
                life_details = gate_result["life_equation_details"]
                if "metrics" in life_details:
                    life_metrics.append(life_details["metrics"])
    
    # Calcular médias das métricas de vida
    avg_life_metrics = {}
    if life_metrics:
        for key in life_metrics[0].keys():
            values = [m[key] for m in life_metrics if key in m]
            avg_life_metrics[key] = sum(values) / len(values) if values else 0.0
    
    return {
        "n_cycles": n_cycles,
        "successful_cycles": successful_cycles,
        "success_rate": successful_cycles / n_cycles if n_cycles > 0 else 0.0,
        "total_cost_usd": total_cost,
        "avg_cost_per_cycle": total_cost / n_cycles if n_cycles > 0 else 0.0,
        "life_equation_metrics": avg_life_metrics,
        "dry_run": dry_run,
        "timestamp": time.time()
    }
    
    async def _generate_challengers(self, base_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate challenger configurations"""
        mutation_results = self.mutator.mutate_parameters(base_config, self.config.n_challengers)
        
        challengers = []
        for i, result in enumerate(mutation_results):
            challenger = {
                'challenger_id': f"challenger_{i:03d}",
                'config': result.mutated_config,
                'mutation_type': result.mutation_type,
                'config_hash': result.config_hash,
                'seed_used': result.seed_used
            }
            challengers.append(challenger)
        
        return challengers
    
    async def _evaluate_challengers(self, challengers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate all challengers using the task battery"""
        evaluation_results = {}
        
        for challenger in challengers:
            challenger_id = challenger['challenger_id']
            
            # Create mock model function for evaluation
            def mock_model_fn(input_text: str) -> str:
                # In a real implementation, this would call the actual model
                # For now, return a simple response based on config
                config = challenger['config']
                temp = config.get('temperature', 0.7)
                
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
                    'aggregate_scores': {'U': {'mean': 0}, 'S': {'mean': 0}, 'C': {'mean': 0}, 'L': {'mean': 0}},
                    'overall_score': 0.0,
                    'error': str(e)
                }
        
        return evaluation_results
    
    async def _score_and_gate_challengers(self, challengers: List[Dict[str, Any]], 
                                        evaluation_results: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply scoring and gates to challengers"""
        scoring_results = {}
        gate_results = {}
        
        for challenger in challengers:
            challenger_id = challenger['challenger_id']
            eval_result = evaluation_results.get(challenger_id, {})
            
            if 'aggregate_scores' in eval_result:
                # Extract USCL scores
                u_score = eval_result['aggregate_scores']['U']['mean']
                s_score = eval_result['aggregate_scores']['S']['mean']
                c_score = eval_result['aggregate_scores']['C']['mean']
                l_score = eval_result['aggregate_scores']['L']['mean']
                
                # Calculate L∞ harmonic score
                linf_score = quick_harmonic([u_score, s_score, c_score, l_score])
                
                # Calculate CAOS+ phi
                caos_phi = quick_caos_phi(c_score, 0.8, 0.9, s_score)  # Mock A, O values
                
                # Calculate SR score
                sr_score = quick_sr_harmonic(0.9, True, 0.8, 0.85)  # Mock values
                
                # Apply score gate
                gate_passed, gate_details = quick_score_gate(u_score, s_score, c_score, l_score)
                
                # Ethics check (simplified)
                ethics_passed = True  # Would do real ethics check here
                
                # Sigma guard check
                sigma_guard_passed = quick_sigma_guard_check_simple(
                    ece=0.05, rho_bias=1.02, fairness=0.9, consent=True, eco_ok=True
                )
                
                # *** EQUAÇÃO DE VIDA (+) - Gate não-compensatório ***
                # Calcular ΔL∞ (diferença com baseline)
                baseline_linf = 0.5  # Baseline fictício
                delta_linf = linf_score - baseline_linf
                
                # Preparar inputs para Equação de Vida (+)
                ethics_input = {
                    "ece": 0.005,
                    "rho_bias": 1.02,
                    "fairness": 0.9,
                    "consent_valid": True,
                    "eco_impact": 0.3
                }
                
                risk_series = [0.9, 0.88, 0.85]  # Série contrativa simulada
                caos_components = (c_score, 0.8, 0.9, s_score)  # (C, A, O, S)
                sr_components = (0.9, ethics_passed, 0.8, 0.85)  # (awareness, ethics_ok, autocorr, metacog)
                
                linf_weights = {"u": 0.25, "s": 0.25, "c": 0.25, "l": 0.25}
                linf_metrics = {"u": u_score, "s": s_score, "c": c_score, "l": l_score}
                
                G = 0.90  # Coerência global simulada
                
                # Avaliar Equação de Vida (+)
                life_verdict = self.life_engine.evaluate(
                    ethics_input=ethics_input,
                    risk_series=risk_series,
                    caos_components=caos_components,
                    sr_components=sr_components,
                    linf_weights=linf_weights,
                    linf_metrics=linf_metrics,
                    cost=0.02,
                    ethical_ok_flag=ethics_passed,
                    G=G,
                    dL_inf=delta_linf
                )
                
                life_passed = life_verdict.ok
                alpha_eff = life_verdict.alpha_eff
                
                scoring_results[challenger_id] = {
                    'u_score': u_score,
                    's_score': s_score,
                    'c_score': c_score,
                    'l_score': l_score,
                    'linf_score': linf_score,
                    'caos_phi': caos_phi,
                    'sr_score': sr_score,
                    'delta_linf': delta_linf,
                    'alpha_eff': alpha_eff,
                    'life_verdict': life_verdict.to_dict()
                }
                
                # Gate final: todos os gates anteriores + Equação de Vida (+)
                all_gates_passed = (gate_passed and ethics_passed and 
                                  sigma_guard_passed and life_passed)
                
                gate_results[challenger_id] = {
                    'score_gate_passed': gate_passed,
                    'score_gate_details': gate_details,
                    'ethics_passed': ethics_passed,
                    'sigma_guard_passed': sigma_guard_passed,
                    'life_equation_passed': life_passed,
                    'life_equation_details': life_verdict.to_dict(),
                    'all_gates_passed': all_gates_passed
                }
            else:
                # Failed evaluation
                scoring_results[challenger_id] = {
                    'u_score': 0, 's_score': 0, 'c_score': 0, 'l_score': 0,
                    'linf_score': 0, 'caos_phi': 0, 'sr_score': 0,
                    'delta_linf': 0, 'alpha_eff': 0.0,
                    'life_verdict': {'ok': False, 'alpha_eff': 0.0, 'reasons': {'evaluation_failed': True}}
                }
                gate_results[challenger_id] = {
                    'score_gate_passed': False,
                    'ethics_passed': False,
                    'sigma_guard_passed': False,
                    'life_equation_passed': False,
                    'life_equation_details': {'ok': False, 'alpha_eff': 0.0},
                    'all_gates_passed': False
                }
        
        return scoring_results, gate_results
    
    async def _apply_vida_plus_gates(self, challengers: List[Dict[str, Any]], 
                                   scoring_results: Dict[str, Any],
                                   gate_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Vida+ gates including Life Equation (+)"""
        vida_plus_results = {
            "life_equation": {},
            "fractal": {},
            "swarm": {},
            "immunity": {},
            "darwin_audit": {},
            "zero_consciousness": {}
        }
        
        # Get global coherence from swarm
        G = 0.9  # Default value, would be calculated from swarm
        if self.config.enable_swarm_cognitive:
            try:
                global_state = sample_global_state()
                G = global_state.get("coherence", 0.9)
                vida_plus_results["swarm"]["global_coherence"] = G
                print(f"   🌐 Global coherence (G): {G:.3f}")
            except Exception as e:
                print(f"   ⚠️  Swarm coherence calculation failed: {e}")
        
        # Apply Life Equation (+) to each challenger
        for challenger in challengers:
            challenger_id = challenger['challenger_id']
            
            if challenger_id not in scoring_results:
                continue
            
            # Extract metrics for Life Equation
            scoring = scoring_results[challenger_id]
            
            # Prepare Life Equation inputs
            ethics_input = {
                "ece": 0.005,  # Would be calculated from ethics
                "rho_bias": 1.02,
                "fairness": 0.9,
                "consent": True,
                "eco_ok": True,
                "thresholds": {}
            }
            
            risk_series = {
                "latency": scoring.get("u_score", 0.5),
                "cost": scoring.get("l_score", 0.5),
                "memory": 0.5,
                "cpu": 0.5
            }
            
            caos_components = (
                scoring.get("c_score", 0.5),  # C
                0.8,  # A (adaptability)
                0.9,  # O (openness)
                scoring.get("s_score", 0.5)   # S (stability)
            )
            
            sr_components = (
                0.9,   # awareness
                True,  # ethics_ok
                0.8,   # autocorr
                0.85   # metacog
            )
            
            linf_weights = {
                "u_score": 0.25,
                "s_score": 0.25,
                "c_score": 0.25,
                "l_score": 0.25,
                "lambda_c": 0.0
            }
            
            linf_metrics = {
                "u_score": scoring.get("u_score", 0.5),
                "s_score": scoring.get("s_score", 0.5),
                "c_score": scoring.get("c_score", 0.5),
                "l_score": scoring.get("l_score", 0.5)
            }
            
            # Apply Life Equation
            try:
                verdict = life_equation(
                    base_alpha=self.config.base_alpha,
                    ethics_input=ethics_input,
                    risk_series=risk_series,
                    caos_components=caos_components,
                    sr_components=sr_components,
                    linf_weights=linf_weights,
                    linf_metrics=linf_metrics,
                    cost=scoring.get("l_score", 0.5),
                    ethical_ok_flag=True,
                    G=G,
                    dL_inf=0.01,  # Would be calculated from previous cycle
                    thresholds=self.config.life_equation_thresholds
                )
                
                vida_plus_results["life_equation"][challenger_id] = {
                    "ok": verdict.ok,
                    "alpha_eff": verdict.alpha_eff,
                    "reasons": verdict.reasons,
                    "metrics": verdict.metrics
                }
                
                print(f"   🧬 {challenger_id}: α_eff={verdict.alpha_eff:.4f}, ok={verdict.ok}")
                
            except Exception as e:
                print(f"   ❌ Life Equation failed for {challenger_id}: {e}")
                vida_plus_results["life_equation"][challenger_id] = {
                    "ok": False,
                    "alpha_eff": 0.0,
                    "error": str(e)
                }
        
        # Apply other Vida+ gates
        if self.config.enable_immunity:
            try:
                # Check immunity for all challengers
                for challenger in challengers:
                    challenger_id = challenger['challenger_id']
                    metrics = scoring_results.get(challenger_id, {})
                    immunity_ok = immunity_guard(metrics, trigger=1.0)
                    vida_plus_results["immunity"][challenger_id] = {"ok": immunity_ok}
            except Exception as e:
                print(f"   ⚠️  Immunity check failed: {e}")
        
        if self.config.enable_darwin_audit:
            try:
                # Apply Darwinian audit
                for challenger in challengers:
                    challenger_id = challenger['challenger_id']
                    metrics = scoring_results.get(challenger_id, {})
                    audit_result = audit_challenger(challenger_id, metrics)
                    vida_plus_results["darwin_audit"][challenger_id] = audit_result.to_dict()
            except Exception as e:
                print(f"   ⚠️  Darwinian audit failed: {e}")
        
        if self.config.enable_zero_consciousness:
            try:
                # Check zero consciousness
                system_state = {"cycle_id": cycle_id, "challengers": len(challengers)}
                consciousness_ok = assert_zero_consciousness(system_state)
                vida_plus_results["zero_consciousness"]["overall"] = {"ok": consciousness_ok}
            except Exception as e:
                print(f"   ⚠️  Zero consciousness check failed: {e}")
        
        return vida_plus_results
    
    def _select_best_challenger(self, challengers: List[Dict[str, Any]], 
                               scoring_results: Dict[str, Any],
                               gate_results: Dict[str, Any],
                               vida_plus_results: Dict[str, Any] = None) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """Select the best challenger based on scores and gates"""
        
        # Filter challengers that passed all gates
        valid_challengers = []
        for challenger in challengers:
            challenger_id = challenger['challenger_id']
            
            # Check traditional gates
            traditional_gates_passed = gate_results.get(challenger_id, {}).get('all_gates_passed', False)
            
            # Check Vida+ gates if enabled
            vida_plus_passed = True
            if self.config.enable_vida_plus and vida_plus_results:
                # Check Life Equation
                life_eq_result = vida_plus_results.get("life_equation", {}).get(challenger_id, {})
                life_eq_passed = life_eq_result.get("ok", False)
                
                # Check immunity
                immunity_result = vida_plus_results.get("immunity", {}).get(challenger_id, {})
                immunity_passed = immunity_result.get("ok", True)
                
                # Check zero consciousness
                consciousness_result = vida_plus_results.get("zero_consciousness", {}).get("overall", {})
                consciousness_passed = consciousness_result.get("ok", True)
                
                vida_plus_passed = life_eq_passed and immunity_passed and consciousness_passed
            
            if traditional_gates_passed and vida_plus_passed:
                challenger['linf_score'] = scoring_results[challenger_id]['linf_score']
                
                # Add alpha_eff from Life Equation if available
                if self.config.enable_vida_plus and vida_plus_results:
                    life_eq_result = vida_plus_results.get("life_equation", {}).get(challenger_id, {})
                    challenger['alpha_eff'] = life_eq_result.get("alpha_eff", 0.0)
                
                valid_challengers.append(challenger)
        
        if not valid_challengers:
            return None, "reject", "no_challengers_passed_gates"
        
        # Select challenger with highest alpha_eff (Life Equation) if Vida+ enabled,
        # otherwise use L∞ score
        if self.config.enable_vida_plus:
            best_challenger = max(valid_challengers, key=lambda c: c.get('alpha_eff', 0.0))
            alpha_eff = best_challenger.get('alpha_eff', 0.0)
            
            # Determine decision based on alpha_eff
            if alpha_eff > 0.01:
                decision = "promote"
                reason = f"high_alpha_eff_{alpha_eff:.4f}"
            elif alpha_eff > 0.005:
                decision = "canary"
                reason = f"moderate_alpha_eff_{alpha_eff:.4f}"
            else:
                decision = "reject"
                reason = f"low_alpha_eff_{alpha_eff:.4f}"
        else:
            # Traditional selection based on L∞ score
            best_challenger = max(valid_challengers, key=lambda c: c['linf_score'])
            linf_score = best_challenger['linf_score']
            
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
    
    async def _deploy_challenger(self, challenger: Dict[str, Any]) -> bool:
        """Deploy challenger using league orchestrator"""
        try:
            success = await run_full_deployment_cycle(self.league, challenger['config'])
            return success
        except Exception as e:
            print(f"   ❌ Deployment failed: {e}")
            return False
    
    def _extract_cycle_metrics(self, evaluation_results: Dict[str, Any], 
                              scoring_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics for tuner update"""
        if not evaluation_results or not scoring_results:
            return {}
        
        # Get metrics from best performer
        best_eval = max(evaluation_results.values(), 
                       key=lambda x: x.get('overall_score', 0))
        
        return {
            'linf_score': best_eval.get('overall_score', 0),
            'U_score': best_eval['aggregate_scores']['U']['mean'],
            'S_score': best_eval['aggregate_scores']['S']['mean'],
            'C_score': best_eval['aggregate_scores']['C']['mean'],
            'L_score': best_eval['aggregate_scores']['L']['mean'],
            'caos_phi': 0.5,  # Would extract from scoring results
            'cost_over_budget': False,  # Would check actual budget
            'recent_promotion_rate': 0.1,  # Would track from history
            'ethics_passed': True
        }
    
    def _estimate_cycle_cost(self, challengers: List[Dict[str, Any]], 
                           evaluation_results: Dict[str, Any]) -> float:
        """Estimate total cost of the cycle"""
        # Simple estimation based on number of challengers and evaluations
        base_cost_per_challenger = 0.01  # $0.01 per challenger
        evaluation_cost = len(challengers) * self.config.max_tasks_per_metric * 0.001
        
        return base_cost_per_challenger * len(challengers) + evaluation_cost
    
    def _compute_evidence_hash(self, cycle_id: str, challengers: List[Dict[str, Any]], 
                              evaluation_results: Dict[str, Any]) -> str:
        """Compute evidence hash for the cycle"""
        evidence_data = {
            'cycle_id': cycle_id,
            'challenger_hashes': [c.get('config_hash', '') for c in challengers],
            'evaluation_summary': {
                cid: result.get('overall_score', 0) 
                for cid, result in evaluation_results.items()
            }
        }
        
        import hashlib
        evidence_str = json.dumps(evidence_data, sort_keys=True)
        return hashlib.sha256(evidence_str.encode()).hexdigest()
    
    def _record_cycle_result(self, result: CycleResult):
        """Record cycle result in WORM ledger"""
        try:
            record_data = {
                'event_type': 'EVOLUTION_CYCLE',
                'cycle_id': result.cycle_id,
                'timestamp': result.timestamp,
                'decision': result.decision,
                'decision_reason': result.decision_reason,
                'n_challengers': len(result.challengers),
                'best_challenger_id': result.best_challenger['challenger_id'] if result.best_challenger else None,
                'duration_s': result.total_duration_s,
                'cost_usd': result.cost_usd,
                'evidence_hash': result.evidence_hash
            }
            
            self.ledger.record(record_data)
            print(f"   📝 Recorded cycle result in WORM ledger")
            
        except Exception as e:
            print(f"   ⚠️  Failed to record in WORM ledger: {e}")


# Utility functions
async def run_evolution_cycles(n_cycles: int = 5, 
                             config: EvolutionConfig = None) -> List[CycleResult]:
    """Run multiple evolution cycles"""
    runner = EvolutionRunner(config)
    results = []
    
    for i in range(n_cycles):
        print(f"\n🔄 Running cycle {i+1}/{n_cycles}")
        try:
            result = await runner.evolve_one_cycle()
            results.append(result)
        except Exception as e:
            print(f"❌ Cycle {i+1} failed: {e}")
            break
    
    return results


# Example usage
if __name__ == "__main__":
    async def demo():
        config = EvolutionConfig(
            n_challengers=3,
            budget_minutes=5,
            dry_run=True,
            max_tasks_per_metric=2
        )
        
        results = await run_evolution_cycles(2, config)
        
        print(f"\n📊 Completed {len(results)} cycles")
        for result in results:
            print(f"  {result.cycle_id}: {result.decision} ({result.decision_reason})")
    
    asyncio.run(demo())
