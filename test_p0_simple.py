#!/usr/bin/env python3
"""
Teste Simples das Correções P0
==============================
"""

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    try:
        from penin.omega.ethics_metrics import EthicsMetricsCalculator
        from penin.omega.scoring import quick_harmonic
        from penin.omega.caos import quick_caos_phi
        from penin.omega.sr import quick_sr_harmonic
        from penin.omega.guards import quick_sigma_guard_check
        from penin.omega.ledger import WORMLedger
        print("✅ Todos os módulos Omega importados com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar módulos: {e}")
        return False

def test_basic_functionality():
    """Testa funcionalidade básica"""
    try:
        # Teste scoring
        from penin.omega.scoring import quick_harmonic
        result = quick_harmonic([0.8, 0.6, 0.9])
        assert 0 < result <= 1
        print(f"✅ Scoring: harmônica = {result:.3f}")
        
        # Teste CAOS⁺
        from penin.omega.caos import quick_caos_phi
        phi = quick_caos_phi(0.7, 0.8, 0.6, 0.5)
        assert 0 <= phi <= 1
        print(f"✅ CAOS⁺: φ = {phi:.3f}")
        
        # Teste SR
        from penin.omega.sr import quick_sr_harmonic
        sr = quick_sr_harmonic(0.8, 0.9, 0.7, 0.6)
        assert 0 <= sr <= 1
        print(f"✅ SR: score = {sr:.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos testes básicos: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testando correções P0...\n")
    
    success = True
    success &= test_imports()
    success &= test_basic_functionality()
    
    if success:
        print("\n✅ Todos os testes P0 passaram!")
    else:
        print("\n❌ Alguns testes falharam")