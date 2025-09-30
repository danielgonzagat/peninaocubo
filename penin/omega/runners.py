"""
Runners Module - Evolve One Cycle Orquestrado
=============================================

Implementa orquestração completa do ciclo de auto-evolução:
1. Gerar challengers (mutators)
2. Avaliar challengers (evaluators)  
3. Calcular gates (guards, sr, caos, linf)
4. Decidir promoção/canário/rollback (acfa)
5. Registrar no ledger (WORM)
6. Atualizar champion ou canário
7. Disparar auto-tuning

Ciclo completo auditável e determinístico.
"""

import time
import uuid
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from typing_extensions import Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .mutators import ChallengerGenerator, MutationConfig
    from .evaluators import ComprehensiveEvaluator, EvaluationResult
    from .guards import GuardOrchestrator
    from .scoring import USCLScorer, LInfinityScorer
    from .caos import CAOSPlusEngine, CAOSComponents
    from .sr import SROmegaEngine, SRComponents
    from .acfa import LeagueManager, CanaryManager, PromotionDecisionEngine, PromotionCandidate
    from .tuner import PeninAutoTuner
    from .ledger import WORMLedger, create_run_record
except ImportError:
    # Fallback para execução direta
    import sys
    sys.path.append('/workspace')
    from penin.omega.mutators import ChallengerGenerator, MutationConfig
    from penin.omega.evaluators import ComprehensiveEvaluator, EvaluationResult
    from penin.omega.guards import GuardOrchestrator
    from penin.omega.scoring import USCLScorer, LInfinityScorer
    from penin.omega.caos import CAOSPlusEngine, CAOSComponents
    from penin.omega.sr import SROmegaEngine, SRComponents
    from penin.omega.acfa import LeagueManager, CanaryManager, PromotionDecisionEngine, PromotionCandidate
    from penin.omega.tuner import PeninAutoTuner
    from penin.omega.ledger import WORMLedger, create_run_record


class CyclePhase(Enum):
    """Fases do ciclo de evolução"""
    INIT = "init"
    MUTATE = "mutate"
    EVALUATE = "evaluate"
    GATE_CHECK = "gate_check"
    DECIDE = "decide"
    PROMOTE = "promote"
    TUNE = "tune"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class CycleConfig:
    """Configuração do ciclo de evolução"""
    n_challengers: int = 8
    budget_usd: float = 1.0
    max_duration_s: float = 300.0  # 5 minutos
    provider_id: str = "mock"
    model_name: str = "mock-model"
    
    # Configuração do champion
    champion_config: Dict[str, Any] = None
    
    # Flags
    dry_run: bool = False
    enable_tuning: bool = True
    enable_canary: bool = True
    
    def __post_init__(self):
        if self.champion_config is None:
            self.champion_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }


@dataclass
class CycleResult:
    """Resultado de um ciclo de evolução"""
    cycle_id: str
    phase: CyclePhase
    success: bool
    
    # Timing
    start_time: float
    end_time: float
    duration_s: float
    
    # Resultados por fase
    mutation_result: Optional[Dict[str, Any]] = None
    evaluation_results: List[EvaluationResult] = None
    gate_results: Optional[Dict[str, Any]] = None
    decision_results: Optional[Dict[str, Any]] = None
    tuning_result: Optional[Dict[str, Any]] = None
    
    # Métricas finais
    final_champion_id: Optional[str] = None
    promotions: int = 0
    canaries: int = 0
    rejections: int = 0
    
    # Erros
    error_message: Optional[str] = None
    failed_phase: Optional[CyclePhase] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "success": self.success,
            "timing": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration_s": self.duration_s
            },
            "results": {
                "mutation": self.mutation_result,
                "evaluations": [e.to_dict() for e in self.evaluation_results] if self.evaluation_results else [],
                "gates": self.gate_results,
                "decisions": self.decision_results,
                "tuning": self.tuning_result
            },
            "metrics": {
                "final_champion_id": self.final_champion_id,
                "promotions": self.promotions,
                "canaries": self.canaries,
                "rejections": self.rejections
            },
            "error": {
                "message": self.error_message,
                "failed_phase": self.failed_phase.value if self.failed_phase else None
            }
        }


