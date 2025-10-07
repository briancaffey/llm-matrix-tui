"""Basic tests for Matrix Rain TUI setup verification."""

import pytest
import matrix_tui


def test_basic_import():
    """Test that the matrix_tui module can be imported."""
    assert hasattr(matrix_tui, "__version__")
    assert matrix_tui.__version__ == "0.0.2"


def test_main_module_exists():
    """Test that the main module can be imported."""
    from matrix_tui import __main__

    assert hasattr(__main__, "main")
    assert callable(__main__.main)


def test_environment_setup():
    """Test that basic environment setup works."""
    # This test verifies that the project structure is correct
    import os
    import sys

    # Check that src is in Python path (configured in pyproject.toml)
    assert any("src" in path for path in sys.path)

    # Check that we can access the module
    assert matrix_tui is not None
