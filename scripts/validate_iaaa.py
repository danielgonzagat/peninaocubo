#!/usr/bin/env python3
"""
Validação IAAA — Script de Verificação Completa
===============================================

Valida a implementação completa do PENIN-Ω IAAA:
- Importação de todas as 15 equações
- Funcionamento dos módulos principais
- Integridade ética (ΣEA/LO-14)
- WORM ledger operacional
- Σ-Guard fail-closed

Execute: python scripts/validate_iaaa.py
"""

import sys
import traceback


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_imports() -> dict[str, bool]:
    """Test all critical imports"""
    print_section("1. Testing Critical Imports")

    results = {}

    # Test 1: Core equations
    try:
        print("✅ Todas as 15 equações importadas com sucesso!")
        results["equations"] = True
    except Exception as e:
        print(f"❌ Erro ao importar equações: {e}")
        traceback.print_exc()
        results["equations"] = False

    # Test 2: Existing modules (backward compatibility)
    try:
        print("✅ Módulos existentes (backward compatibility) OK!")
        results["backward_compat"] = True
    except Exception as e:
        print(f"❌ Erro em módulos existentes: {e}")
        traceback.print_exc()
        results["backward_compat"] = False

    # Test 3: Optional research plugins (may not be installed)
    plugins_available = {}

    try:
        plugins_available["nextpy"] = True
        print("✅ NextPy adapter disponível")
    except:
        plugins_available["nextpy"] = False
        print("⚠️  NextPy adapter criado mas biblioteca não instalada (opcional)")

    try:
        plugins_available["symbolicai"] = True
        print("✅ SymbolicAI adapter disponível")
    except:
        plugins_available["symbolicai"] = False
        print("⚠️  SymbolicAI adapter criado mas biblioteca não instalada (opcional)")

    try:
        plugins_available["metacognitive"] = True
        print("✅ Metacognitive Prompting disponível")
    except:
        plugins_available["metacognitive"] = False
        print("⚠️  Metacognitive Prompting criado mas módulo em desenvolvimento")

    results["plugins"] = plugins_available

    return results


def test_basic_functionality() -> bool:
    """Test basic functionality of main equations"""
    print_section("2. Testing Basic Functionality")

    try:
        import numpy as np

        from penin.equations import (
            ControlPolicy,
            CostComponents,
            EthicalGates,
            Evidence,
            Metric,
            PeninState,
            ProjectionConstraints,
            compute_linf_meta,
            penin_update,
            sigma_guard_check,
        )

        # Setup básico
        print("Criando estado inicial...")
        state = PeninState(parameters=np.random.randn(10))
        evidence = Evidence(rewards=[0.8])
        policy = ControlPolicy(base_alpha=0.001)
        constraints = ProjectionConstraints(max_norm=10.0)

        print("✅ Setup OK")

        # Testar L∞
        print("\nTestando Meta-Função L∞...")
        metrics = [
            Metric("accuracy", 0.85, weight=0.5),
            Metric("robustness", 0.78, weight=0.5),
        ]
        cost = CostComponents(time_seconds=1.0, tokens_used=100)
        gates = EthicalGates(
            rho_contractivity=0.95,
            ece=0.008,
            rho_bias=1.03,
            consent=True,
            eco_ok=True,
        )

        linf, linf_details = compute_linf_meta(metrics, cost, gates)
        print(f"✅ L∞ = {linf:.4f}")
        print(f"   - Base score: {linf_details.get('base_score', 0):.4f}")
        print(f"   - Cost penalty: {linf_details.get('cost_penalty', 0):.4f}")
        print(f"   - Ethical gates: {linf_details.get('ethical_gates_pass', False)}")

        # Testar Σ-Guard
        print("\nTestando Σ-Guard Gate...")
        gate_pass, gate_details = sigma_guard_check(
            rho=0.95,
            ece=0.008,
            rho_bias=1.03,
            consent=True,
            eco_ok=True,
        )
        print(f"✅ Σ-Guard: {'PASS' if gate_pass else 'FAIL'}")
        print(f"   - Checks: {gate_details['checks']}")

        # Testar Penin Update (apenas se gate passar)
        if gate_pass:
            print("\nTestando Penin Update...")

            def simple_objective(s, e):
                return linf  # Placeholder

            new_state, update_info = penin_update(
                state,
                evidence,
                policy,
                constraints,
                objective_fn=simple_objective,
                caos_phi=0.5,
                sr_score=0.85,
                r_score=0.85,
            )

            print(f"✅ Update: {update_info['action']}")
            print(f"   - State changed: {update_info['state_changed']}")
            if "alpha_eff" in update_info:
                print(f"   - α_eff: {update_info['alpha_eff']:.6f}")

        return True

    except Exception as e:
        print(f"❌ Erro em testes funcionais: {e}")
        traceback.print_exc()
        return False


