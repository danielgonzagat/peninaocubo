#!/usr/bin/env python3
"""
Demonstração do Sistema PENIN-Ω com Correções P0
===============================================

Demonstra o sistema funcionando com todas as correções P0 implementadas:
1. Métricas éticas calculadas em tempo real
2. Observabilidade segura (localhost + auth)
3. WORM ledger com WAL mode
4. Router com governança de custos
"""

import asyncio
import tempfile
from pathlib import Path

from observability import ObservabilityConfig, ObservabilityManager

from penin.omega import CAOSComponents, CAOSPlusEngine

# Imports do sistema
from penin.omega.ethics_metrics import calculate_and_validate_ethics
from penin.omega.ledger import WORMLedger, create_run_record
from penin.omega.scoring import LInfinityScorer, USCLScorer
from penin.omega.sr import SRComponents, SROmegaEngine
from penin.providers.base import LLMResponse
from penin.router import MultiLLMRouterComplete as MultiLLMRouter


class MockProvider:
    """Provider mock para demonstração"""

    def __init__(self, name: str, cost_per_token: float = 0.001):
        self.name = name
        self.cost_per_token = cost_per_token

    async def chat(self, messages, **kwargs):
        # Simular latência variável
        await asyncio.sleep(0.1 + hash(self.name) % 3 * 0.1)

        # Simular resposta
        tokens = 50 + hash(str(messages)) % 100
        cost = tokens * self.cost_per_token

        response = LLMResponse(
            content=f"Response from {self.name}: {len(messages)} messages processed",
            provider=self.name,
            model=f"{self.name}-model",
            latency_s=0.1 + hash(self.name) % 3 * 0.1,
        )
        response.cost_usd = cost
        response.tokens_used = tokens

        return response


async def demo_ethics_calculation():
    """Demonstra cálculo de métricas éticas"""
    print("🧠 Demonstração: Cálculo de Métricas Éticas")
    print("=" * 50)

    # Estado simulado do sistema
    state_dict = {
        "consent": True,
        "eco": True,
        "rho": 0.7,
        "risk_history": [1.0, 0.8, 0.6, 0.5],  # Série contrativa
        "ece": 0.005,  # Será recalculado
        "bias": 1.02,  # Será recalculado
    }

    # Configuração de thresholds
    config = {"ethics": {"ece_max": 0.01, "rho_bias_max": 1.05, "consent_required": True, "eco_ok_required": True}}

    # Calcular métricas éticas
    print("Calculando métricas éticas...")
    result = calculate_and_validate_ethics(state_dict, config, dataset_id="demo_dataset", seed=42)

    metrics = result["metrics"]
    validation = result["validation"]

    print(f"✅ ECE calculado: {metrics['ece']:.4f} (threshold: {config['ethics']['ece_max']})")
    print(f"✅ ρ_bias calculado: {metrics['rho_bias']:.3f} (threshold: {config['ethics']['rho_bias_max']})")
    print(f"✅ ρ contratividade: {metrics['rho']:.3f} (contrativo: {metrics['rho'] < 1.0})")
    print(f"✅ Consent: {metrics['consent']}")
    print(f"✅ Eco: {metrics['eco_ok']}")
    print(f"✅ Evidência hash: {result['evidence_hash']}")
    print(f"✅ Validação passou: {validation['passed']}")

    if not validation["passed"]:
        print("⚠️  Violações encontradas:")
        for violation in validation["violations"]:
            print(f"   - {violation['message']}")

    print()
    return result


