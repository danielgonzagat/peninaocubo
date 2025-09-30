#!/usr/bin/env python3
"""
Teste Canário PENIN-Ω Vida+
===========================

Executa teste canário completo do sistema integrado.
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any

# Adicionar workspace ao path
sys.path.append("/workspace")

from penin.omega.life_eq import quick_life_check, LifeEquationEngine
from penin.omega.swarm import quick_swarm_test, heartbeat, sample_global_state
from penin.omega.fractal import quick_fractal_test
from penin.omega.caos_kratos import phi_kratos, adaptive_kratos
from penin.omega.neural_chain import add_block, get_chain_head, verify_chain
from penin.omega.checkpoint import save_snapshot, restore_last
from penin.omega.immunity import guard, anomaly_score
from penin.omega.zero_consciousness import spi_proxy, assert_zero_consciousness
from penin.auto_docs import update_readme


def run_canary_test() -> Dict[str, Any]:
    """Executa teste canário completo"""
    print("🐦 PENIN-Ω Vida+ - Teste Canário")
    print("=" * 50)

    canary_start = time.time()
    results = {
        "start_time": canary_start,
        "modules_tested": [],
        "modules_passed": [],
        "modules_failed": [],
        "metrics": {},
        "errors": [],
    }

    # 1. Equação de Vida (+)
    print("\n1️⃣  Testando Equação de Vida (+)...")
    try:
        life_engine = LifeEquationEngine()

        # Teste com parâmetros que devem passar
        passed, alpha_eff = quick_life_check(
            caos_components=(0.8, 0.7, 0.6, 0.9),
            sr_components=(0.85, True, 0.80, 0.82),
            G=0.90,
            dL_inf=0.02,
            ethical_ok=True,
        )

        results["modules_tested"].append("life_equation")
        results["metrics"]["alpha_eff"] = alpha_eff

        if passed and alpha_eff > 0.0:
            results["modules_passed"].append("life_equation")
            print(f"   ✅ Equação de Vida (+): α_eff = {alpha_eff:.6f}")
        else:
            results["modules_failed"].append("life_equation")
            print(f"   ❌ Equação de Vida (+): falhou (α_eff = {alpha_eff})")

    except Exception as e:
        results["modules_failed"].append("life_equation")
        results["errors"].append(f"life_equation: {str(e)}")
        print(f"   ❌ Equação de Vida (+): erro - {e}")

    # 2. Swarm Cognitivo
    print("\n2️⃣  Testando Swarm Cognitivo...")
    try:
        # Enviar alguns heartbeats
        heartbeat("canary-node-1", {"phi": 0.7, "sr": 0.8, "G": 0.9})
        heartbeat("canary-node-2", {"phi": 0.75, "sr": 0.82, "G": 0.88})

        # Obter estado global
        global_state = sample_global_state()

        results["modules_tested"].append("swarm")
        results["metrics"]["global_G"] = global_state.get("global_G", 0.0)
        results["metrics"]["active_nodes"] = global_state.get("active_nodes", 0)

        if global_state.get("active_nodes", 0) > 0:
            results["modules_passed"].append("swarm")
            print(f"   ✅ Swarm: {global_state['active_nodes']} nós ativos, G = {global_state.get('global_G', 0):.3f}")
        else:
            results["modules_failed"].append("swarm")
            print("   ❌ Swarm: nenhum nó ativo")

    except Exception as e:
        results["modules_failed"].append("swarm")
        results["errors"].append(f"swarm: {str(e)}")
        print(f"   ❌ Swarm: erro - {e}")

    # 3. DSL Fractal
    print("\n3️⃣  Testando DSL Fractal...")
    try:
        fractal_report = quick_fractal_test(depth=2, branching=2)

        results["modules_tested"].append("fractal")
        results["metrics"]["fractal_nodes_updated"] = fractal_report.get("nodes_updated", 0)

        if fractal_report.get("success", False):
            results["modules_passed"].append("fractal")
            print(f"   ✅ Fractal: {fractal_report['nodes_updated']} nós atualizados")
        else:
            results["modules_failed"].append("fractal")
            print("   ❌ Fractal: propagação falhou")

    except Exception as e:
        results["modules_failed"].append("fractal")
        results["errors"].append(f"fractal: {str(e)}")
        print(f"   ❌ Fractal: erro - {e}")

    # 4. CAOS-KRATOS
    print("\n4️⃣  Testando CAOS-KRATOS...")
    try:
        phi_normal = phi_kratos(0.5, 0.6, 0.7, 0.8, exploration_factor=1.0)
        phi_enhanced = phi_kratos(0.5, 0.6, 0.7, 0.8, exploration_factor=2.0)
        phi_adaptive = adaptive_kratos(0.5, 0.6, 0.7, 0.8, current_performance=0.6)

        results["modules_tested"].append("caos_kratos")
        results["metrics"]["phi_kratos"] = phi_enhanced
        results["metrics"]["phi_adaptive"] = phi_adaptive

        if phi_enhanced >= phi_normal and phi_adaptive > 0.0:
            results["modules_passed"].append("caos_kratos")
            print(f"   ✅ CAOS-KRATOS: φ_enhanced = {phi_enhanced:.3f}, φ_adaptive = {phi_adaptive:.3f}")
        else:
            results["modules_failed"].append("caos_kratos")
            print("   ❌ CAOS-KRATOS: valores inválidos")

    except Exception as e:
        results["modules_failed"].append("caos_kratos")
        results["errors"].append(f"caos_kratos: {str(e)}")
        print(f"   ❌ CAOS-KRATOS: erro - {e}")

    # 5. Blockchain Neural
    print("\n5️⃣  Testando Blockchain Neural...")
    try:
        # Adicionar bloco canário
        canary_state = {
            "test": "canary",
            "timestamp": time.time(),
            "alpha_eff": results["metrics"].get("alpha_eff", 0.0),
            "global_G": results["metrics"].get("global_G", 0.0),
        }

        chain_hash = add_block(canary_state)
        chain_head = get_chain_head()

        results["modules_tested"].append("neural_chain")
        results["metrics"]["chain_hash"] = chain_hash[:16] if chain_hash else "none"

        if chain_hash and chain_head:
            results["modules_passed"].append("neural_chain")
            print(f"   ✅ Neural Chain: bloco adicionado, hash = {chain_hash[:16]}...")
        else:
            results["modules_failed"].append("neural_chain")
            print("   ❌ Neural Chain: falha ao adicionar bloco")

    except Exception as e:
        results["modules_failed"].append("neural_chain")
        results["errors"].append(f"neural_chain: {str(e)}")
        print(f"   ❌ Neural Chain: erro - {e}")

    # 6. Checkpoint & Imunidade
    print("\n6️⃣  Testando Checkpoint & Imunidade...")
    try:
        # Checkpoint
        checkpoint_state = {"canary": True, "metrics": results["metrics"]}
        checkpoint_path = save_snapshot(checkpoint_state)

        # Imunidade (com threshold mais permissivo)
        immunity_ok = guard(results["metrics"], trigger=2.0)  # Permitir até 2 anomalias

        results["modules_tested"].extend(["checkpoint", "immunity"])

        if checkpoint_path and immunity_ok:
            results["modules_passed"].extend(["checkpoint", "immunity"])
            print(f"   ✅ Checkpoint: salvo, Imunidade: OK")
        else:
            if not checkpoint_path:
                results["modules_failed"].append("checkpoint")
            if not immunity_ok:
                results["modules_failed"].append("immunity")
            print(f"   ⚠️  Checkpoint: {bool(checkpoint_path)}, Imunidade: {immunity_ok}")

    except Exception as e:
        results["modules_failed"].extend(["checkpoint", "immunity"])
        results["errors"].append(f"checkpoint_immunity: {str(e)}")
        print(f"   ❌ Checkpoint/Imunidade: erro - {e}")

    # 7. Zero-Consciousness Proof
    print("\n7️⃣  Testando Zero-Consciousness Proof...")
    try:
        spi = spi_proxy(0.01, 0.02, 0.01)  # Valores baixos (sem consciência)
        consciousness_ok = assert_zero_consciousness(spi)

        results["modules_tested"].append("zero_consciousness")
        results["metrics"]["spi_proxy"] = spi

        if consciousness_ok:
            results["modules_passed"].append("zero_consciousness")
            print(f"   ✅ Zero-Consciousness: SPI = {spi:.4f} (sem consciência)")
        else:
            results["modules_failed"].append("zero_consciousness")
            print(f"   ❌ Zero-Consciousness: SPI = {spi:.4f} (possível consciência)")

    except Exception as e:
        results["modules_failed"].append("zero_consciousness")
        results["errors"].append(f"zero_consciousness: {str(e)}")
        print(f"   ❌ Zero-Consciousness: erro - {e}")

    # 8. Auto-docs
    print("\n8️⃣  Testando Auto-docs...")
    try:
        update_readme()
        readme_path = Path("README_AUTO.md")

        results["modules_tested"].append("auto_docs")

        if readme_path.exists():
            results["modules_passed"].append("auto_docs")
            print("   ✅ Auto-docs: README_AUTO.md gerado")
        else:
            results["modules_failed"].append("auto_docs")
            print("   ❌ Auto-docs: falha ao gerar README")

    except Exception as e:
        results["modules_failed"].append("auto_docs")
        results["errors"].append(f"auto_docs: {str(e)}")
        print(f"   ❌ Auto-docs: erro - {e}")

    # Finalizar canário
    canary_duration = time.time() - canary_start
    results["duration_s"] = canary_duration
    results["success_rate"] = (
        len(results["modules_passed"]) / len(results["modules_tested"]) if results["modules_tested"] else 0.0
    )
    results["overall_success"] = results["success_rate"] >= 0.8  # 80% dos módulos devem passar

    print(f"\n🎯 RESULTADO DO CANÁRIO")
    print("=" * 50)
    print(f"Duração: {canary_duration:.2f}s")
    print(f"Módulos testados: {len(results['modules_tested'])}")
    print(f"Módulos passaram: {len(results['modules_passed'])}")
    print(f"Módulos falharam: {len(results['modules_failed'])}")
    print(f"Taxa de sucesso: {results['success_rate']:.1%}")
    print(f"Sucesso geral: {'✅ SIM' if results['overall_success'] else '❌ NÃO'}")

    if results["errors"]:
        print(f"\nErros encontrados:")
        for error in results["errors"]:
            print(f"  - {error}")

    print(f"\nMétricas principais:")
    for key, value in results["metrics"].items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.4f}")
        else:
            print(f"  - {key}: {value}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PENIN-Ω Vida+ Canary Test")
    parser.add_argument("--save-report", action="store_true", help="Salvar relatório em arquivo")
    args = parser.parse_args()

    # Executar canário
    canary_results = run_canary_test()

    # Salvar relatório se solicitado
    if args.save_report:
        report_path = Path("canary_report.json")
        with report_path.open("w") as f:
            json.dump(canary_results, f, indent=2, default=str)
        print(f"\n📄 Relatório salvo em: {report_path}")

    # Exit code baseado no sucesso
    sys.exit(0 if canary_results["overall_success"] else 1)