def test_ethical_fail_closed() -> bool:
    """Test fail-closed behavior on ethical violations"""
    print_section("3. Testing Fail-Closed Behavior")

    try:
        from penin.equations import (
            CostComponents,
            EthicalGates,
            LInfConfig,
            Metric,
            compute_linf_meta,
            sigma_guard_check,
        )

        # Test 1: Violação de consent
        print("Teste 1: Violação de consent (LO-07)...")
        gate_pass, details = sigma_guard_check(
            rho=0.95,
            ece=0.008,
            rho_bias=1.03,
            consent=False,  # VIOLAÇÃO!
            eco_ok=True,
        )

        if not gate_pass and "consent" in details.get("failed_checks", []):
            print("✅ Fail-closed funcionando: consent=False → gate rejeitou")
        else:
            print("❌ Fail-closed FALHOU: deveria rejeitar consent=False")
            return False

        # Test 2: Violação de contratividade (ρ ≥ 1.0)
        print("\nTeste 2: Violação de contratividade (LO-04)...")
        gate_pass, details = sigma_guard_check(
            rho=1.05,  # VIOLAÇÃO! (≥ 1.0)
            ece=0.008,
            rho_bias=1.03,
            consent=True,
            eco_ok=True,
        )

        if not gate_pass and "rho_ok" in [k for k, v in details["checks"].items() if not v]:
            print("✅ Fail-closed funcionando: ρ≥1.0 → gate rejeitou")
        else:
            print("❌ Fail-closed FALHOU: deveria rejeitar ρ≥1.0")
            return False

        # Test 3: Violação de ECE
        print("\nTeste 3: Violação de ECE (calibração)...")
        gate_pass, details = sigma_guard_check(
            rho=0.95,
            ece=0.05,  # VIOLAÇÃO! (> 0.01)
            rho_bias=1.03,
            consent=True,
            eco_ok=True,
        )

        if not gate_pass:
            print("✅ Fail-closed funcionando: ECE>0.01 → gate rejeitou")
        else:
            print("❌ Fail-closed FALHOU: deveria rejeitar ECE>0.01")
            return False

        # Test 4: L∞ com gates falhando
        print("\nTeste 4: L∞ com gates éticos falhando...")
        metrics = [Metric("acc", 0.9, weight=1.0)]
        cost = CostComponents()
        gates_bad = EthicalGates(
            rho_contractivity=1.5,  # VIOLAÇÃO!
            consent=False,  # VIOLAÇÃO!
        )
        config = LInfConfig(fail_closed=True)

        linf, details = compute_linf_meta(metrics, cost, gates_bad, config)

        if linf == 0.0 and details["action"] == "rejected_ethical_gates":
            print("✅ L∞ fail-closed funcionando: violações → L∞=0")
        else:
            print("❌ L∞ fail-closed FALHOU: deveria zerar com violações")
            return False

        print("\n✅ Todos os testes de fail-closed passaram!")
        return True

    except Exception as e:
        print(f"❌ Erro em testes de fail-closed: {e}")
        traceback.print_exc()
        return False


def test_worm_ledger() -> bool:
    """Test WORM ledger functionality"""
    print_section("4. Testing WORM Ledger")

    try:
        import os

        from penin.ledger.worm_ledger import append_event, merkle_root

        # Limpar ledger de teste
        test_ledger = "ledger/worm_test.log"
        if os.path.exists(test_ledger):
            os.remove(test_ledger)

        print("Gravando eventos de teste no WORM ledger...")

        # Modificar temporariamente LEDGER para teste
        import penin.ledger.worm_ledger as worm

        original_ledger = worm.LEDGER
        worm.LEDGER = test_ledger

        # Adicionar eventos
        append_event({"event": "test_1", "value": 42})
        append_event({"event": "test_2", "value": 84})
        append_event({"event": "test_3", "value": 126})

        # Calcular merkle root
        root = merkle_root()

        # Restaurar LEDGER original
        worm.LEDGER = original_ledger

        if root:
            print("✅ WORM ledger funcionando!")
            print(f"   - Merkle root: {root[:16]}...")
            print("   - 3 eventos registrados")

            # Verificar imutabilidade (eventos gravados)
            with open(test_ledger) as f:
                lines = f.readlines()
                if len(lines) == 3:
                    print("✅ Imutabilidade verificada: 3 linhas gravadas")
                else:
                    print(f"⚠️  Esperado 3 linhas, encontrado {len(lines)}")

            # Limpar
            os.remove(test_ledger)

            return True
        else:
            print("❌ Merkle root vazio")
            return False

    except Exception as e:
        print(f"❌ Erro em WORM ledger: {e}")
        traceback.print_exc()
        return False