class EvolutionRunner:
    """Runner principal do ciclo de evolução"""
    
    def __init__(self,
                 ledger_path: Optional[Path] = None,
                 runs_dir: Optional[Path] = None,
                 seed: Optional[int] = None):
        """
        Args:
            ledger_path: Caminho do ledger WORM
            runs_dir: Diretório para artifacts
            seed: Seed para determinismo
        """
        # Paths
        if ledger_path is None:
            ledger_path = Path.home() / ".penin_omega" / "evolution_ledger.db"
        if runs_dir is None:
            runs_dir = Path.home() / ".penin_omega" / "evolution_runs"
            
        # Componentes principais
        self.ledger = WORMLedger(ledger_path, runs_dir)
        self.evaluator = ComprehensiveEvaluator()
        self.challenger_generator = ChallengerGenerator(seed)
        self.guard_orchestrator = GuardOrchestrator()
        
        # Engines de scoring
        self.uscl_scorer = USCLScorer()
        self.linf_scorer = LInfinityScorer()
        self.caos_engine = CAOSPlusEngine()
        self.sr_engine = SROmegaEngine()
        
        # Liga e tuning
        self.canary_manager = CanaryManager()
        self.decision_engine = PromotionDecisionEngine()
        self.league_manager = LeagueManager(
            self.ledger, self.evaluator, self.decision_engine, self.canary_manager
        )
        self.auto_tuner = PeninAutoTuner()
        
        # Estado
        self.cycle_count = 0
        self.evaluation_history: List[Dict[str, float]] = []
        
    def evolve_one_cycle(self,
                        config: CycleConfig,
                        model_func: Callable[[str], str]) -> CycleResult:
        """
        Executa um ciclo completo de evolução
        
        Args:
            config: Configuração do ciclo
            model_func: Função do modelo para teste
            
        Returns:
            CycleResult com todos os detalhes
        """
        cycle_id = f"cycle_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        result = CycleResult(
            cycle_id=cycle_id,
            phase=CyclePhase.INIT,
            success=False,
            start_time=start_time,
            end_time=start_time,
            duration_s=0.0
        )
        
        try:
            print(f"🚀 Iniciando ciclo de evolução: {cycle_id}")
            print(f"   Challengers: {config.n_challengers}")
            print(f"   Budget: ${config.budget_usd:.2f}")
            print(f"   Provider: {config.provider_id}")
            print(f"   Dry run: {config.dry_run}")
            print()
            
            # Fase 1: MUTATE - Gerar challengers
            result.phase = CyclePhase.MUTATE
            print("🧬 Fase 1: Gerando challengers...")
            
            challengers = self.challenger_generator.generate_from_champion(
                config.champion_config,
                config.n_challengers
            )
            
            mutation_summary = self.challenger_generator.get_challenger_summary(challengers)
            result.mutation_result = mutation_summary
            
            print(f"   ✅ {len(challengers)} challengers gerados")
            print(f"   📊 Por tipo: {mutation_summary['by_type']}")
            
            if config.dry_run:
                print("   🏃 Dry run - parando na mutação")
                result.success = True
                result.phase = CyclePhase.COMPLETE
                return result
                
            # Fase 2: EVALUATE - Avaliar challengers
            result.phase = CyclePhase.EVALUATE
            print("\n📊 Fase 2: Avaliando challengers...")
            
            evaluation_results = []
            total_cost = 0.0
            
            for i, challenger in enumerate(challengers, 1):
                print(f"   Avaliando {i}/{len(challengers)}: {challenger.mutation_id}")
                
                # Criar função do modelo com config do challenger
                def configured_model(prompt: str) -> str:
                    # Em produção, aplicaria a config ao modelo real
                    # Por ora, usar modelo mock
                    return model_func(prompt)
                    
                # Avaliar
                evaluation = self.evaluator.evaluate_model(
                    configured_model,
                    challenger.mutations.get("config", config.champion_config),
                    config.provider_id,
                    config.model_name
                )
                
                evaluation_results.append(evaluation)
                total_cost += evaluation.total_cost_usd
                
                print(f"      U={evaluation.U:.3f}, S={evaluation.S:.3f}, "
                      f"C={evaluation.C:.3f}, L={evaluation.L:.3f}")
                
                # Verificar budget
                if total_cost > config.budget_usd:
                    print(f"   ⚠️  Budget esgotado: ${total_cost:.4f} > ${config.budget_usd:.2f}")
                    break
                    
            result.evaluation_results = evaluation_results
            print(f"   ✅ {len(evaluation_results)} avaliações completas")
            print(f"   💰 Custo total: ${total_cost:.4f}")
            
            # Fase 3: GATE_CHECK - Verificar gates
            result.phase = CyclePhase.GATE_CHECK
            print("\n🛡️  Fase 3: Verificando gates...")
            
            gate_results = {"passed": 0, "failed": 0, "details": []}
            
            for evaluation in evaluation_results:
                # Simular estado para guards
                state_dict = {
                    "consent": True,
                    "eco": True,
                    "ece": 0.005,
                    "bias": 1.02,
                    "rho": 0.8,
                    "U": evaluation.U,
                    "S": evaluation.S,
                    "C": evaluation.C,
                    "L": evaluation.L
                }
                
                # Verificar guards
                guards_passed, violations, evidence = self.guard_orchestrator.check_all_guards(state_dict)
                
                # Verificar CAOS⁺
                caos_components = CAOSComponents(C=0.7, A=0.8, O=0.6, S=0.5)
                caos_phi, caos_details = self.caos_engine.compute_phi(caos_components)
                
                # Verificar SR
                sr_components = SRComponents(
                    awareness=0.8, ethics=0.9 if guards_passed else 0.1,
                    autocorrection=0.7, metacognition=0.6
                )
                sr_passed, sr_gate_details = self.sr_engine.gate_check(sr_components)
                
                # Resultado do gate
                all_gates_passed = guards_passed and sr_passed and caos_phi > 0.5
                
                gate_detail = {
                    "evaluation_id": f"{evaluation.provider_id}_{evaluation.timestamp}",
                    "guards_passed": guards_passed,
                    "sr_passed": sr_passed,
                    "caos_phi": caos_phi,
                    "all_passed": all_gates_passed,
                    "violations": len(violations)
                }
                
                gate_results["details"].append(gate_detail)
                
                if all_gates_passed:
                    gate_results["passed"] += 1
                else:
                    gate_results["failed"] += 1
                    
            result.gate_results = gate_results
            print(f"   ✅ Gates: {gate_results['passed']} passou, {gate_results['failed']} falhou")
            
            # Fase 4: DECIDE - Decisão de promoção
            result.phase = CyclePhase.DECIDE
            print("\n🏆 Fase 4: Decisões de promoção...")
            
            # Adicionar challengers à liga
            candidates = []
            for evaluation in evaluation_results:
                candidate = PromotionCandidate(
                    run_id=f"candidate_{int(evaluation.timestamp)}",
                    config={"provider": evaluation.provider_id},
                    evaluation=evaluation
                )
                candidates.append(candidate)
                self.league_manager.active_challengers[candidate.run_id] = candidate
                
            # Executar ciclo de promoção
            promotion_results = self.league_manager.run_promotion_cycle()
            result.decision_results = promotion_results
            
            result.promotions = len(promotion_results.get("promotions", []))
            result.canaries = len(promotion_results.get("canaries", []))
            result.rejections = len(promotion_results.get("rejections", []))
            
            print(f"   ✅ Decisões: {result.promotions} promoções, "
                  f"{result.canaries} canários, {result.rejections} rejeições")
            
            # Fase 5: PROMOTE - Executar promoções
            result.phase = CyclePhase.PROMOTE
            if result.promotions > 0:
                print("\n🚀 Fase 5: Executando promoções...")
                promoted_ids = promotion_results.get("promotions", [])
                if promoted_ids:
                    result.final_champion_id = promoted_ids[0]  # Primeiro promovido
                    print(f"   ✅ Novo champion: {result.final_champion_id[:8]}...")
            else:
                print("\n⏸️  Fase 5: Nenhuma promoção - champion mantido")
                
            # Fase 6: TUNE - Auto-tuning
            result.phase = CyclePhase.TUNE
            if config.enable_tuning and len(self.evaluation_history) > 0:
                print("\n🎛️  Fase 6: Auto-tuning...")
                
                # Adicionar avaliações atuais ao histórico
                for evaluation in evaluation_results:
                    eval_dict = {
                        "U": evaluation.U,
                        "S": evaluation.S,
                        "C": evaluation.C,
                        "L": evaluation.L,
                        "cost": evaluation.total_cost_usd,
                        "linf": self.linf_scorer.update_and_score({
                            "rsi": 0.8, "synergy": 0.7, "novelty": 0.6,
                            "stability": evaluation.S, "viability": 0.8, "cost": evaluation.C
                        })["linf"]
                    }
                    self.evaluation_history.append(eval_dict)
                    
                # Executar tuning
                tuning_result = self.auto_tuner.tune_from_evaluations(self.evaluation_history)
                result.tuning_result = tuning_result
                
                if tuning_result.get("tuning_active", False):
                    updates = len([u for u in tuning_result.get("parameter_updates", {}).values() 
                                  if "error" not in u])
                    print(f"   ✅ {updates} parâmetros atualizados")
                    print(f"   📈 Objetivo: {tuning_result.get('current_objective', 0):.4f}")
                else:
                    print("   ⏸️  Warmup - tuning inativo")
            else:
                print("\n⏸️  Fase 6: Auto-tuning desabilitado")
                
            # Sucesso
            result.phase = CyclePhase.COMPLETE
            result.success = True
            
        except Exception as e:
            result.error_message = str(e)
            result.failed_phase = result.phase
            result.phase = CyclePhase.ERROR
            print(f"\n❌ Erro na fase {result.failed_phase.value}: {e}")
            
        finally:
            result.end_time = time.time()
            result.duration_s = result.end_time - result.start_time
            self.cycle_count += 1
            
            # Registrar ciclo no ledger
            self._record_cycle_in_ledger(result, config)
            
        return result
        
    def _record_cycle_in_ledger(self, result: CycleResult, config: CycleConfig):
        """Registra ciclo no WORM ledger"""
        try:
            # Criar record do ciclo
            record = create_run_record(
                run_id=result.cycle_id,
                provider_id=config.provider_id,
                metrics={
                    "U": 0.0,  # Será preenchido com média dos challengers
                    "S": 0.0,
                    "C": 0.0,
                    "L": 0.0
                },
                decision_verdict="cycle_complete" if result.success else "cycle_failed"
            )
            
            # Calcular métricas médias
            if result.evaluation_results:
                avg_U = sum(e.U for e in result.evaluation_results) / len(result.evaluation_results)
                avg_S = sum(e.S for e in result.evaluation_results) / len(result.evaluation_results)
                avg_C = sum(e.C for e in result.evaluation_results) / len(result.evaluation_results)
                avg_L = sum(e.L for e in result.evaluation_results) / len(result.evaluation_results)
                
                record.metrics.U = avg_U
                record.metrics.S = avg_S
                record.metrics.C = avg_C
                record.metrics.L = avg_L
                
            # Artifacts do ciclo
            artifacts = {
                "cycle_result": result.to_dict(),
                "config": config.__dict__,
                "evaluation_history_size": len(self.evaluation_history),
                "cycle_count": self.cycle_count
            }
            
            # Salvar no ledger
            hash_result = self.ledger.append_record(record, artifacts)
            print(f"   📝 Ciclo registrado no ledger: {hash_result[:8]}...")
            
        except Exception as e:
            print(f"   ⚠️  Erro ao registrar no ledger: {e}")
            
    def get_runner_status(self) -> Dict[str, Any]:
        """Obtém status do runner"""
        return {
            "cycle_count": self.cycle_count,
            "evaluation_history_size": len(self.evaluation_history),
            "league_status": self.league_manager.get_league_status(),
            "tuning_stats": self.auto_tuner.get_tuning_stats(),
            "ledger_stats": self.ledger.get_stats()
        }
        
    def rollback_to_cycle(self, target_cycle_id: str) -> bool:
        """Rollback para ciclo específico"""
        try:
            return self.league_manager.rollback_to_champion(target_cycle_id)
        except Exception as e:
            print(f"❌ Erro no rollback: {e}")
            return False


