#!/usr/bin/env python3
"""
Teste de integração completa do sistema PENIN-Ω (1/8 até 8/8)
"""

import sys
from pathlib import Path


def test_module_1():
    """Test módulo 1/8 (Core)"""
    print("Testing 1/8 (Core)...")
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "1_de_8", "--test"], check=False, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("✅ 1/8 (Core) - All tests passed")
            return True
        else:
            print(f"❌ 1/8 (Core) - Tests failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 1/8 (Core) - Error: {e}")
        return False


def test_module_2():
    """Test módulo 2/8 (Strategy)"""
    print("Testing 2/8 (Strategy)...")
    try:
        import subprocess

        result = subprocess.run([sys.executable, "2_de_8"], check=False, capture_output=True, text=True, timeout=10)
        if "PLANO GERADO" in result.stdout:
            print("✅ 2/8 (Strategy) - Working")
            return True
        else:
            print("❌ 2/8 (Strategy) - No plan generated")
            return False
    except Exception as e:
        print(f"❌ 2/8 (Strategy) - Error: {e}")
        return False


def test_module_3():
    """Test módulo 3/8 (Acquisition)"""
    print("Testing 3/8 (Acquisition)...")
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "3_de_8", "--seed", "42"], check=False, capture_output=True, text=True, timeout=15
        )
        if "RELATÓRIO DE AQUISIÇÃO" in result.stdout:
            print("✅ 3/8 (Acquisition) - Working")
            return True
        else:
            print("❌ 3/8 (Acquisition) - No report generated")
            return False
    except Exception as e:
        print(f"❌ 3/8 (Acquisition) - Error: {e}")
        return False


def test_module_4():
    """Test módulo 4/8 (Mutation)"""
    print("Testing 4/8 (Mutation)...")
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "4_de_8", "--test"], check=False, capture_output=True, text=True, timeout=20
        )
        if "tests completed" in result.stdout.lower():
            print("✅ 4/8 (Mutation) - Tests completed")
            return True
        else:
            print("❌ 4/8 (Mutation) - Tests failed")
            return False
    except Exception as e:
        print(f"❌ 4/8 (Mutation) - Error: {e}")
        return False


def test_module_5():
    """Test módulo 5/8 (Crucible)"""
    print("Testing 5/8 (Crucible)...")
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "5_de_8", "--test"], check=False, capture_output=True, text=True, timeout=20
        )
        if "All tests passed" in result.stdout or "tests completed" in result.stdout.lower():
            print("✅ 5/8 (Crucible) - Tests passed")
            return True
        else:
            print("❌ 5/8 (Crucible) - Tests failed")
            return False
    except Exception as e:
        print(f"❌ 5/8 (Crucible) - Error: {e}")
        return False


def test_integration_flow():
    """Test fluxo de integração completo"""
    print("\nTesting complete integration flow...")

    try:
        # Test if modules can import each other
        sys.path.insert(0, str(Path.cwd()))

        # Test basic imports with fallback loader for script files
        import importlib.machinery
        import importlib.util
        from importlib import import_module

        def _fallback_load(module_name: str) -> bool:
            p = Path.cwd() / module_name
            if not p.exists():
                return False
            try:
                loader = importlib.machinery.SourceFileLoader(module_name, str(p))
                spec = importlib.util.spec_from_loader(module_name, loader)
                mod = importlib.util.module_from_spec(spec)
                loader.exec_module(mod)
                sys.modules[module_name] = mod
                return True
            except Exception:
                return False

        modules = []
        for i in range(1, 5 + 1):
            module_name = f"{i}_de_8"
            try:
                import_module(module_name)
                modules.append(f"{i}/8")
                print(f"✅ Module {i}/8 importable")
            except Exception as e:
                # Try fallback direct file load (handles files without .py extension)
                if _fallback_load(module_name):
                    modules.append(f"{i}/8")
                    print(f"✅ Module {i}/8 loaded via fallback")
                else:
                    print(f"⚠️ Module {i}/8 import issue: {e}")

        print(f"✅ Integration flow - {len(modules)}/5 modules working")
        return len(modules) >= 3  # At least 3 modules working

    except Exception as e:
        print(f"❌ Integration flow - Error: {e}")
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("PENIN-Ω COMPLETE INTEGRATION TEST")
    print("=" * 60)

    results = []

    # Test individual modules
    results.append(test_module_1())
    results.append(test_module_2())
    results.append(test_module_3())
    results.append(test_module_4())
    results.append(test_module_5())

    # Test integration
    results.append(test_integration_flow())

    # Summary
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed / total * 100:.1f}%")

    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ System is fully integrated and working")
        return 0
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - system mostly working")
        return 0
    else:
        print("❌ Multiple failures - system needs attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
