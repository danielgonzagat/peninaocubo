# Contributing to PENIN-Ω

First off, thank you for considering contributing to PENIN-Ω! 🎉

This document provides guidelines for contributing to the project.

---

## 🎯 Code of Conduct

Be respectful, inclusive, and constructive. We're building something important together.

---

## 🏗️ Architecture Overview

Before contributing, **read these first**:

1. [penin/ARCHITECTURE.md](penin/ARCHITECTURE.md) - Module hierarchy
2. [README.md](README.md) - Project overview
3. Module-specific READMEs in each directory

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/peninaocubo.git
cd peninaocubo
```

### 2. Set Up Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

---

## 📝 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow our [code standards](#code-standards) below.

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_math_core.py -v

# Run with coverage
pytest --cov=penin --cov-report=term-missing
```

**Requirements**:
- All existing tests must pass
- New code must have tests (target: 85%+ coverage)
- No decrease in overall coverage

### 4. Lint and Format

```bash
# Auto-fix what's possible
ruff check . --fix
black .

# Type check
mypy penin/ --ignore-missing-imports
```

**Requirements**:
- Zero linting errors
- Code formatted with Black
- Type hints for public APIs

### 5. Commit

```bash
git add -A
git commit -m "feat: your feature description"
```

**Commit Message Format**:
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat: add neuromorphic SpikingBrain-7B integration

Implements adapter for SpikingBrain-7B with:
- Provider class
- Cost estimation
- 100× speedup validation

Closes #123
```

### 6. Push and PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## 📋 PR Checklist

Before submitting, ensure:

- [ ] All tests pass (`pytest tests/`)
- [ ] No linting errors (`ruff check .`)
- [ ] Code formatted (`black .`)
- [ ] Type hints added (`mypy penin/`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages follow convention

### For Mathematical/Ethical Changes

Also ensure:

- [ ] ΔL∞ ≥ β_min (improvement demonstrated)
- [ ] All Σ-Guard gates pass
- [ ] Ethics validation passes (ΣEA/LO-14)
- [ ] WORM ledger entry created
- [ ] PCAg (proof) attached

---

## 📚 Code Standards

### Python Version

- **Minimum**: Python 3.11+
- **Target**: Python 3.13 compatibility

### Code Style

- **Formatter**: Black (line length: 100)
- **Linter**: Ruff (with strict rules)
- **Import sorting**: isort (via Ruff)

### Type Hints

```python
# ✅ Good
def compute_score(metrics: list[float], weights: list[float]) -> float:
    """Compute weighted score."""
    return sum(m * w for m, w in zip(metrics, weights))

# ❌ Bad
def compute_score(metrics, weights):
    return sum(m * w for m, w in zip(metrics, weights))
```

### Docstrings

Use **Google style**:

```python
def function_name(param1: int, param2: str) -> bool:
    """
    Short description (one line).
    
    Longer description if needed, explaining what the function does,
    why it exists, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When params are invalid
    
    Example:
        >>> function_name(42, "test")
        True
    """
```

### File Organization

```python
# 1. Module docstring
"""Module description."""

# 2. Future imports
from __future__ import annotations

# 3. Standard library
import os
import sys

# 4. Third-party
import numpy as np
import pytest

# 5. Local
from penin.math import compute_linf_meta
from penin.core.caos import CAOSPlusEngine

# 6. Type checking (if needed)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from penin.omega import SomethingElse

# 7. Constants
DEFAULT_KAPPA = 20.0

# 8. Classes and functions
class MyClass:
    ...
```

### File Naming

- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_CASE`

### Maximum Lengths

- **Line**: 100 characters
- **Function**: ≤ 50 lines (prefer smaller)
- **Class**: ≤ 300 lines (prefer smaller)
- **File**: ≤ 1,500 lines (if larger, consider splitting)

---

## 🧪 Testing Standards

### Test Structure

```python
class TestMyFeature:
    """Test suite for MyFeature."""
    
    def test_basic_functionality(self):
        """Test basic usage."""
        result = my_function(42)
        assert result == expected
    
    def test_edge_case_empty_input(self):
        """Test with empty input."""
        with pytest.raises(ValueError, match="cannot be empty"):
            my_function([])
    
    def test_integration_with_other_module(self):
        """Test integration with other components."""
        ...
```

### Coverage Requirements

- **P0 (core)**: ≥ 85%
- **P1 (features)**: ≥ 75%
- **P2 (nice-to-have)**: ≥ 60%

### Test Types

1. **Unit tests**: `tests/test_*.py`
2. **Integration tests**: `tests/integration/test_*.py`
3. **Property-based tests**: `tests/properties/test_*.py`
4. **Chaos tests**: `tests/test_chaos_*.py`

---

## 🔒 Ethical Guidelines

All code must respect the **14 Leis Originárias** (LO-01 to LO-14):

1. **LO-01**: Anti-Idolatria (no worship of AI)
2. **LO-02**: Anti-Ocultismo (no occult practices)
3. **LO-03**: Anti-Dano Físico (no physical harm)
4. **LO-04**: Anti-Dano Emocional (no manipulation)
5. **LO-05**: Privacidade (absolute privacy respect)
6. **LO-06**: Transparência (auditable decisions)
7. **LO-07**: Consentimento (require consent)
8. **LO-08**: Autonomia (respect autonomy)
9. **LO-09**: Justiça (fairness)
10. **LO-10**: Beneficência (genuine benefit)
11. **LO-11**: Não-Maleficência (do no harm)
12. **LO-12**: Responsabilidade (accountability)
13. **LO-13**: Sustentabilidade (eco-impact)
14. **LO-14**: Humildade (recognize limits)

**No contribution** that violates these principles will be accepted.

---

## 🎯 Layer Guidelines

Know which layer you're contributing to:

| Layer | Purpose | Max Complexity |
|-------|---------|----------------|
| 1. Equations | Theory | Pure math, specs |
| 2. Math/Ethics/Guard | Implementations | Minimal dependencies |
| 3. Core/Engine | Runtime | Orchestration |
| 4. Omega | High-level | Pre-integrated APIs |
| 5. Services | REST APIs | FastAPI/async |

**Rule**: Can depend on lower layers, never higher layers.

---

## 📊 Definition of Done (DoD)

A contribution is complete when:

- [ ] Code implemented and documented
- [ ] Tests written and passing
- [ ] Linting clean
- [ ] Type hints added
- [ ] README updated (if new module)
- [ ] CHANGELOG.md updated
- [ ] PR description complete
- [ ] All checks green
- [ ] Reviewed and approved

---

## 🤝 Review Process

1. Automated checks run (CI/CD)
2. Maintainer reviews code
3. Feedback addressed
4. Approved and merged

**Timeline**: We aim to review PRs within 2-3 days.

---

## 🐛 Reporting Bugs

Use GitHub Issues with:

- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Environment (Python version, OS)
- Logs/screenshots if applicable

---

## 💡 Proposing Features

1. Check if already planned (see ROADMAP.md)
2. Open Discussion first (for big features)
3. Get feedback before implementing
4. Create PR when ready

---

## 📚 Resources

- [ARCHITECTURE.md](penin/ARCHITECTURE.md) - Module hierarchy
- [ROADMAP_EXECUTAVEL.md](ROADMAP_EXECUTAVEL.md) - Planned features
- Module READMEs - Usage guides

---

## ❓ Questions?

- **Discussions**: For questions and ideas
- **Issues**: For bugs and feature requests
- **Email**: [maintainer email if applicable]

---

**Thank you for contributing to the future of autonomous AI!** 🚀🧠✨