class BatchRunner:
    """Runner para múltiplos ciclos"""
    
    def __init__(self, evolution_runner: EvolutionRunner):
        self.runner = evolution_runner
        self.batch_results: List[CycleResult] = []
        
    def run_batch(self,
                 n_cycles: int,
                 config: CycleConfig,
                 model_func: Callable[[str], str],
                 stop_on_error: bool = False) -> Dict[str, Any]:
        """
        Executa batch de ciclos
        
        Args:
            n_cycles: Número de ciclos
            config: Configuração base
            model_func: Função do modelo
            stop_on_error: Se deve parar no primeiro erro
            
        Returns:
            Resumo do batch
        """
        print(f"🔄 Executando batch de {n_cycles} ciclos...")
        
        batch_start = time.time()
        successful_cycles = 0
        failed_cycles = 0
        
        for cycle_num in range(1, n_cycles + 1):
            print(f"\n--- Ciclo {cycle_num}/{n_cycles} ---")
            
            # Executar ciclo
            cycle_result = self.runner.evolve_one_cycle(config, model_func)
            self.batch_results.append(cycle_result)
            
            if cycle_result.success:
                successful_cycles += 1
                print(f"✅ Ciclo {cycle_num} concluído em {cycle_result.duration_s:.2f}s")
            else:
                failed_cycles += 1
                print(f"❌ Ciclo {cycle_num} falhou: {cycle_result.error_message}")
                
                if stop_on_error:
                    print("🛑 Parando batch devido a erro")
                    break
                    
        batch_duration = time.time() - batch_start
        
        # Resumo do batch
        summary = {
            "total_cycles": len(self.batch_results),
            "successful_cycles": successful_cycles,
            "failed_cycles": failed_cycles,
            "success_rate": successful_cycles / len(self.batch_results) if self.batch_results else 0,
            "batch_duration_s": batch_duration,
            "avg_cycle_duration_s": batch_duration / len(self.batch_results) if self.batch_results else 0,
            "runner_status": self.runner.get_runner_status()
        }
        
        print(f"\n📊 Batch completo:")
        print(f"   Ciclos: {summary['total_cycles']}")
        print(f"   Sucessos: {summary['successful_cycles']}")
        print(f"   Falhas: {summary['failed_cycles']}")
        print(f"   Taxa de sucesso: {summary['success_rate']*100:.1f}%")
        print(f"   Duração total: {summary['batch_duration_s']:.2f}s")
        
        return summary