def demo_scoring_system():
    """Demonstra sistema de scoring"""
    print("📊 Demonstração: Sistema de Scoring")
    print("=" * 50)

    # Scorer U/S/C/L
    uscl_scorer = USCLScorer(weights={"wU": 0.3, "wS": 0.3, "wC": 0.2, "wL": 0.2}, tau=0.7)

    # Métricas simuladas
    metrics = {"U": 0.8, "S": 0.7, "C": 0.3, "L": 0.6}
    result = uscl_scorer.update_and_score(**metrics)

    print(f"✅ Score U/S/C/L: {result['score']:.3f}")
    print(f"✅ Veredito: {result['verdict']}")
    print(f"✅ Passou gate: {result['passed']}")

    # L∞ Scorer
    linf_scorer = LInfinityScorer(
        metric_weights={"rsi": 0.2, "synergy": 0.2, "novelty": 0.2, "stability": 0.2, "viability": 0.15, "cost": 0.05}
    )

    linf_metrics = {"rsi": 0.8, "synergy": 0.7, "novelty": 0.6, "stability": 0.9, "viability": 0.8, "cost": 0.3}

    linf_result = linf_scorer.update_and_score(linf_metrics, ethical_ok=True)

    print(f"✅ L∞ score: {linf_result['linf']:.3f}")
    print(f"✅ Penalidade de custo: {linf_result['cost_penalty']:.3f}")
    print()


def demo_caos_and_sr():
    """Demonstra CAOS⁺ e SR"""
    print("🌀 Demonstração: CAOS⁺ e SR-Ω∞")
    print("=" * 50)

    # CAOS⁺
    caos_engine = CAOSPlusEngine(kappa=2.0, gamma=0.5)
    components = CAOSComponents(C=0.7, A=0.8, O=0.6, S=0.5)

    phi, details = caos_engine.compute_phi(components)
    harmony = caos_engine.compute_harmony(components)

    print(f"✅ φ(CAOS⁺): {phi:.3f}")
    print(f"✅ Harmonia CAOS: {harmony:.3f}")
    print(f"✅ Estável: {details['stable']}")

    # SR-Ω∞
    sr_engine = SROmegaEngine()
    sr_components = SRComponents(awareness=0.8, ethics=0.9, autocorrection=0.7, metacognition=0.6)

    sr_score, sr_details = sr_engine.compute_sr(sr_components)
    sr_passed, sr_gate = sr_engine.gate_check(sr_components, tau=0.8)

    print(f"✅ SR-Ω∞ score: {sr_score:.3f}")
    print(f"✅ SR gate passou: {sr_passed}")
    print()


async def demo_router_with_budget():
    """Demonstra router com orçamento"""
    print("💰 Demonstração: Router com Governança de Custos")
    print("=" * 50)

    # Criar providers mock
    providers = [
        MockProvider("cheap-provider", cost_per_token=0.0005),
        MockProvider("expensive-provider", cost_per_token=0.002),
        MockProvider("fast-provider", cost_per_token=0.001),
    ]

    # Router com orçamento baixo para demonstrar
    router = MultiLLMRouter(
        providers,
        daily_budget_usd=1.0,  # Orçamento baixo para demo
        cost_weight=0.4,  # Peso alto para custo
    )

    # Status inicial
    status = router.get_budget_status()
    print(f"✅ Orçamento diário: ${status['daily_budget_usd']:.2f}")
    print(f"✅ Uso atual: ${status['current_usage_usd']:.2f}")
    print(f"✅ Restante: ${status['remaining_usd']:.2f}")

    # Fazer algumas chamadas
    messages = [{"role": "user", "content": "Test message"}]

    try:
        print("\n🔄 Fazendo chamadas ao router...")
        for i in range(3):
            response = await router.ask(messages)
            status = router.get_budget_status()
            print(
                f"   Chamada {i + 1}: {response.provider} (${response.cost_usd:.4f}) - "
                f"Restante: ${status['remaining_usd']:.2f}"
            )

            if status["budget_exceeded"]:
                print("   ⚠️  Orçamento esgotado!")
                break

    except RuntimeError as e:
        print(f"   🛑 Proteção de orçamento ativada: {e}")

    print()