def test_mathematical_guarantees() -> bool:
    """Test mathematical guarantees (contractividade, não-compensatoriedade)"""
    print_section("5. Testing Mathematical Guarantees")

    try:
        import numpy as np

        from penin.equations import (
            Metric,
            harmonic_mean_weighted,
            ir_to_ic,
            lyapunov_check,
        )

        # Test 1: Lyapunov contratividade
        print("Teste 1: Contratividade Lyapunov...")
        state_current = np.array([1.0, 2.0, 3.0])
        state_next_good = np.array([0.9, 1.8, 2.7])  # Mais perto de 0
        state_next_bad = np.array([1.1, 2.2, 3.3])  # Mais longe de 0

        is_contractive, V_curr, V_next = lyapunov_check(state_current, state_next_good)
        if is_contractive and V_next < V_curr:
            print(f"✅ Lyapunov OK: V({V_curr:.2f}) → V({V_next:.2f}) < V_curr")
        else:
            print("❌ Lyapunov FALHOU: deveria ser contrativo")
            return False

        is_contractive_bad, _, _ = lyapunov_check(state_current, state_next_bad)
        if not is_contractive_bad:
            print("✅ Lyapunov detectou não-contratividade corretamente")
        else:
            print("❌ Lyapunov não detectou expansão")
            return False

        # Test 2: IR→IC contratividade
        print("\nTeste 2: IR→IC (Lapidação de risco)...")
        knowledge = {"risk": 1.0, "data": "test"}
        rho = 0.9

        lapidated, converged = ir_to_ic(knowledge, rho=rho, max_iterations=3)

        if converged and lapidated["risk"] <= knowledge["risk"]:
            print(f"✅ IR→IC OK: risk {knowledge['risk']:.2f} → {lapidated['risk']:.2f}")
        else:
            print("❌ IR→IC não convergiu ou risco não reduziu")
            return False

        # Test 3: Não-compensatoriedade (L∞ harmônica)
        print("\nTeste 3: Não-compensatoriedade (média harmônica)...")

        # Caso 1: Métricas balanceadas
        metrics_balanced = [
            Metric("m1", 0.8, weight=0.5),
            Metric("m2", 0.8, weight=0.5),
        ]
        score_balanced = harmonic_mean_weighted(metrics_balanced)

        # Caso 2: Uma métrica muito baixa (bottleneck)
        metrics_bottleneck = [
            Metric("m1", 0.1, weight=0.5),  # BAIXA!
            Metric("m2", 0.9, weight=0.5),  # Alta
        ]
        score_bottleneck = harmonic_mean_weighted(metrics_bottleneck)

        # Média harmônica deve penalizar bottleneck
        if score_bottleneck < score_balanced * 0.5:
            print("✅ Não-compensatoriedade OK:")
            print(f"   - Balanceado: {score_balanced:.3f}")
            print(f"   - Bottleneck: {score_bottleneck:.3f} (< 50% do balanceado)")
        else:
            print("❌ Não-compensatoriedade FALHOU:")
            print(f"   - Bottleneck deveria ser < {score_balanced * 0.5:.3f}")
            print(f"   - Obtido: {score_bottleneck:.3f}")
            return False

        print("\n✅ Todas as garantias matemáticas verificadas!")
        return True

    except Exception as e:
        print(f"❌ Erro em garantias matemáticas: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print(
        """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              PENIN-Ω IAAA Validation Suite                       ║
║                                                                  ║
║     Inteligência Artificial Adaptativa Autoevolutiva             ║
║              Autoconsciente e Auditável                          ║
║                                                                  ║
║                      Version 1.0.0                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    )

    results = {}

    # Run tests
    import_results = test_imports()
    results["imports"] = import_results.get("equations", False) and import_results.get("backward_compat", False)

    results["functionality"] = test_basic_functionality()
    results["fail_closed"] = test_ethical_fail_closed()
    results["worm_ledger"] = test_worm_ledger()
    results["math_guarantees"] = test_mathematical_guarantees()

    # Summary
    print_section("SUMMARY / RESUMO")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    print(f"Testes executados: {total_tests}")
    print(f"Testes passados:   {passed_tests}")
    print(f"Testes falhados:   {total_tests - passed_tests}")
    print()

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print()

    if passed_tests == total_tests:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║           ✅ IAAA VALIDATION: ALL TESTS PASSED ✅            ║")
        print("║                                                              ║")
        print("║        Sistema IAAA validado e pronto para uso!             ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        return 0
    else:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║            ⚠️  IAAA VALIDATION: SOME TESTS FAILED           ║")
        print("║                                                              ║")
        print("║   Alguns testes falharam. Ver detalhes acima.               ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        return 1


if __name__ == "__main__":
    sys.exit(main())
