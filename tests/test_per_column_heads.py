"""Test per-column independence in rendering."""

import pytest
from unittest.mock import Mock, call
from matrix_tui.vertical_column import ColumnWriter
from matrix_tui.renderer import HEAD_FG, TRAIL_FG, BG


@pytest.fixture
def mock_renderer():
    """Create a mock renderer with color properties."""
    renderer = Mock()
    renderer.height = 5
    renderer.width = 10
    renderer.head_color = HEAD_FG
    renderer.trail_color = TRAIL_FG
    renderer.background_color = BG
    return renderer


def test_per_column_independence(mock_renderer):
    """Test that two writers operate independently."""
    # Create two writers at different columns
    writer0 = ColumnWriter(mock_renderer, 0)
    writer1 = ColumnWriter(mock_renderer, 1)

    # Feed characters to writer 0
    writer0.on_char("A")
    writer0.on_char("B")

    # Feed characters to writer 1
    writer1.on_char("X")
    writer1.on_char("Y")

    # Verify writer 0 calls
    expected_calls_0 = [
        # First char 'A' at (0, 0) with white
        call(0, 0, "A", HEAD_FG, BG),
        # Second char 'B' at (1, 0) with white, repaint 'A' to green
        call(0, 0, "A", TRAIL_FG, BG),
        call(1, 0, "B", HEAD_FG, BG),
    ]

    # Verify writer 1 calls
    expected_calls_1 = [
        # First char 'X' at (0, 1) with white
        call(0, 1, "X", HEAD_FG, BG),
        # Second char 'Y' at (1, 1) with white, repaint 'X' to green
        call(0, 1, "X", TRAIL_FG, BG),
        call(1, 1, "Y", HEAD_FG, BG),
    ]

    # Check that draw_cell was called with correct parameters
    all_calls = mock_renderer.draw_cell.call_args_list

    # Verify writer 0 calls are present
    assert call(0, 0, "A", HEAD_FG, BG) in all_calls
    assert call(0, 0, "A", TRAIL_FG, BG) in all_calls
    assert call(1, 0, "B", HEAD_FG, BG) in all_calls

    # Verify writer 1 calls are present
    assert call(0, 1, "X", HEAD_FG, BG) in all_calls
    assert call(0, 1, "X", TRAIL_FG, BG) in all_calls
    assert call(1, 1, "Y", HEAD_FG, BG) in all_calls

    # Verify writers have correct internal state
    assert writer0.row == 2  # After 2 chars, row should be 2
    assert writer0.col == 0
    assert writer0.last_pos == (1, 0)
    assert writer0.last_char == "B"

    assert writer1.row == 2  # After 2 chars, row should be 2
    assert writer1.col == 1
    assert writer1.last_pos == (1, 1)
    assert writer1.last_char == "Y"


def test_column_wrapping_independence(mock_renderer):
    """Test that column wrapping works independently."""
    # Create writers at different columns
    writer0 = ColumnWriter(mock_renderer, 0)
    writer1 = ColumnWriter(mock_renderer, 1)

    # Fill writer 0 to wrap around (height=5)
    for i in range(6):  # 0,1,2,3,4,0
        writer0.on_char("A")

    # Fill writer 1 to wrap around
    for i in range(6):  # 0,1,2,3,4,0
        writer1.on_char("B")

    # Both should be at row 1 after wrapping (6 chars with height=5: 0,1,2,3,4,0,1)
    assert writer0.row == 1
    assert writer1.row == 1

    # But at different columns
    assert writer0.col == 0
    assert writer1.col == 1


def test_skip_newlines_independence(mock_renderer):
    """Test that newlines are skipped independently per column."""
    writer0 = ColumnWriter(mock_renderer, 0)
    writer1 = ColumnWriter(mock_renderer, 1)

    # Feed characters with newlines
    writer0.on_char("A")
    writer0.on_char("\n")  # Should be skipped
    writer0.on_char("B")

    writer1.on_char("X")
    writer1.on_char("\r")  # Should be skipped
    writer1.on_char("Y")

    # Verify newlines didn't affect row positions
    assert writer0.row == 2  # A at 0, B at 1
    assert writer1.row == 2  # X at 0, Y at 1

    # Verify last characters are correct
    assert writer0.last_char == "B"
    assert writer1.last_char == "Y"