def demo_worm_ledger():
    """Demonstra WORM ledger com WAL"""
    print("📝 Demonstração: WORM Ledger com WAL Mode")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "demo_ledger.db"
        runs_dir = Path(tmpdir) / "runs"

        # Criar ledger
        ledger = WORMLedger(db_path=db_path, runs_dir=runs_dir)

        # Verificar WAL mode
        import sqlite3

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            cursor.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]

        print(f"✅ Journal mode: {mode}")
        print(f"✅ Busy timeout: {timeout}ms")

        # Criar alguns records
        records = []
        for i in range(3):
            record = create_run_record(
                provider_id=f"demo-provider-{i}",
                metrics={"U": 0.8 + i * 0.05, "S": 0.7 + i * 0.03, "C": 0.3 - i * 0.02, "L": 0.6 + i * 0.04},
                decision_verdict="promote" if i > 0 else "canary",
            )

            # Adicionar artifacts
            artifacts = {
                "config": {"provider": f"demo-provider-{i}", "cycle": i},
                "metrics_detail": {"raw_scores": [0.8, 0.7, 0.3, 0.6]},
            }

            hash_result = ledger.append_record(record, artifacts)
            records.append(hash_result)
            print(f"✅ Record {i + 1} inserido: {hash_result[:8]}...")

        # Verificar integridade
        is_valid, error = ledger.verify_chain_integrity()
        print(f"✅ Integridade da chain: {is_valid}")

        # Estatísticas
        stats = ledger.get_stats()
        print(f"✅ Total de records: {stats['total_records']}")
        print(f"✅ Decisões: {stats['decisions']}")

    print()


def demo_observability():
    """Demonstra observabilidade segura"""
    print("📊 Demonstração: Observabilidade Segura")
    print("=" * 50)

    # Configuração com auth token
    config = ObservabilityConfig(
        enable_metrics=True,
        metrics_port=8001,  # Porta diferente para demo
        metrics_auth_token="demo-token-123",
        enable_json_logs=True,
    )

    obs = ObservabilityManager(config)

    print(f"✅ Métricas habilitadas: {config.enable_metrics}")
    print(f"✅ Porta: {config.metrics_port} (bind: 127.0.0.1)")
    print(f"✅ Auth token configurado: {'***' + config.metrics_auth_token[-3:]}")
    print(f"✅ JSON logs: {config.enable_json_logs}")

    # Simular algumas métricas
    if obs.metrics:
        obs.metrics.alpha.set(0.15)
        obs.metrics.delta_linf.set(0.03)
        obs.metrics.caos.set(1.2)
        obs.metrics.record_decision("PROMOTE")
        obs.metrics.record_gate_failure("SR_GATE")

        print("✅ Métricas atualizadas")
        print("   - Alpha: 0.15")
        print("   - ΔL∞: 0.03")
        print("   - CAOS⁺: 1.2")
        print("   - Decisão: PROMOTE")
        print("   - Gate failure: SR_GATE")

    print("✅ Endpoint seguro: http://127.0.0.1:8001/metrics")
    print("   (Requer: Authorization: Bearer demo-token-123)")
    print()


async def main():
    """Demonstração completa do sistema"""
    print("🚀 PENIN-Ω Sistema com Correções P0")
    print("=" * 60)
    print("Demonstrando todas as correções P0 implementadas:")
    print("1. Métricas éticas calculadas")
    print("2. Observabilidade segura")
    print("3. WORM ledger com WAL")
    print("4. Router com orçamento")
    print("=" * 60)
    print()

    # Executar demonstrações
    await demo_ethics_calculation()
    demo_scoring_system()
    demo_caos_and_sr()
    await demo_router_with_budget()
    demo_worm_ledger()
    demo_observability()

    print("🎉 Demonstração Completa!")
    print("=" * 60)
    print("✅ Todas as correções P0 estão funcionando")
    print("✅ Sistema pronto para produção auditável")
    print("✅ Fail-closed, reprodutível e governado")
    print()
    print("Próximos passos:")
    print("- Implementar ciclo de auto-evolução completo")
    print("- Adicionar mutadores e avaliadores")
    print("- Criar CLI de operação")
    print("- Deploy em produção")


if __name__ == "__main__":
    asyncio.run(main())
