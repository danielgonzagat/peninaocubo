#!/usr/bin/env python3
"""
Teste de Integração Completo - PENIN-Ω Vida+
============================================

Valida todos os módulos implementados e sua integração.
"""

import sys
import time
from pathlib import Path

# Adicionar ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

def test_life_equation():
    """Testa Equação de Vida (+)"""
    print("🧬 Testando Equação de Vida (+)...")
    
    from penin.omega.life_eq import quick_life_check, validate_life_equation_gates
    
    # Teste básico
    verdict = quick_life_check()
    assert verdict.ok, f"Life equation should pass with good parameters"
    assert verdict.alpha_eff > 0, f"Alpha effective should be positive: {verdict.alpha_eff}"
    
    # Validação de gates
    gates = validate_life_equation_gates()
    assert gates["all_ok"]["passed"], "All OK test should pass"
    assert not gates["high_ece"]["passed"], "High ECE test should fail"
    assert not gates["low_dlinf"]["passed"], "Low dLinf test should fail"
    
    print("  ✅ Equação de Vida (+) funcionando corretamente")


def test_fractal_dsl():
    """Testa DSL Fractal"""
    print("🌿 Testando DSL Fractal...")
    
    from penin.omega.fractal import quick_fractal_test, validate_fractal_non_compensatory
    
    # Teste básico
    result = quick_fractal_test()
    assert result["total_nodes"] > 1, "Should create multiple nodes"
    assert result["update_report"]["success"], "Update should succeed"
    
    # Teste não-compensatório
    nc_test = validate_fractal_non_compensatory()
    assert nc_test["passed"], "Non-compensatory test should pass"
    
    print("  ✅ DSL Fractal funcionando corretamente")


def test_swarm_cognitive():
    """Testa Swarm Cognitivo"""
    print("🐝 Testando Swarm Cognitivo...")
    
    from penin.omega.swarm import quick_swarm_test, validate_swarm_aggregation
    
    # Teste básico
    result = quick_swarm_test()
    assert result["nodes_simulated"] >= 3, "Should simulate multiple nodes"
    assert result["global_state"]["active_nodes"] >= 3, "Should have active nodes"
    
    # Validação de agregação
    validation = validate_swarm_aggregation()
    assert validation["validation"]["all_passed"], "Aggregation validation should pass"
    
    print("  ✅ Swarm Cognitivo funcionando corretamente")


def test_caos_kratos():
    """Testa CAOS-KRATOS"""
    print("⚡ Testando CAOS-KRATOS...")
    
    from penin.omega.caos_kratos import quick_kratos_test, validate_kratos_saturation, validate_kratos_exploration_gain
    
    # Teste básico
    result = quick_kratos_test()
    assert result["engine_result"]["phi"] > 0, "Phi should be positive"
    
    # Validação de saturação
    saturation = validate_kratos_saturation()
    assert saturation["passed"], "Saturation test should pass"
    
    # Validação de ganho de exploração
    gain_test = validate_kratos_exploration_gain()
    assert gain_test["passed"], "Exploration gain test should pass"
    
    print("  ✅ CAOS-KRATOS funcionando corretamente")


def test_marketplace():
    """Testa Marketplace Cognitivo"""
    print("🏪 Testando Marketplace Cognitivo...")
    
    from penin.omega.market import quick_market_test, validate_market_conservation
    
    # Teste básico
    result = quick_market_test()
    assert result["trades_executed"] > 0, "Should execute trades"
    
    # Validação de conservação
    conservation = validate_market_conservation()
    assert conservation["passed"], "Conservation test should pass"
    
    print("  ✅ Marketplace Cognitivo funcionando corretamente")


def test_neural_chain():
    """Testa Blockchain Neural"""
    print("⛓️ Testando Blockchain Neural...")
    
    from penin.omega.neural_chain import quick_neural_chain_test, validate_neural_chain_integrity
    
    # Teste básico
    result = quick_neural_chain_test()
    assert result["blocks_added"] > 0, "Should add blocks"
    assert result["validation"]["valid"], "Chain should be valid"
    
    # Validação de integridade
    integrity = validate_neural_chain_integrity()
    assert integrity["passed"], "Integrity test should pass"
    
    print("  ✅ Blockchain Neural funcionando corretamente")


def test_remaining_modules():
    """Testa módulos restantes"""
    print("🔧 Testando módulos restantes...")
    
    # API Metabolizer
    from penin.omega.api_metabolizer import record_call, suggest_replay, get_metabolization_stats
    hash_id = record_call("test", "endpoint", {"prompt": "test"}, {"response": "ok"})
    assert hash_id, "Should return hash ID"
    stats = get_metabolization_stats()
    assert stats["total_calls"] > 0, "Should have recorded calls"
    
    # Self-RAG
    from penin.omega.self_rag import ingest_text, query, self_cycle, get_knowledge_stats
    ingest_text("test_doc", "This is a test document about PENIN evolution")
    result = query("test evolution")
    assert result["total_found"] > 0, "Should find documents"
    
    # Imunidade Digital
    from penin.omega.immunity import guard, immune_response
    assert guard({"phi": 0.8, "sr": 0.9}), "Should pass with good metrics"
    assert not guard({"phi": float('nan')}), "Should fail with NaN"
    
    # Checkpoint
    from penin.omega.checkpoint import save_snapshot, restore_last, list_snapshots
    save_snapshot({"test": "state"})
    restored = restore_last()
    assert restored is not None, "Should restore snapshot"
    
    # GAME + Darwin
    from penin.omega.game import GAMEOptimizer
    from penin.omega.darwin_audit import darwinian_score, selection_audit
    
    optimizer = GAMEOptimizer()
    step = optimizer.step(0.1)
    assert isinstance(step, float), "Should return float step"
    
    score = darwinian_score(True, 0.8, 0.9, 0.85, 0.7)
    assert score > 0, "Should return positive score for good metrics"
    
    # Zero-Consciousness
    from penin.omega.zero_consciousness import spi_proxy, assert_zero_consciousness, consciousness_audit
    spi = spi_proxy(0.005, 0.9, 0.01)  # Parâmetros que garantem SPI baixo
    assert spi < 0.1, f"SPI should be low for good parameters: {spi}"
    assert assert_zero_consciousness(spi), f"Should assert zero consciousness: SPI={spi}"
    
    print("  ✅ Todos os módulos restantes funcionando corretamente")


def test_auto_docs():
    """Testa geração de documentação automática"""
    print("📚 Testando Auto-Docs...")
    
    from penin.auto_docs import update_readme, generate_system_report
    
    # Atualizar README
    result = update_readme()
    assert result["status"] == "success", "README update should succeed"
    
    # Gerar relatório
    report = generate_system_report()
    assert "overall_health" in report, "Should have overall health"
    
    print("  ✅ Auto-Docs funcionando corretamente")


def run_integration_test():
    """Executa teste de integração completo"""
    print("🚀 PENIN-Ω Vida+ - Teste de Integração Completo")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Executar todos os testes
        test_life_equation()
        test_fractal_dsl()
        test_swarm_cognitive()
        test_caos_kratos()
        test_marketplace()
        test_neural_chain()
        test_remaining_modules()
        test_auto_docs()
        
        # Sucesso
        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"✅ TODOS OS TESTES PASSARAM! ({elapsed:.2f}s)")
        print("🎉 PENIN-Ω Vida+ está funcionalmente completo!")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"❌ TESTE FALHOU: {e} ({elapsed:.2f}s)")
        import traceback
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)