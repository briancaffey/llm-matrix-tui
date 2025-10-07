"""Renderer smoke tests using capsys."""

import pytest
from matrix_tui.renderer import Renderer


class TestRendererSmoke:
    """Smoke tests for Renderer functionality."""

    def test_renderer_init_draw_char_finalize(self, capsys):
        """Test basic renderer functionality: init, draw_char, finalize."""
        renderer = Renderer()

        # Initialize renderer
        renderer.init()

        # Draw a character at position (0,0)
        renderer.draw_char(0, 0, "X")

        # Finalize renderer
        renderer.finalize()

        # Capture output
        captured = capsys.readouterr()

        # The output should contain 'X' (along with escape codes)
        assert "X" in captured.out, f"Expected 'X' in output, got: {captured.out}"

    def test_renderer_dimensions_caching(self):
        """Test that renderer caches terminal dimensions."""
        renderer = Renderer()

        # Initialize to cache dimensions
        renderer.init()

        # Dimensions should be cached
        assert renderer.height > 0, "Height should be cached and positive"
        assert renderer.width > 0, "Width should be cached and positive"

    def test_refresh_dims_updates_dimensions(self):
        """Test that refresh_dims updates cached dimensions."""
        renderer = Renderer()

        # Initialize to cache initial dimensions
        renderer.init()
        original_height = renderer.height
        original_width = renderer.width

        # Refresh dimensions
        renderer.refresh_dims()

        # Dimensions should still be valid (may be same or different)
        assert renderer.height > 0, "Height should be positive after refresh"
        assert renderer.width > 0, "Width should be positive after refresh"

    def test_draw_char_updates_cursor_position(self):
        """Test that draw_char updates internal cursor position."""
        renderer = Renderer()

        # Initialize renderer
        renderer.init()

        # Draw character at specific position
        renderer.draw_char(5, 0, "Y")

        # Cursor position should be updated
        assert (
            renderer.current_x == 0
        ), f"Expected current_x=0, got {renderer.current_x}"
        assert (
            renderer.current_y == 5
        ), f"Expected current_y=5, got {renderer.current_y}"

    def test_multiple_draw_char_calls(self, capsys):
        """Test multiple draw_char calls."""
        renderer = Renderer()

        # Initialize renderer
        renderer.init()

        # Draw multiple characters
        renderer.draw_char(0, 0, "A")
        renderer.draw_char(1, 0, "B")
        renderer.draw_char(2, 0, "C")

        # Finalize renderer
        renderer.finalize()

        # Capture output
        captured = capsys.readouterr()

        # Output should contain all characters
        assert "A" in captured.out, "Expected 'A' in output"
        assert "B" in captured.out, "Expected 'B' in output"
        assert "C" in captured.out, "Expected 'C' in output"

    def test_draw_char_with_different_positions(self, capsys):
        """Test draw_char with different row/column positions."""
        renderer = Renderer()

        # Initialize renderer
        renderer.init()

        # Draw characters at different positions
        renderer.draw_char(0, 0, "1")
        renderer.draw_char(1, 0, "2")
        renderer.draw_char(0, 1, "3")  # Different column

        # Finalize renderer
        renderer.finalize()

        # Capture output
        captured = capsys.readouterr()

        # Output should contain all characters
        assert "1" in captured.out, "Expected '1' in output"
        assert "2" in captured.out, "Expected '2' in output"
        assert "3" in captured.out, "Expected '3' in output"
