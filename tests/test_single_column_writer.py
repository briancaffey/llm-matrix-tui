"""Unit tests for SingleColumnWriter logic (no blessed I/O)."""

import pytest
from unittest.mock import Mock
from matrix_tui.vertical_column import SingleColumnWriter
from matrix_tui.renderer import HEAD_FG, TRAIL_FG, BG


class TestSingleColumnWriter:
    """Test cases for SingleColumnWriter functionality."""

    def test_basic_character_writing(self):
        """Test basic character writing with wrap-around behavior."""
        # Mock renderer with height=5
        mock_renderer = Mock()
        mock_renderer.height = 5
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Feed "ABCDE" via on_char loop
        test_chars = "ABCDE"
        for char in test_chars:
            writer.on_char(char)

        # Expect draw_cell calls: A (white), A repaint (green), B (white), B repaint (green), C (white), C repaint (green), D (white), D repaint (green), E (white)
        expected_calls = [
            ((0, 0, "A", HEAD_FG, BG), {}),  # A in white
            ((0, 0, "A", TRAIL_FG, BG), {}),  # A repainted green
            ((1, 0, "B", HEAD_FG, BG), {}),  # B in white
            ((1, 0, "B", TRAIL_FG, BG), {}),  # B repainted green
            ((2, 0, "C", HEAD_FG, BG), {}),  # C in white
            ((2, 0, "C", TRAIL_FG, BG), {}),  # C repainted green
            ((3, 0, "D", HEAD_FG, BG), {}),  # D in white
            ((3, 0, "D", TRAIL_FG, BG), {}),  # D repainted green
            ((4, 0, "E", HEAD_FG, BG), {}),  # E in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    def test_wrap_around_behavior(self):
        """Test that characters wrap to top when reaching bottom."""
        # Mock renderer with height=3
        mock_renderer = Mock()
        mock_renderer.height = 3
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Feed "ABCDE" - should wrap after 3 characters
        test_chars = "ABCDE"
        for char in test_chars:
            writer.on_char(char)

        # Expect draw_cell calls with wrapping: A (white), A repaint (green), B (white), B repaint (green), C (white), C repaint (green), D (white), D repaint (green), E (white)
        expected_calls = [
            ((0, 0, "A", HEAD_FG, BG), {}),  # A in white
            ((0, 0, "A", TRAIL_FG, BG), {}),  # A repainted green
            ((1, 0, "B", HEAD_FG, BG), {}),  # B in white
            ((1, 0, "B", TRAIL_FG, BG), {}),  # B repainted green
            ((2, 0, "C", HEAD_FG, BG), {}),  # C in white
            ((2, 0, "C", TRAIL_FG, BG), {}),  # C repainted green
            ((0, 0, "D", HEAD_FG, BG), {}),  # D in white (wrapped)
            ((0, 0, "D", TRAIL_FG, BG), {}),  # D repainted green
            ((1, 0, "E", HEAD_FG, BG), {}),  # E in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    def test_skip_newline_and_carriage_return(self):
        """Test that newline and carriage return characters are skipped."""
        # Mock renderer with height=5
        mock_renderer = Mock()
        mock_renderer.height = 5
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Feed "AB\nC\rD" - newline/carriage should be skipped
        test_chars = "AB\nC\rD"
        for char in test_chars:
            writer.on_char(char)

        # Expect only A, B, C, D to be drawn (skipping \n and \r) with color repaint
        expected_calls = [
            ((0, 0, "A", HEAD_FG, BG), {}),  # A in white
            ((0, 0, "A", TRAIL_FG, BG), {}),  # A repainted green
            ((1, 0, "B", HEAD_FG, BG), {}),  # B in white
            ((1, 0, "B", TRAIL_FG, BG), {}),  # B repainted green
            ((2, 0, "C", HEAD_FG, BG), {}),  # C in white
            ((2, 0, "C", TRAIL_FG, BG), {}),  # C repainted green
            ((3, 0, "D", HEAD_FG, BG), {}),  # D in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    def test_resize_handling(self):
        """Test resize handling updates dimensions and adjusts row position."""
        # Mock renderer with initial height=5
        mock_renderer = Mock()
        mock_renderer.height = 5
        mock_renderer.draw_cell = Mock()
        mock_renderer.refresh_dims = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Write some characters to get to row 3
        for char in "ABC":
            writer.on_char(char)

        # Simulate resize to height=3
        mock_renderer.height = 3
        writer.on_resize()

        # Verify refresh_dims was called
        mock_renderer.refresh_dims.assert_called_once()

        # Continue writing - should wrap properly with new height
        writer.on_char("D")
        writer.on_char("E")

        # Expect calls: A(0), B(1), C(2), resize, D(0), E(1) with color repaint
        expected_calls = [
            ((0, 0, "A", HEAD_FG, BG), {}),  # A in white
            ((0, 0, "A", TRAIL_FG, BG), {}),  # A repainted green
            ((1, 0, "B", HEAD_FG, BG), {}),  # B in white
            ((1, 0, "B", TRAIL_FG, BG), {}),  # B repainted green
            ((2, 0, "C", HEAD_FG, BG), {}),  # C in white
            ((2, 0, "C", TRAIL_FG, BG), {}),  # C repainted green
            ((0, 0, "D", HEAD_FG, BG), {}),  # D in white (after resize, wraps to 0)
            ((0, 0, "D", TRAIL_FG, BG), {}),  # D repainted green
            ((1, 0, "E", HEAD_FG, BG), {}),  # E in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    def test_column_fixed_at_zero(self):
        """Test that column is always fixed at 0."""
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.height = 10
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Write several characters
        for char in "HELLO":
            writer.on_char(char)

        # All calls should have col=0
        for call in mock_renderer.draw_cell.call_args_list:
            args, kwargs = call
            row, col, char, fg_color, bg_color = args
            assert col == 0, f"Expected col=0, got col={col}"

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.height = 5
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Feed empty string
        writer.on_char("")

        # Should not call draw_cell
        mock_renderer.draw_cell.assert_not_called()

    def test_single_character_handling(self):
        """Test handling of single character."""
        # Mock renderer
        mock_renderer = Mock()
        mock_renderer.height = 5
        mock_renderer.draw_cell = Mock()

        writer = SingleColumnWriter(mock_renderer)

        # Feed single character
        writer.on_char("X")

        # Should call draw_cell once with white color
        mock_renderer.draw_cell.assert_called_once_with(0, 0, "X", HEAD_FG, BG)
