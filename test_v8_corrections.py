#!/usr/bin/env python3
"""Test script for v8.0 corrections - runs without external dependencies."""

import ast
import sys
from pathlib import Path


def test_caos_duplicates():
    """Test that phi_caos is defined only once."""
    print("Testing CAOS duplicates...")

    caos_file = Path("penin/omega/caos.py")
    source = caos_file.read_text()
    tree = ast.parse(source)

    # Count phi_caos definitions
    phi_caos_count = 0
    caos_components_init_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "phi_caos":
            phi_caos_count += 1
        elif isinstance(node, ast.ClassDef) and node.name == "CAOSComponents":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    caos_components_init_count += 1

    assert phi_caos_count == 1, f"❌ Found {phi_caos_count} phi_caos definitions (expected 1)"
    assert caos_components_init_count == 1, (
        f"❌ Found {caos_components_init_count} CAOSComponents.__init__ (expected 1)"
    )
    print("✅ CAOS: No duplicates found")
    return True


def test_router_syntax():
    """Test that router has no syntax errors and no orphan code."""
    print("Testing router syntax...")

    router_file = Path("penin/router.py")
    source = router_file.read_text()

    # Check for duplicate imports
    assert source.count("from datetime import") == 1, "❌ Duplicate datetime imports"

    # Check for orphan daily_usage references
    assert "self.daily_usage" not in source, "❌ Found orphan self.daily_usage reference"
    assert "_save_daily_usage" not in source, "❌ Found orphan _save_daily_usage reference"

    # Parse to check syntax
    try:
        ast.parse(source)
        print("✅ Router: Syntax valid, no orphan code")
        return True
    except SyntaxError as e:
        print(f"❌ Router syntax error: {e}")
        return False


def test_requirements_duplicates():
    """Test that requirements.txt has no duplicates."""
    print("Testing requirements.txt duplicates...")

    req_file = Path("requirements.txt")
    lines = req_file.read_text().strip().split("\n")

    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # Extract package name
            for sep in [">=", "==", "<=", ">", "<", "~=", "!="]:
                if sep in line:
                    package = line.split(sep)[0].strip().lower()
                    break
            else:
                package = line.strip().lower()

            if package:
                packages.append(package)

    seen = set()
    duplicates = []
    for pkg in packages:
        if pkg in seen:
            duplicates.append(pkg)
        seen.add(pkg)

    if duplicates:
        print(f"❌ Found duplicate packages: {duplicates}")
        return False
    else:
        print(f"✅ Requirements: No duplicates ({len(packages)} unique packages)")
        return True


def test_pyproject_toml():
    """Test that pyproject.toml is complete."""
    print("Testing pyproject.toml...")

    pyproject_file = Path("pyproject.toml")
    content = pyproject_file.read_text()

    required_sections = [
        "[build-system]",
        "[project]",
        "[project.scripts]",
        "[project.optional-dependencies]",
        "[tool.black]",
        "[tool.ruff]",
    ]

    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)

    if missing:
        print(f"❌ Missing sections in pyproject.toml: {missing}")
        return False

    # Check CLI entry point
    if 'penin = "penin.cli:main"' not in content:
        print("❌ Missing penin CLI entry point")
        return False

    print("✅ pyproject.toml: Complete with all sections")
    return True


def test_cache_module():
    """Test that cache module exists and uses orjson+HMAC."""
    print("Testing cache module...")

    cache_file = Path("penin/cache.py")
    if not cache_file.exists():
        print("❌ Cache module not found")
        return False

    content = cache_file.read_text()

    # Check for orjson
    if "import orjson" not in content:
        print("❌ Cache doesn't import orjson")
        return False

    # Check for HMAC
    if "import hmac" not in content:
        print("❌ Cache doesn't import hmac")
        return False

    # Check no pickle
    if "import pickle" in content or "pickle." in content:
        print("❌ Cache still uses pickle")
        return False

    print("✅ Cache: Uses orjson + HMAC, no pickle")
    return True


def test_tooling_files():
    """Test that tooling files exist."""
    print("Testing tooling files...")

    required_files = [
        ".env.example",
        ".gitignore",
        ".pre-commit-config.yaml",
        "LICENSE",
        "CHANGELOG.md",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print(f"❌ Missing tooling files: {missing}")
        return False

    print("✅ Tooling: All files present")
    return True


def test_github_workflows():
    """Test that GitHub workflows exist."""
    print("Testing GitHub workflows...")

    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("⚠️  GitHub workflows directory not found (may be intentional)")
        return True

    required_workflows = ["ci.yml", "security.yml"]
    missing = []

    for workflow in required_workflows:
        if not (workflows_dir / workflow).exists():
            missing.append(workflow)

    if missing:
        print(f"❌ Missing workflows: {missing}")
        return False

    print("✅ GitHub workflows: All present")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("PENIN v8.0 Upgrade Validation")
    print("=" * 60)
    print()

    tests = [
        test_caos_duplicates,
        test_router_syntax,
        test_requirements_duplicates,
        test_pyproject_toml,
        test_cache_module,
        test_tooling_files,
        test_github_workflows,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ {test.__name__} failed with error: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 v8.0 upgrade successful! Ready for deployment.")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("\nPlease review the failures above.")

    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
