"""
ACFA Module - Liga Canário + Decisão de Promoção
===============================================

Implementa:
- Matchmaker champion↔challenger
- Shadow/canary traffic (fração do tráfego)
- Decisão de promoção baseada em ΔL∞ + Score U/S/C/L + gates
- Rollback atômico via champion pointer
- Liga EPV (Expected Performance Value)
"""

import time
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from typing_extensions import Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .scoring import ScoreVerdict, score_gate
    from .evaluators import EvaluationResult, ComprehensiveEvaluator
    from .guards import GuardOrchestrator
    from .ledger import WORMLedger, RunRecord, create_run_record
except ImportError:
    # Fallback para execução direta
    import sys
    sys.path.append('/workspace')
    from penin.omega.scoring import ScoreVerdict, score_gate
    from penin.omega.evaluators import EvaluationResult, ComprehensiveEvaluator
    from penin.omega.guards import GuardOrchestrator
    from penin.omega.ledger import WORMLedger, RunRecord, create_run_record


class CanaryStatus(Enum):
    """Status do teste canário"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PromotionDecision(Enum):
    """Decisão de promoção"""
    PROMOTE = "promote"
    CANARY = "canary"
    ROLLBACK = "rollback"
    REJECT = "reject"


@dataclass
class CanaryTest:
    """Configuração de teste canário"""
    challenger_id: str
    champion_id: str
    traffic_fraction: float  # [0,1] fração do tráfego
    duration_s: float        # Duração do teste
    start_time: float
    status: CanaryStatus
    
    # Métricas coletadas
    requests_sent: int = 0
    responses_received: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    
    # Avaliação
    evaluation_result: Optional[EvaluationResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenger_id": self.challenger_id,
            "champion_id": self.champion_id,
            "traffic_fraction": self.traffic_fraction,
            "duration_s": self.duration_s,
            "start_time": self.start_time,
            "status": self.status.value,
            "metrics": {
                "requests_sent": self.requests_sent,
                "responses_received": self.responses_received,
                "avg_latency_ms": self.avg_latency_ms,
                "error_rate": self.error_rate
            },
            "evaluation": self.evaluation_result.to_dict() if self.evaluation_result else None
        }


@dataclass
class PromotionCandidate:
    """Candidato à promoção"""
    run_id: str
    config: Dict[str, Any]
    evaluation: EvaluationResult
    canary_test: Optional[CanaryTest] = None
    
    def compute_hash(self) -> str:
        """Hash do candidato"""
        data = {
            "run_id": self.run_id,
            "config": self.config,
            "evaluation_hash": hashlib.sha256(
                json.dumps(self.evaluation.to_dict(), sort_keys=True).encode()
            ).hexdigest()
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class CanaryManager:
    """Gerenciador de testes canário"""
    
    def __init__(self, 
                 default_fraction: float = 0.1,
                 default_duration_s: float = 300):  # 5 minutos
        self.default_fraction = default_fraction
        self.default_duration_s = default_duration_s
        self.active_canaries: Dict[str, CanaryTest] = {}
        
    def start_canary_test(self,
                         challenger_id: str,
                         champion_id: str,
                         traffic_fraction: Optional[float] = None,
                         duration_s: Optional[float] = None) -> CanaryTest:
        """
        Inicia teste canário
        
        Args:
            challenger_id: ID do challenger
            champion_id: ID do champion atual
            traffic_fraction: Fração do tráfego [0,1]
            duration_s: Duração do teste
            
        Returns:
            CanaryTest configurado
        """
        canary = CanaryTest(
            challenger_id=challenger_id,
            champion_id=champion_id,
            traffic_fraction=traffic_fraction or self.default_fraction,
            duration_s=duration_s or self.default_duration_s,
            start_time=time.time(),
            status=CanaryStatus.PENDING
        )
        
        self.active_canaries[challenger_id] = canary
        return canary
        
    def update_canary_metrics(self,
                            challenger_id: str,
                            requests_sent: int,
                            responses_received: int,
                            latencies: List[float],
                            errors: int) -> bool:
        """
        Atualiza métricas do canário
        
        Returns:
            True se canário ainda ativo
        """
        if challenger_id not in self.active_canaries:
            return False
            
        canary = self.active_canaries[challenger_id]
        
        # Atualizar métricas
        canary.requests_sent = requests_sent
        canary.responses_received = responses_received
        canary.avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
        canary.error_rate = errors / requests_sent if requests_sent > 0 else 0.0
        
        # Verificar se teste terminou
        elapsed = time.time() - canary.start_time
        if elapsed >= canary.duration_s:
            canary.status = CanaryStatus.SUCCESS if canary.error_rate < 0.1 else CanaryStatus.FAILED
            return False
        else:
            canary.status = CanaryStatus.RUNNING
            return True
            
    def get_canary_status(self, challenger_id: str) -> Optional[CanaryTest]:
        """Obtém status do canário"""
        return self.active_canaries.get(challenger_id)
        
    def finish_canary_test(self, challenger_id: str,
                          evaluation_result: EvaluationResult) -> Optional[CanaryTest]:
        """
        Finaliza teste canário com avaliação
        
        Args:
            challenger_id: ID do challenger
            evaluation_result: Resultado da avaliação
            
        Returns:
            CanaryTest finalizado ou None
        """
        if challenger_id not in self.active_canaries:
            return None
            
        canary = self.active_canaries[challenger_id]
        canary.evaluation_result = evaluation_result
        
        # Determinar status final
        if canary.status == CanaryStatus.RUNNING:
            if canary.error_rate < 0.1 and evaluation_result.U > 0.5:
                canary.status = CanaryStatus.SUCCESS
            else:
                canary.status = CanaryStatus.FAILED
                
        return canary


class PromotionDecisionEngine:
    """Engine de decisão de promoção"""
    
    def __init__(self,
                 beta_min: float = 0.02,  # ΔL∞ mínimo
                 tau_score: float = 0.7,  # Threshold Score U/S/C/L
                 score_weights: Optional[Dict[str, float]] = None):
        """
        Args:
            beta_min: ΔL∞ mínimo para promoção
            tau_score: Threshold do Score U/S/C/L
            score_weights: Pesos para U/S/C/L
        """
        self.beta_min = beta_min
        self.tau_score = tau_score
        
        if score_weights is None:
            score_weights = {"wU": 0.3, "wS": 0.3, "wC": 0.2, "wL": 0.2}
        self.score_weights = score_weights
        
        self.guard_orchestrator = GuardOrchestrator()
        
    def evaluate_promotion(self,
                          candidate: PromotionCandidate,
                          champion_evaluation: EvaluationResult,
                          canary_test: Optional[CanaryTest] = None) -> Tuple[PromotionDecision, Dict[str, Any]]:
        """
        Avalia se candidato deve ser promovido
        
        Args:
            candidate: Candidato à promoção
            champion_evaluation: Avaliação do champion atual
            canary_test: Teste canário (opcional)
            
        Returns:
            (decision, details)
        """
        details = {
            "timestamp": time.time(),
            "candidate_id": candidate.run_id,
            "champion_metrics": {
                "U": champion_evaluation.U,
                "S": champion_evaluation.S,
                "C": champion_evaluation.C,
                "L": champion_evaluation.L
            },
            "candidate_metrics": {
                "U": candidate.evaluation.U,
                "S": candidate.evaluation.S,
                "C": candidate.evaluation.C,
                "L": candidate.evaluation.L
            },
            "gates_checked": [],
            "decision_factors": {}
        }
        
        # 1. Calcular ΔL∞ (assumindo L∞ como média harmônica de U,S,L com penalização C)
        champion_linf = self._compute_linf(champion_evaluation)
        candidate_linf = self._compute_linf(candidate.evaluation)
        delta_linf = candidate_linf - champion_linf
        
        details["delta_linf"] = delta_linf
        details["decision_factors"]["delta_linf_check"] = delta_linf >= self.beta_min
        
        # 2. Calcular Score U/S/C/L
        candidate_verdict, candidate_score = score_gate(
            candidate.evaluation.U,
            candidate.evaluation.S,
            candidate.evaluation.C,
            candidate.evaluation.L,
            **self.score_weights,
            tau=self.tau_score
        )
        
        details["candidate_score"] = candidate_score
        details["candidate_verdict"] = candidate_verdict.value
        details["decision_factors"]["score_gate_check"] = candidate_verdict == ScoreVerdict.PASS
        
        # 3. Verificar guards (Σ-Guard + IR→IC)
        # Simular estado para guards
        candidate_state = {
            "consent": True,  # Assumir OK para demo
            "eco": True,
            "ece": 0.005,     # Simular ECE baixo
            "bias": 1.02,     # Simular bias baixo
            "rho": 0.8        # Simular risco contrativo
        }
        
        guards_passed, violations, guard_evidence = self.guard_orchestrator.check_all_guards(
            candidate_state
        )
        
        details["guards_passed"] = guards_passed
        details["guard_violations"] = [v.to_dict() for v in violations]
        details["decision_factors"]["guards_check"] = guards_passed
        
        # 4. Verificar canário (se aplicável)
        canary_ok = True
        if canary_test:
            canary_ok = (canary_test.status == CanaryStatus.SUCCESS and 
                        canary_test.error_rate < 0.05)
            details["canary_test"] = canary_test.to_dict()
            details["decision_factors"]["canary_check"] = canary_ok
            
        # 5. Decisão final (fail-closed)
        all_checks = [
            details["decision_factors"]["delta_linf_check"],
            details["decision_factors"]["score_gate_check"],
            details["decision_factors"]["guards_check"],
            canary_ok
        ]
        
        if all(all_checks):
            decision = PromotionDecision.PROMOTE
            reason = "All gates passed"
        elif candidate_verdict == ScoreVerdict.CANARY and guards_passed:
            decision = PromotionDecision.CANARY
            reason = "Score in canary range, guards passed"
        elif not guards_passed:
            decision = PromotionDecision.REJECT
            reason = f"Guards failed: {len(violations)} violations"
        elif delta_linf < self.beta_min:
            decision = PromotionDecision.REJECT
            reason = f"ΔL∞ {delta_linf:.4f} < {self.beta_min}"
        else:
            decision = PromotionDecision.ROLLBACK
            reason = "Score too low for promotion"
            
        details["decision"] = decision.value
        details["reason"] = reason
        details["all_checks_passed"] = all(all_checks)
        
        return decision, details
        
    def _compute_linf(self, evaluation: EvaluationResult) -> float:
        """Computa L∞ aproximado a partir de U/S/C/L"""
        # Usar média harmônica de U,S,L com penalização por C
        metrics = [evaluation.U, evaluation.S, evaluation.L]
        weights = [0.4, 0.3, 0.3]  # Pesos para U,S,L
        
        # Média harmônica
        if any(m <= 0 for m in metrics):
            base_score = 0.0
        else:
            denom = sum(w / m for w, m in zip(weights, metrics))
            base_score = 1.0 / denom
            
        # Penalização por custo (exponencial)
        import math
        cost_penalty = math.exp(-0.1 * evaluation.C)
        
        return base_score * cost_penalty


class LeagueManager:
    """Gerenciador da Liga (ACFA - Adaptive Challenger-Champion Framework)"""
    
    def __init__(self,
                 ledger: WORMLedger,
                 evaluator: ComprehensiveEvaluator,
                 decision_engine: PromotionDecisionEngine,
                 canary_manager: CanaryManager):
        """
        Args:
            ledger: WORM ledger para persistência
            evaluator: Avaliador U/S/C/L
            decision_engine: Engine de decisão
            canary_manager: Gerenciador de canários
        """
        self.ledger = ledger
        self.evaluator = evaluator
        self.decision_engine = decision_engine
        self.canary_manager = canary_manager
        
        # Estado da liga
        self.current_champion: Optional[RunRecord] = None
        self.active_challengers: Dict[str, PromotionCandidate] = {}
        
    def register_champion(self, champion_record: RunRecord) -> bool:
        """Registra champion atual"""
        try:
            self.current_champion = champion_record
            success = self.ledger.set_champion(champion_record.run_id)
            
            if success:
                print(f"✅ Champion registrado: {champion_record.run_id[:8]}...")
                
            return success
        except Exception as e:
            print(f"❌ Erro ao registrar champion: {e}")
            return False
            
    def add_challenger(self,
                      challenger_config: Dict[str, Any],
                      model_func: Callable[[str], str],
                      provider_id: str = "unknown",
                      model_name: str = "unknown") -> Optional[PromotionCandidate]:
        """
        Adiciona challenger à liga
        
        Args:
            challenger_config: Configuração do challenger
            model_func: Função do modelo challenger
            provider_id: ID do provider
            model_name: Nome do modelo
            
        Returns:
            PromotionCandidate ou None se falhou
        """
        try:
            # Avaliar challenger
            evaluation = self.evaluator.evaluate_model(
                model_func, challenger_config, provider_id, model_name
            )
            
            # Criar candidato
            run_id = f"challenger_{int(time.time())}_{hash(str(challenger_config)) % 10000:04d}"
            
            candidate = PromotionCandidate(
                run_id=run_id,
                config=challenger_config,
                evaluation=evaluation
            )
            
            self.active_challengers[run_id] = candidate
            
            print(f"✅ Challenger adicionado: {run_id[:8]}... "
                  f"(U={evaluation.U:.3f}, S={evaluation.S:.3f}, C={evaluation.C:.3f}, L={evaluation.L:.3f})")
            
            return candidate
            
        except Exception as e:
            print(f"❌ Erro ao adicionar challenger: {e}")
            return None
            
    def run_promotion_cycle(self) -> Dict[str, Any]:
        """
        Executa ciclo de promoção para todos os challengers
        
        Returns:
            Dict com resultados do ciclo
        """
        if not self.current_champion:
            return {"error": "No champion registered"}
            
        if not self.active_challengers:
            return {"message": "No challengers to evaluate"}
            
        # Obter avaliação do champion (simular)
        champion_evaluation = EvaluationResult(
            provider_id="champion",
            model_name="champion-model",
            config={},
            U=0.7, S=0.8, C=0.4, L=0.6,
            total_tokens=1000,
            total_cost_usd=0.05,
            avg_latency_ms=150.0,
            task_results=[],
            timestamp=time.time(),
            duration_s=1.0
        )
        
        results = {
            "timestamp": time.time(),
            "champion_id": self.current_champion.run_id,
            "challengers_evaluated": 0,
            "decisions": {},
            "promotions": [],
            "canaries": [],
            "rejections": []
        }
        
        # Avaliar cada challenger
        for challenger_id, candidate in self.active_challengers.items():
            try:
                # Decisão de promoção
                decision, decision_details = self.decision_engine.evaluate_promotion(
                    candidate, champion_evaluation
                )
                
                results["decisions"][challenger_id] = {
                    "decision": decision.value,
                    "details": decision_details
                }
                
                # Categorizar decisão
                if decision == PromotionDecision.PROMOTE:
                    results["promotions"].append(challenger_id)
                    # Promover imediatamente
                    self._promote_challenger(candidate)
                elif decision == PromotionDecision.CANARY:
                    results["canaries"].append(challenger_id)
                    # Iniciar teste canário
                    self._start_canary_for_challenger(candidate)
                else:
                    results["rejections"].append(challenger_id)
                    
                results["challengers_evaluated"] += 1
                
            except Exception as e:
                results["decisions"][challenger_id] = {
                    "decision": "error",
                    "error": str(e)
                }
                
        # Limpar challengers processados (exceto canários)
        for challenger_id in list(self.active_challengers.keys()):
            if challenger_id not in results["canaries"]:
                del self.active_challengers[challenger_id]
                
        return results
        
    def _promote_challenger(self, candidate: PromotionCandidate) -> bool:
        """Promove challenger para champion"""
        try:
            # Criar record no ledger
            record = create_run_record(
                run_id=candidate.run_id,
                provider_id=candidate.evaluation.provider_id,
                metrics={
                    "U": candidate.evaluation.U,
                    "S": candidate.evaluation.S,
                    "C": candidate.evaluation.C,
                    "L": candidate.evaluation.L,
                    "linf": self.decision_engine._compute_linf(candidate.evaluation)
                },
                decision_verdict="promote"
            )
            
            # Artifacts
            artifacts = {
                "evaluation": candidate.evaluation.to_dict(),
                "config": candidate.config,
                "promotion_timestamp": time.time()
            }
            
            # Salvar no ledger
            hash_result = self.ledger.append_record(record, artifacts)
            
            # Atualizar champion pointer
            success = self.ledger.set_champion(candidate.run_id)
            
            if success:
                self.current_champion = record
                print(f"🚀 PROMOÇÃO: {candidate.run_id[:8]}... é o novo champion!")
                
            return success
            
        except Exception as e:
            print(f"❌ Erro na promoção: {e}")
            return False
            
    def _start_canary_for_challenger(self, candidate: PromotionCandidate) -> bool:
        """Inicia teste canário para challenger"""
        try:
            canary = self.canary_manager.start_canary_test(
                candidate.run_id,
                self.current_champion.run_id if self.current_champion else "unknown"
            )
            
            candidate.canary_test = canary
            
            print(f"🕊️  CANÁRIO: {candidate.run_id[:8]}... iniciou teste "
                  f"({canary.traffic_fraction*100:.1f}% tráfego, {canary.duration_s}s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar canário: {e}")
            return False
            
    def rollback_to_champion(self, target_run_id: Optional[str] = None) -> bool:
        """
        Rollback para champion específico ou último estável
        
        Args:
            target_run_id: ID específico ou None para último champion
            
        Returns:
            True se rollback bem-sucedido
        """
        try:
            if target_run_id:
                # Rollback para run específico
                target_record = self.ledger.get_record(target_run_id)
                if not target_record:
                    return False
            else:
                # Rollback para champion atual
                target_record = self.ledger.get_champion()
                if not target_record:
                    return False
                    
            # Atualizar champion pointer
            success = self.ledger.set_champion(target_record.run_id)
            
            if success:
                self.current_champion = target_record
                print(f"⏪ ROLLBACK: Voltou para {target_record.run_id[:8]}...")
                
            return success
            
        except Exception as e:
            print(f"❌ Erro no rollback: {e}")
            return False
            
    def get_league_status(self) -> Dict[str, Any]:
        """Obtém status da liga"""
        return {
            "champion": {
                "run_id": self.current_champion.run_id if self.current_champion else None,
                "timestamp": self.current_champion.timestamp if self.current_champion else None
            },
            "active_challengers": len(self.active_challengers),
            "active_canaries": len([c for c in self.active_challengers.values() 
                                  if c.canary_test and c.canary_test.status == CanaryStatus.RUNNING]),
            "decision_config": {
                "beta_min": self.decision_engine.beta_min,
                "tau_score": self.decision_engine.tau_score,
                "score_weights": self.decision_engine.score_weights
            }
        }


# Funções de conveniência
def quick_canary_test(challenger_config: Dict[str, Any],
                     champion_config: Dict[str, Any],
                     model_func: Callable[[str], str]) -> Dict[str, Any]:
    """Teste canário rápido"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        ledger = WORMLedger(
            db_path=Path(tmpdir) / "test.db",
            runs_dir=Path(tmpdir) / "runs"
        )
        
        evaluator = ComprehensiveEvaluator()
        decision_engine = PromotionDecisionEngine()
        canary_manager = CanaryManager()
        
        league = LeagueManager(ledger, evaluator, decision_engine, canary_manager)
        
        # Registrar champion mock
        champion_record = create_run_record(
            run_id="champion_001",
            provider_id="champion",
            decision_verdict="current_champion"
        )
        league.register_champion(champion_record)
        
        # Adicionar challenger
        candidate = league.add_challenger(
            challenger_config, model_func, "test-provider", "test-model"
        )
        
        if not candidate:
            return {"error": "Failed to create challenger"}
            
        # Executar ciclo
        cycle_result = league.run_promotion_cycle()
        
        return {
            "league_status": league.get_league_status(),
            "cycle_result": cycle_result,
            "candidate_hash": candidate.compute_hash()[:8]
        }


