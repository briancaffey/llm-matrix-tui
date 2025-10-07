"""Test CLI parsing for --columns flag."""

import pytest
import sys
from unittest.mock import patch
from matrix_tui.__main__ import parse_args


def test_cli_default_columns():
    """Test that default columns is 1 when no flag is provided."""
    with patch.object(sys, "argv", ["matrix-tui"]):
        args = parse_args()
        assert args.columns == 1


def test_cli_columns_flag():
    """Test that --columns flag is parsed correctly."""
    with patch.object(sys, "argv", ["matrix-tui", "--columns", "5"]):
        args = parse_args()
        assert args.columns == 5


def test_cli_columns_short_flag():
    """Test that -c short flag is parsed correctly."""
    with patch.object(sys, "argv", ["matrix-tui", "-c", "3"]):
        args = parse_args()
        assert args.columns == 3


def test_cli_columns_zero():
    """Test that --columns 0 is parsed but will be validated in main()."""
    with patch.object(sys, "argv", ["matrix-tui", "--columns", "0"]):
        args = parse_args()
        assert args.columns == 0
