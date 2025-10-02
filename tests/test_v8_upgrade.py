"""Integration tests for v8.0 upgrade."""

from pathlib import Path

import pytest


def test_package_structure():
    """Test that package structure is correct."""
    root = Path(__file__).parent.parent

    # Check essential files exist
    assert (root / "pyproject.toml").exists(), "pyproject.toml missing"
    assert (root / "requirements.txt").exists(), "requirements.txt missing"
    assert (root / "LICENSE").exists(), "LICENSE missing"
    assert (root / ".env.example").exists(), ".env.example missing"
    assert (root / ".gitignore").exists(), ".gitignore missing"
    assert (root / ".pre-commit-config.yaml").exists(), ".pre-commit-config.yaml missing"

    # Check package structure
    assert (root / "penin").is_dir(), "penin package directory missing"
    assert (root / "penin" / "__init__.py").exists(), "penin/__init__.py missing"
    assert (root / "penin" / "cli.py").exists(), "penin/cli.py missing"
    assert (root / "penin" / "omega").is_dir(), "penin/omega directory missing"
    assert (root / "penin" / "providers").is_dir(), "penin/providers directory missing"


def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid and complete."""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"

    content = pyproject.read_text()

    # Check essential sections
    assert "[build-system]" in content, "Missing [build-system] section"
    assert "[project]" in content, "Missing [project] section"
    assert "[project.scripts]" in content, "Missing [project.scripts] section"
    assert "[project.optional-dependencies]" in content, "Missing [project.optional-dependencies]"

    # Check CLI entry point
    assert 'penin = "penin.cli:main"' in content, "Missing penin CLI entry point"

    # Check version
    assert 'version = "0.9.0"' in content, "Version should be 0.9.0"


def test_requirements_no_duplicates():
    """Test that requirements.txt has no duplicate entries."""
    root = Path(__file__).parent.parent
    requirements = root / "requirements.txt"

    lines = requirements.read_text().strip().split("\n")

    # Extract package names (before version specifiers)
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # Extract package name (before >=, ==, etc.)
            for sep in [">=", "==", "<=", ">", "<", "~=", "!="]:
                if sep in line:
                    package = line.split(sep)[0].strip()
                    break
            else:
                package = line.strip()
            packages.append(package.lower())

    # Check for duplicates
    seen = set()
    duplicates = []
    for pkg in packages:
        if pkg in seen:
            duplicates.append(pkg)
        seen.add(pkg)

    assert len(duplicates) == 0, f"Duplicate packages found: {duplicates}"


def test_github_workflows_valid():
    """Test that GitHub workflows are valid."""
    root = Path(__file__).parent.parent
    workflows_dir = root / ".github" / "workflows"

    if not workflows_dir.exists():
        pytest.skip("No GitHub workflows directory")

    # Check workflow files exist
    assert (workflows_dir / "ci.yml").exists(), "ci.yml workflow missing"
    assert (workflows_dir / "security.yml").exists(), "security.yml workflow missing"

    # Check workflow content
    ci_content = (workflows_dir / "ci.yml").read_text()
    assert "pytest" in ci_content, "CI should run pytest"
    assert "ruff" in ci_content, "CI should run ruff"
    assert "black" in ci_content, "CI should run black"

    security_content = (workflows_dir / "security.yml").read_text()
    assert "gitleaks" in security_content, "Security should run gitleaks"


def test_imports_work():
    """Test that package imports work correctly."""
    # Test main package import

    # Test submodule imports
    from penin.cache import SecureCache

    # Test specific imports
    from penin.omega import phi_caos
    from penin.router import MultiLLMRouterComplete as MultiLLMRouter

    # Verify functions/classes exist
    assert callable(phi_caos)
    assert callable(MultiLLMRouter)
    assert callable(SecureCache)


def test_no_sys_path_hacks():
    """Test that there are no sys.path hacks in main code."""
    root = Path(__file__).parent.parent
    penin_dir = root / "penin"

    # Check all Python files in penin package
    for py_file in penin_dir.rglob("*.py"):
        content = py_file.read_text()

        # Skip test files
        if "test" in py_file.name:
            continue

        assert "sys.path.append" not in content, f"Found sys.path hack in {py_file}"
        assert "sys.path.insert" not in content, f"Found sys.path hack in {py_file}"


def test_cache_uses_orjson():
    """Test that cache uses orjson instead of pickle."""
    root = Path(__file__).parent.parent
    cache_file = root / "penin" / "cache.py"

    content = cache_file.read_text()

    # Check for orjson usage
    assert "import orjson" in content, "Cache should import orjson"
    assert "orjson.dumps" in content, "Cache should use orjson.dumps"
    assert "orjson.loads" in content, "Cache should use orjson.loads"

    # Check for HMAC usage
    assert "import hmac" in content, "Cache should import hmac"
    assert "hmac.new" in content, "Cache should use hmac.new"

    # Ensure no pickle usage
    assert "import pickle" not in content, "Cache should not import pickle"
    assert "pickle.dumps" not in content, "Cache should not use pickle.dumps"
    assert "pickle.loads" not in content, "Cache should not use pickle.loads"


def test_env_example_complete():
    """Test that .env.example contains all necessary variables."""
    root = Path(__file__).parent.parent
    env_example = root / ".env.example"

    content = env_example.read_text()

    # Check for essential variables
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "PENIN_BUDGET_DAILY_USD",
        "PENIN_METRICS_TOKEN",
        "PENIN_CACHE_HMAC_KEY",
    ]

    for var in required_vars:
        assert var in content, f"Missing {var} in .env.example"


def test_gitignore_comprehensive():
    """Test that .gitignore covers essential patterns."""
    root = Path(__file__).parent.parent
    gitignore = root / ".gitignore"

    content = gitignore.read_text()

    # Check for essential patterns
    patterns = [
        ".env",
        "*.db",
        "__pycache__",
        "*.pyc",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
    ]

    for pattern in patterns:
        assert pattern in content, f"Missing {pattern} in .gitignore"