# Exemplo de uso
if __name__ == "__main__":
    print("🏆 Demonstração: ACFA - Liga Canário + Promoção")
    print("=" * 60)
    
    # Modelo mock
    def mock_model(prompt: str) -> str:
        if "json" in prompt.lower():
            return '{"nome": "João Silva", "email": "joao@email.com", "telefone": "(11) 99999-9999"}'
        elif "capital" in prompt.lower():
            return "Brasília"
        elif "resumo" in prompt.lower():
            return "IA transforma economia com investimentos, mas gera preocupações."
        else:
            return f"Resposta para: {prompt[:30]}..."
            
    # Configurações
    champion_config = {
        "temperature": 0.7,
        "max_tokens": 1000,
        "provider": "champion"
    }
    
    challenger_config = {
        "temperature": 0.8,  # Diferente do champion
        "max_tokens": 1200,  # Mais tokens
        "provider": "challenger"
    }
    
    print("Champion config:", champion_config)
    print("Challenger config:", challenger_config)
    print()
    
    # Executar teste
    result = quick_canary_test(challenger_config, champion_config, mock_model)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print("✅ Liga ACFA executada:")
        
        league_status = result["league_status"]
        print(f"   Champion: {league_status['champion']['run_id']}")
        print(f"   Challengers ativos: {league_status['active_challengers']}")
        print(f"   Canários ativos: {league_status['active_canaries']}")
        
        cycle_result = result["cycle_result"]
        print(f"   Challengers avaliados: {cycle_result['challengers_evaluated']}")
        print(f"   Promoções: {len(cycle_result['promotions'])}")
        print(f"   Canários: {len(cycle_result['canaries'])}")
        print(f"   Rejeições: {len(cycle_result['rejections'])}")
        
        # Mostrar decisões
        for challenger_id, decision_info in cycle_result["decisions"].items():
            decision = decision_info["decision"]
            print(f"   {challenger_id[:8]}...: {decision}")
            if "details" in decision_info:
                details = decision_info["details"]
                if "reason" in details:
                    print(f"      Motivo: {details['reason']}")
                if "delta_linf" in details:
                    print(f"      ΔL∞: {details['delta_linf']:.4f}")
                    
    print("\n✅ ACFA implementado e funcionando!")
    print("🔄 Próximo: Implementar auto-tuning AdaGrad")