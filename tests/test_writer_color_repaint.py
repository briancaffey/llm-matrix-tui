"""Test writer color repaint logic with mocked renderer."""

import pytest
from unittest.mock import Mock, call
from matrix_tui.vertical_column import SingleColumnWriter
from matrix_tui.renderer import HEAD_FG, TRAIL_FG, BG


class TestWriterColorRepaint:
    """Test the color repaint behavior of SingleColumnWriter."""

    def test_first_character_draws_white(self):
        """Test that the first character is drawn with white foreground."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")

        # Assert
        mock_renderer.draw_cell.assert_called_once_with(0, 0, "A", HEAD_FG, BG)

    def test_second_character_repaints_first_then_draws_new(self):
        """Test that second character repaints first as green, then draws new as white."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("B")

        # Assert - should have 3 calls total: A (white), A repaint (green), B (white)
        expected_calls = [
            call(0, 0, "A", HEAD_FG, BG),  # First A in white
            call(0, 0, "A", TRAIL_FG, BG),  # Repaint A in green
            call(1, 0, "B", HEAD_FG, BG),  # B in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)
        assert mock_renderer.draw_cell.call_count == 3

    def test_sequence_ab_correct_order(self):
        """Test the exact sequence for characters A and B."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("B")

        # Assert - verify exact call sequence
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 3

        # First call: A in white
        assert calls[0] == call(0, 0, "A", HEAD_FG, BG)

        # Second call: A repainted in green
        assert calls[1] == call(0, 0, "A", TRAIL_FG, BG)

        # Third call: B in white
        assert calls[2] == call(1, 0, "B", HEAD_FG, BG)

    def test_three_characters_sequence(self):
        """Test repaint behavior with three characters."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("C")

        # Assert - should have 5 calls total (A, A repaint, B, B repaint, C)
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 5

        # Verify the pattern: each new char causes repaint of previous + new draw
        expected_calls = [
            call(0, 0, "A", HEAD_FG, BG),  # A in white
            call(0, 0, "A", TRAIL_FG, BG),  # A repainted green
            call(1, 0, "B", HEAD_FG, BG),  # B in white
            call(1, 0, "B", TRAIL_FG, BG),  # B repainted green
            call(2, 0, "C", HEAD_FG, BG),  # C in white
        ]

        for i, expected_call in enumerate(expected_calls):
            assert calls[i] == expected_call

    def test_skip_control_characters(self):
        """Test that newline and carriage return are skipped."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("\n")  # Should be skipped
        writer.on_char("B")
        writer.on_char("\r")  # Should be skipped
        writer.on_char("C")

        # Assert - only A, B, C should be drawn (no calls for \n or \r)
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 5  # A, A repaint, B, B repaint, C

        # Verify no calls contain newline or carriage return
        for call_args in calls:
            char = call_args[0][2]  # Third argument is the character
            assert char not in {"\n", "\r"}

    def test_empty_string_skipped(self):
        """Test that empty strings are skipped."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("")  # Should be skipped
        writer.on_char("B")

        # Assert - only A and B should be drawn
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 3  # A, A repaint, B

        # Verify no calls contain empty string
        for call_args in calls:
            char = call_args[0][2]  # Third argument is the character
            assert char != ""
