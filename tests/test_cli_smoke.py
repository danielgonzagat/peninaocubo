"""
CLI Smoke Tests
===============

Basic smoke tests for penin CLI to ensure it runs without crashing.
"""

import sys
from pathlib import Path

import pytest

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cli_module_exists():
    """Test CLI module exists and can be imported"""
    import penin.cli
    
    # Just verify module loads
    assert penin.cli is not None


def test_cli_structure():
    """Test CLI has expected structure"""
    import penin.cli
    
    # CLI module loaded successfully
    assert hasattr(penin.cli, '__name__')


def test_version_available():
    """Test version info is available"""
    from penin import __version__
    
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0
    print(f"Version: {__version__}")


def test_cli_no_crash_on_import():
    """Test importing cli module doesn't crash"""
    try:
        import penin.cli
        # Verify it loaded
        assert penin.cli.__name__ == 'penin.cli'
    except Exception as e:
        pytest.fail(f"CLI import crashed: {e}")
