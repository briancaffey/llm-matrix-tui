"""Test writer behavior with control characters and colors."""

import pytest
from unittest.mock import Mock, call
from matrix_tui.vertical_column import SingleColumnWriter
from matrix_tui.renderer import HEAD_FG, TRAIL_FG, BG


class TestWriterSkipNewlinesColors:
    """Test that control characters are properly skipped while maintaining color logic."""

    def test_skip_newlines_between_printable_chars(self):
        """Test that newlines between printable chars don't break repaint logic."""
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

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 5  # A, A repaint, B, B repaint, C

        # Verify the sequence is correct despite skipped chars
        expected_calls = [
            call(0, 0, "A", HEAD_FG, BG),  # A in white
            call(0, 0, "A", TRAIL_FG, BG),  # A repainted green
            call(1, 0, "B", HEAD_FG, BG),  # B in white
            call(1, 0, "B", TRAIL_FG, BG),  # B repainted green
            call(2, 0, "C", HEAD_FG, BG),  # C in white
        ]

        for i, expected_call in enumerate(expected_calls):
            assert calls[i] == expected_call

    def test_skip_multiple_control_chars(self):
        """Test skipping multiple consecutive control characters."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("\n")
        writer.on_char("\r")
        writer.on_char("\n")
        writer.on_char("B")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 3  # A, A repaint, B

        # Verify only A and B were drawn
        assert calls[0] == call(0, 0, "A", HEAD_FG, BG)
        assert calls[1] == call(0, 0, "A", TRAIL_FG, BG)
        assert calls[2] == call(1, 0, "B", HEAD_FG, BG)

    def test_control_chars_at_start(self):
        """Test that control characters at the start are properly skipped."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("\n")
        writer.on_char("\r")
        writer.on_char("A")
        writer.on_char("B")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 3  # A, A repaint, B

        # Verify A and B were drawn correctly
        assert calls[0] == call(0, 0, "A", HEAD_FG, BG)
        assert calls[1] == call(0, 0, "A", TRAIL_FG, BG)
        assert calls[2] == call(1, 0, "B", HEAD_FG, BG)

    def test_control_chars_at_end(self):
        """Test that control characters at the end don't affect the sequence."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("B")
        writer.on_char("\n")
        writer.on_char("\r")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 3  # A, A repaint, B

        # Verify only A and B were drawn
        assert calls[0] == call(0, 0, "A", HEAD_FG, BG)
        assert calls[1] == call(0, 0, "A", TRAIL_FG, BG)
        assert calls[2] == call(1, 0, "B", HEAD_FG, BG)

    def test_mixed_printable_and_control_chars(self):
        """Test complex sequence with mixed printable and control characters."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("\n")
        writer.on_char("B")
        writer.on_char("\r")
        writer.on_char("C")
        writer.on_char("\n")
        writer.on_char("D")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 7  # A, A repaint, B, B repaint, C, C repaint, D

        # Verify the sequence
        expected_calls = [
            call(0, 0, "A", HEAD_FG, BG),  # A in white
            call(0, 0, "A", TRAIL_FG, BG),  # A repainted green
            call(1, 0, "B", HEAD_FG, BG),  # B in white
            call(1, 0, "B", TRAIL_FG, BG),  # B repainted green
            call(2, 0, "C", HEAD_FG, BG),  # C in white
            call(2, 0, "C", TRAIL_FG, BG),  # C repainted green
            call(3, 0, "D", HEAD_FG, BG),  # D in white
        ]

        for i, expected_call in enumerate(expected_calls):
            assert calls[i] == expected_call

    def test_empty_strings_skipped(self):
        """Test that empty strings are properly skipped."""
        # Arrange
        mock_renderer = Mock()
        mock_renderer.height = 5
        writer = SingleColumnWriter(mock_renderer)

        # Act
        writer.on_char("A")
        writer.on_char("")
        writer.on_char("B")
        writer.on_char("")
        writer.on_char("C")

        # Assert
        calls = mock_renderer.draw_cell.call_args_list
        assert len(calls) == 5  # A, A repaint, B, B repaint, C

        # Verify only printable characters were drawn
        for call_args in calls:
            char = call_args[0][2]  # Third argument is the character
            assert char in {"A", "B", "C"}  # Only printable chars
