"""Test writer wrap behavior with colors."""

import pytest
from unittest.mock import Mock, call
from matrix_tui.vertical_column import SingleColumnWriter
from matrix_tui.renderer import HEAD_FG, TRAIL_FG, BG


class TestWriterWrapColors:
    """Test the wrapping behavior with color repaint."""

    def test_wrap_behavior_with_colors(self):
        """Test that wrapping preserves color rules."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 3  # Small height to force wrapping
        writer = SingleColumnWriter(mock_renderer)

        # Act - feed "ABCD" which should wrap
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("C")
        writer.on_char("D")

        # Assert - verify the complete sequence
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 7  # A, A repaint, B, B repaint, C, C repaint, D

        expected_calls = [
            call(0, 0, "A", HEAD_FG, BG),  # A in white at row 0
            call(0, 0, "A", TRAIL_FG, BG),  # A repainted green
            call(1, 0, "B", HEAD_FG, BG),  # B in white at row 1
            call(1, 0, "B", TRAIL_FG, BG),  # B repainted green
            call(2, 0, "C", HEAD_FG, BG),  # C in white at row 2
            call(2, 0, "C", TRAIL_FG, BG),  # C repainted green
            call(0, 0, "D", HEAD_FG, BG),  # D in white at row 0 (wrapped)
        ]

        for i, expected_call in enumerate(expected_calls):
            assert calls[i] == expected_call

    def test_wrap_preserves_repaint_logic(self):
        """Test that wrapping doesn't break the repaint logic."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 2  # Very small height
        writer = SingleColumnWriter(mock_renderer)

        # Act - feed "ABC" to test wrap behavior
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("C")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 5  # A, A repaint, B, B repaint, C

        # Verify positions: A at (0,0), B at (1,0), C at (0,0) (wrapped)
        assert calls[0] == call(0, 0, "A", HEAD_FG, BG)  # A in white
        assert calls[1] == call(0, 0, "A", TRAIL_FG, BG)  # A repainted green
        assert calls[2] == call(1, 0, "B", HEAD_FG, BG)  # B in white
        assert calls[3] == call(1, 0, "B", TRAIL_FG, BG)  # B repainted green
        assert calls[4] == call(0, 0, "C", HEAD_FG, BG)  # C in white (wrapped to top)

    def test_multiple_wraps(self):
        """Test behavior with multiple wraps."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 2
        writer = SingleColumnWriter(mock_renderer)

        # Act - feed "ABCDE" to get multiple wraps
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("C")
        writer.on_char("D")
        writer.on_char("E")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 9  # Each char + repaint except first

        # Verify the pattern continues correctly through wraps
        expected_positions = [
            (0, 0),  # A
            (0, 0),  # A repaint
            (1, 0),  # B
            (1, 0),  # B repaint
            (0, 0),  # C (wrapped)
            (0, 0),  # C repaint
            (1, 0),  # D
            (1, 0),  # D repaint
            (0, 0),  # E (wrapped)
        ]

        for i, (expected_row, expected_col) in enumerate(expected_positions):
            call_args = calls[i][0]
            assert call_args[0] == expected_row  # row
            assert call_args[1] == expected_col  # col

    def test_wrap_with_resize(self):
        """Test that resize maintains proper behavior after wrapping."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 3
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("C")
        writer.on_char("D")  # This wraps to row 0

        # Simulate resize
        mock_renderer.height = 5
        writer.on_resize()

        writer.on_char("E")

        # Assert - E should be at row 1 (not 0) because row was adjusted by resize
        calls = mock_renderer.draw_cell.call_args_list
        last_call = calls[-1]
        assert last_call == call(1, 0, "E", HEAD_FG, BG)  # E should be at row 1
