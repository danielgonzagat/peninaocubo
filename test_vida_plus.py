#!/usr/bin/env python3
"""
PENIN-Ω Vida+ Test Suite
========================

Comprehensive test suite for all Vida+ modules and integration.
Tests the Life Equation (+) and all advanced cognitive modules.
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add penin to path
sys.path.insert(0, str(Path(__file__).parent))

from penin.omega.life_eq import life_equation, test_life_equation
from penin.omega.fractal import build_fractal, propagate_update, test_fractal_system
from penin.omega.swarm import heartbeat, sample_global_state, test_swarm_system
from penin.omega.caos_kratos import phi_kratos, test_caos_kratos
from penin.omega.market import InternalMarket, test_marketplace_system
from penin.omega.neural_chain import add_block, test_neural_chain
from penin.omega.self_rag import ingest_text, query, self_cycle, test_self_rag_system
from penin.omega.api_metabolizer import record_call, suggest_replay, test_api_metabolizer
from penin.omega.immunity import test_immunity_system
from penin.omega.checkpoint import test_checkpoint_system
from penin.omega.game import test_game_system
from penin.omega.darwin_audit import test_darwin_audit_system
from penin.omega.zero_consciousness import test_zero_consciousness_system
from penin.auto_docs import test_auto_documentation


async def test_all_modules():
    """Test all Vida+ modules"""
    print("🧪 PENIN-Ω Vida+ Test Suite")
    print("=" * 50)
    
    test_results = {}
    
    # Test Life Equation (+)
    print("\n1. Testing Life Equation (+)...")
    try:
        result = test_life_equation()
        test_results["life_equation"] = {"status": "PASS", "result": result}
        print("   ✅ Life Equation (+) test passed")
    except Exception as e:
        test_results["life_equation"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Life Equation (+) test failed: {e}")
    
    # Test Fractal DSL
    print("\n2. Testing Fractal DSL...")
    try:
        result = test_fractal_system()
        test_results["fractal"] = {"status": "PASS", "result": result}
        print("   ✅ Fractal DSL test passed")
    except Exception as e:
        test_results["fractal"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Fractal DSL test failed: {e}")
    
    # Test Swarm Cognitive
    print("\n3. Testing Swarm Cognitive...")
    try:
        result = test_swarm_system()
        test_results["swarm"] = {"status": "PASS", "result": result}
        print("   ✅ Swarm Cognitive test passed")
    except Exception as e:
        test_results["swarm"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Swarm Cognitive test failed: {e}")
    
    # Test CAOS-KRATOS
    print("\n4. Testing CAOS-KRATOS...")
    try:
        result = test_caos_kratos()
        test_results["caos_kratos"] = {"status": "PASS", "result": result}
        print("   ✅ CAOS-KRATOS test passed")
    except Exception as e:
        test_results["caos_kratos"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ CAOS-KRATOS test failed: {e}")
    
    # Test Marketplace
    print("\n5. Testing Marketplace...")
    try:
        result = test_marketplace_system()
        test_results["marketplace"] = {"status": "PASS", "result": result}
        print("   ✅ Marketplace test passed")
    except Exception as e:
        test_results["marketplace"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Marketplace test failed: {e}")
    
    # Test Neural Chain
    print("\n6. Testing Neural Chain...")
    try:
        result = test_neural_chain()
        test_results["neural_chain"] = {"status": "PASS", "result": result}
        print("   ✅ Neural Chain test passed")
    except Exception as e:
        test_results["neural_chain"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Neural Chain test failed: {e}")
    
    # Test Self-RAG
    print("\n7. Testing Self-RAG...")
    try:
        result = test_self_rag_system()
        test_results["self_rag"] = {"status": "PASS", "result": result}
        print("   ✅ Self-RAG test passed")
    except Exception as e:
        test_results["self_rag"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Self-RAG test failed: {e}")
    
    # Test API Metabolizer
    print("\n8. Testing API Metabolizer...")
    try:
        result = test_api_metabolizer()
        test_results["api_metabolizer"] = {"status": "PASS", "result": result}
        print("   ✅ API Metabolizer test passed")
    except Exception as e:
        test_results["api_metabolizer"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ API Metabolizer test failed: {e}")
    
    # Test Immunity
    print("\n9. Testing Immunity...")
    try:
        result = test_immunity_system()
        test_results["immunity"] = {"status": "PASS", "result": result}
        print("   ✅ Immunity test passed")
    except Exception as e:
        test_results["immunity"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Immunity test failed: {e}")
    
    # Test Checkpoint
    print("\n10. Testing Checkpoint...")
    try:
        result = test_checkpoint_system()
        test_results["checkpoint"] = {"status": "PASS", "result": result}
        print("   ✅ Checkpoint test passed")
    except Exception as e:
        test_results["checkpoint"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Checkpoint test failed: {e}")
    
    # Test GAME
    print("\n11. Testing GAME...")
    try:
        result = test_game_system()
        test_results["game"] = {"status": "PASS", "result": result}
        print("   ✅ GAME test passed")
    except Exception as e:
        test_results["game"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ GAME test failed: {e}")
    
    # Test Darwinian Audit
    print("\n12. Testing Darwinian Audit...")
    try:
        result = test_darwin_audit_system()
        test_results["darwin_audit"] = {"status": "PASS", "result": result}
        print("   ✅ Darwinian Audit test passed")
    except Exception as e:
        test_results["darwin_audit"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Darwinian Audit test failed: {e}")
    
    # Test Zero Consciousness
    print("\n13. Testing Zero Consciousness...")
    try:
        result = test_zero_consciousness_system()
        test_results["zero_consciousness"] = {"status": "PASS", "result": result}
        print("   ✅ Zero Consciousness test passed")
    except Exception as e:
        test_results["zero_consciousness"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Zero Consciousness test failed: {e}")
    
    # Test Auto Documentation
    print("\n14. Testing Auto Documentation...")
    try:
        result = test_auto_documentation()
        test_results["auto_docs"] = {"status": "PASS", "result": result}
        print("   ✅ Auto Documentation test passed")
    except Exception as e:
        test_results["auto_docs"] = {"status": "FAIL", "error": str(e)}
        print(f"   ❌ Auto Documentation test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for result in test_results.values() if result["status"] == "PASS")
    failed = sum(1 for result in test_results.values() if result["status"] == "FAIL")
    total = len(test_results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\n❌ Failed tests:")
        for module, result in test_results.items():
            if result["status"] == "FAIL":
                print(f"   - {module}: {result['error']}")
    else:
        print("\n🎉 All tests passed! Vida+ system is ready.")
    
    return test_results


async def test_integration():
    """Test integration of Vida+ modules with evolution cycle"""
    print("\n🔗 Testing Vida+ Integration...")
    
    try:
        from penin.omega.runners import EvolutionRunner, EvolutionConfig
        
        # Create config with Vida+ enabled
        config = EvolutionConfig(
            n_challengers=2,
            budget_minutes=5,
            dry_run=True,
            enable_vida_plus=True,
            base_alpha=0.02
        )
        
        # Initialize runner
        runner = EvolutionRunner(config)
        
        # Run one cycle
        print("   Running evolution cycle with Vida+...")
        result = await runner.evolve_one_cycle()
        
        print(f"   ✅ Integration test passed")
        print(f"   Cycle ID: {result.cycle_id}")
        print(f"   Decision: {result.decision}")
        print(f"   Vida+ results: {len(result.life_equation_results) if result.life_equation_results else 0} challengers")
        
        return {"status": "PASS", "result": result}
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return {"status": "FAIL", "error": str(e)}


async def main():
    """Main test function"""
    print("🚀 Starting PENIN-Ω Vida+ Test Suite")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual modules
    module_results = await test_all_modules()
    
    # Test integration
    integration_result = await test_integration()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL SUMMARY")
    print("=" * 60)
    
    module_passed = sum(1 for r in module_results.values() if r["status"] == "PASS")
    module_total = len(module_results)
    integration_passed = integration_result["status"] == "PASS"
    
    print(f"Module tests: {module_passed}/{module_total} passed")
    print(f"Integration test: {'PASSED' if integration_passed else 'FAILED'}")
    
    if module_passed == module_total and integration_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🌟 PENIN-Ω Vida+ system is fully operational!")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)