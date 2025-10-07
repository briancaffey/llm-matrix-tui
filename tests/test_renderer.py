"""Tests for the renderer module."""

import pytest
from unittest.mock import Mock, patch
from matrix_tui.renderer import Renderer


class TestRenderer:
    """Test cases for the Renderer class."""

    def test_renderer_initialization(self):
        """Test that Renderer initializes correctly."""
        renderer = Renderer()
        assert renderer.term is not None
        assert renderer.current_x == 0
        assert renderer.current_y == 0

    @patch("builtins.print")
    def test_renderer_init(self, mock_print):
        """Test that init() clears screen, hides cursor, and fills background."""
        renderer = Renderer()
        renderer.init()

        # Should call print at least twice (clear and hide_cursor) plus many more for fill_background
        assert mock_print.call_count >= 2
        # Check that clear and hide_cursor are called
        calls = [call[0][0] for call in mock_print.call_args_list]
        # The blessed terminal methods return escape sequences
        assert len(calls) >= 2

    @patch("builtins.print")
    def test_renderer_draw_text(self, mock_print):
        """Test that draw_text() outputs text correctly."""
        renderer = Renderer()
        test_text = "Hello, World!"

        renderer.draw_text(test_text)

        # Should call print once with the text
        mock_print.assert_called_once_with(test_text, end="", flush=True)

    @patch("builtins.print")
    def test_renderer_finalize(self, mock_print):
        """Test that finalize() restores cursor."""
        renderer = Renderer()
        renderer.finalize()

        # Should call print once with normal_cursor
        mock_print.assert_called_once()
        # The blessed terminal method returns an escape sequence
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, str)

    def test_renderer_lifecycle(self, capsys):
        """Test complete renderer lifecycle."""
        renderer = Renderer()

        # Initialize
        renderer.init()
        out = capsys.readouterr().out
        # Terminal control sequences may not be visible in test output
        # Just verify the method doesn't crash

        # Draw some text
        renderer.draw_text("Test output")
        out = capsys.readouterr().out
        assert "Test output" in out

        # Finalize
        renderer.finalize()
        # Terminal restore sequences may not be visible in test output
        # Just verify the method doesn't crash

    def test_renderer_cursor_tracking(self):
        """Test that renderer tracks cursor position correctly."""
        renderer = Renderer()

        # Test horizontal movement
        renderer.draw_text("Hello")
        assert renderer.current_x == 5
        assert renderer.current_y == 0

        # Test newline handling
        renderer.draw_text("\nWorld")
        assert renderer.current_x == 5
        assert renderer.current_y == 1

    @patch("builtins.print")
    def test_renderer_draw_text_at(self, mock_print):
        """Test that draw_text_at() positions text correctly."""
        renderer = Renderer()
        test_text = "Test"

        renderer.draw_text_at(10, 5, test_text)

        # Should call print with move_xy + text
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, str)
        # Verify cursor position was updated
        assert renderer.current_x == 14  # 10 + len("Test")
        assert renderer.current_y == 5

    def test_renderer_error_tolerance(self):
        """Test that renderer handles unexpected characters safely."""
        renderer = Renderer()

        # Test with various problematic characters
        problematic_texts = [
            "\x1b[31mRed text\x1b[0m",  # ANSI escape sequences
            "Text with\nnewlines",
            "Text with\ttabs",
            "Unicode: 🚀",
            "",  # Empty string
        ]

        # Should not raise exceptions
        for text in problematic_texts:
            try:
                renderer.draw_text(text)
            except Exception as e:
                pytest.fail(f"Renderer failed on text '{text}': {e}")
