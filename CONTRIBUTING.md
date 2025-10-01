# Contributing to PENIN-Ω

Thank you for your interest in contributing to PENIN-Ω! This document provides guidelines and instructions for contributing to the project.

## 🌟 Ways to Contribute

- **Bug Reports**: Submit detailed bug reports with reproducible examples
- **Feature Requests**: Propose new features with clear use cases
- **Code Contributions**: Submit pull requests with improvements or fixes
- **Documentation**: Improve or expand documentation
- **Testing**: Add or improve test coverage
- **Reviews**: Review pull requests from other contributors

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of async Python and FastAPI

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/<your-username>/penin-omega.git
cd penin-omega
```

2. **Create a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev,full]"
```

4. **Run tests to verify setup**

```bash
pytest tests/ -v
```

## 📝 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or improvements

### 2. Make Changes

- Write clean, readable code following project conventions
- Add or update tests for your changes
- Update documentation as needed
- Follow the code style guidelines (see below)

### 3. Run Tests and Linters

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=penin --cov-report=html tests/

# Run linters
ruff check .
black --check .
mypy penin/

# Auto-format code
black .
ruff check --fix .
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for XYZ provider"
# or
git commit -m "fix: resolve race condition in WORM ledger"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference to related issues
- Summary of changes
- Any breaking changes noted

## 🎨 Code Style Guidelines

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 120)
- Use Ruff for linting
- Use type hints for all functions
- Write docstrings for public APIs

Example:

```python
async def calculate_caos_score(
    metrics: Dict[str, float],
    boost: float = 0.0,
    *,
    use_ewma: bool = True
) -> float:
    """
    Calculate CAOS+ score with optional boost.

    Args:
        metrics: Dictionary of metric values
        boost: Boost factor (0.0 to 0.05)
        use_ewma: Whether to use EWMA smoothing

    Returns:
        Computed CAOS+ score between 0.0 and 1.0

    Raises:
        ValueError: If boost exceeds maximum allowed value
    """
    if boost > 0.05:
        raise ValueError(f"Boost {boost} exceeds maximum 0.05")
    
    # Implementation here
    ...
```

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases and error conditions

Example:

```python
import pytest
from penin.engine.caos_plus import calculate_caos_score

def test_caos_score_without_boost():
    """Test CAOS+ calculation without boost."""
    metrics = {"quality": 0.8, "diversity": 0.7}
    score = calculate_caos_score(metrics)
    assert 0.0 <= score <= 1.0

def test_caos_score_with_invalid_boost():
    """Test that excessive boost raises ValueError."""
    metrics = {"quality": 0.8}
    with pytest.raises(ValueError, match="exceeds maximum"):
        calculate_caos_score(metrics, boost=0.1)

@pytest.mark.asyncio
async def test_async_caos_calculation():
    """Test async CAOS+ calculation."""
    result = await async_calculate_caos(...)
    assert result.success is True
```

### Documentation

- Use Google-style docstrings
- Document all public APIs
- Include examples in docstrings where helpful
- Update README.md for user-facing changes
- Keep docs/ directory up to date

## 🏗️ Project Architecture

### Core Principles

1. **Fail-Closed Design**: All gates default to safe state
2. **Deterministic Behavior**: Same seed = same results
3. **Auditability**: All decisions logged to WORM ledger
4. **Non-Compensatory Gates**: All requirements must pass
5. **Loose Coupling**: Services communicate via well-defined APIs

### Key Components

- **Engine**: Core evolution logic (Master Equation, CAOS+, Fibonacci)
- **Omega**: Advanced modules (scoring, tuning, ethics)
- **Services**: Microservices (Guard, SR, Meta, League)
- **Ledger**: WORM audit trail with Merkle proofs
- **Router**: Cost-aware LLM provider selection

## 🔒 Security Guidelines

- Never commit secrets or API keys
- Use environment variables for sensitive configuration
- Validate all external inputs
- Follow fail-closed principles
- Report security issues privately (see SECURITY.md)

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest tests/`)
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No linter errors (`ruff check .`)
- [ ] Code formatted (`black .`)
- [ ] Type hints added (`mypy penin/`)
- [ ] Commit messages are clear
- [ ] PR description is complete
- [ ] No breaking changes (or clearly documented)

## 🐛 Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Minimal example to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: Python version, OS, package versions
6. **Logs**: Relevant error messages or stack traces

## 💡 Feature Requests

When proposing features, include:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Impact**: Who benefits from this feature?
5. **Implementation**: High-level implementation plan (optional)

## 📞 Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Examples**: See `examples/` directory

## 🎯 Priority Areas

We're especially interested in contributions for:

- [ ] Additional LLM provider integrations
- [ ] Enhanced observability and monitoring
- [ ] Performance optimizations
- [ ] Kubernetes deployment manifests
- [ ] Extended test coverage
- [ ] Documentation improvements
- [ ] Real-world usage examples

## 📜 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Help create a welcoming community

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project documentation (with permission)

## 📚 Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

---

Thank you for contributing to PENIN-Ω! 🚀