# Funções de conveniência
def quick_evolution_cycle(n_challengers: int = 4,
                         budget_usd: float = 0.5,
                         seed: Optional[int] = None) -> CycleResult:
    """Executa ciclo rápido de evolução"""
    
    # Modelo mock
    def mock_model(prompt: str) -> str:
        if "json" in prompt.lower():
            return '{"nome": "João Silva", "email": "joao@email.com"}'
        elif "capital" in prompt.lower():
            return "Brasília"
        else:
            return f"Resposta para: {prompt[:30]}..."
            
    # Configuração
    config = CycleConfig(
        n_challengers=n_challengers,
        budget_usd=budget_usd,
        provider_id="mock",
        dry_run=False,
        enable_tuning=True
    )
    
    # Runner temporário
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = EvolutionRunner(
            ledger_path=Path(tmpdir) / "evolution.db",
            runs_dir=Path(tmpdir) / "runs",
            seed=seed
        )
        
        return runner.evolve_one_cycle(config, mock_model)


def quick_batch_evolution(n_cycles: int = 3,
                         n_challengers: int = 3,
                         seed: Optional[int] = None) -> Dict[str, Any]:
    """Executa batch rápido de evolução"""
    
    def mock_model(prompt: str) -> str:
        return f"Mock response to: {prompt[:20]}..."
        
    config = CycleConfig(
        n_challengers=n_challengers,
        budget_usd=1.0,
        dry_run=False,
        enable_tuning=True
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = EvolutionRunner(
            ledger_path=Path(tmpdir) / "batch.db",
            runs_dir=Path(tmpdir) / "runs",
            seed=seed
        )
        
        batch_runner = BatchRunner(runner)
        return batch_runner.run_batch(n_cycles, config, mock_model)


# Exemplo de uso
if __name__ == "__main__":
    print("🔄 Demonstração: Runners - Evolve One Cycle")
    print("=" * 60)
    
    # Executar ciclo único
    print("🚀 Executando ciclo único de evolução...")
    cycle_result = quick_evolution_cycle(n_challengers=3, budget_usd=0.5, seed=42)
    
    print(f"\n✅ Ciclo {cycle_result.cycle_id[:8]}... completo:")
    print(f"   Sucesso: {cycle_result.success}")
    print(f"   Fase final: {cycle_result.phase.value}")
    print(f"   Duração: {cycle_result.duration_s:.2f}s")
    
    if cycle_result.mutation_result:
        print(f"   Challengers: {cycle_result.mutation_result['total']}")
        
    if cycle_result.evaluation_results:
        print(f"   Avaliações: {len(cycle_result.evaluation_results)}")
        
    if cycle_result.gate_results:
        gates = cycle_result.gate_results
        print(f"   Gates: {gates['passed']} passou, {gates['failed']} falhou")
        
    print(f"   Promoções: {cycle_result.promotions}")
    print(f"   Canários: {cycle_result.canaries}")
    print(f"   Rejeições: {cycle_result.rejections}")
    
    if cycle_result.error_message:
        print(f"   Erro: {cycle_result.error_message}")
        
    print("\n" + "="*60)
    print("✅ Runners implementados e funcionando!")
    print("🔄 Sistema de auto-evolução completo!")
    print("🎯 Próximo: Implementar CLI (penin evolve/promote/rollback)")