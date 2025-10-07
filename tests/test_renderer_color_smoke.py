"""Test renderer color functionality with mocked terminal."""

import pytest
from unittest.mock import Mock, patch
from matrix_tui.renderer import Renderer, HEAD_FG, TRAIL_FG, BG


class TestRendererColorSmoke:
    """Test the renderer's color drawing capabilities."""

    def test_draw_cell_with_colors(self):
        """Test that draw_cell properly composes color strings."""
        # Arrange
        renderer = Renderer()

        # Mock the terminal methods
        mock_term = Mock()
        mock_term.move_yx.return_value = "\x1b[1;1H"
        mock_term.color_rgb.return_value = "\x1b[38;2;255;255;255m"
        mock_term.on_color_rgb.return_value = "\x1b[48;2;0;0;0m"
        mock_term.normal = "\x1b[0m"

        renderer.term = mock_term

        # Act
        with patch("builtins.print") as mock_print:
            renderer.draw_cell(0, 0, "X", HEAD_FG, BG)

        # Assert
        mock_term.move_yx.assert_called_once_with(0, 0)
        mock_term.color_rgb.assert_called_once_with(255, 255, 255)  # HEAD_FG
        mock_term.on_color_rgb.assert_called_once_with(0, 0, 0)  # BG
        mock_print.assert_called_once()

        # Verify the composed string
        call_args = mock_print.call_args[0][0]
        assert "\x1b[1;1H" in call_args  # move_yx
        assert "\x1b[38;2;255;255;255m" in call_args  # color_rgb
        assert "\x1b[48;2;0;0;0m" in call_args  # on_color_rgb
        assert "X" in call_args  # character
        assert "\x1b[0m" in call_args  # normal

    def test_draw_cell_with_trail_colors(self):
        """Test draw_cell with trail colors."""
        # Arrange
        renderer = Renderer()

        mock_term = Mock()
        mock_term.move_yx.return_value = "\x1b[2;1H"
        mock_term.color_rgb.return_value = "\x1b[38;2;118;185;0m"
        mock_term.on_color_rgb.return_value = "\x1b[48;2;0;0;0m"
        mock_term.normal = "\x1b[0m"

        renderer.term = mock_term

        # Act
        with patch("builtins.print") as mock_print:
            renderer.draw_cell(1, 0, "Y", TRAIL_FG, BG)

        # Assert
        mock_term.color_rgb.assert_called_once_with(118, 185, 0)  # TRAIL_FG
        mock_term.on_color_rgb.assert_called_once_with(0, 0, 0)  # BG

    def test_color_fallback_when_truecolor_unsupported(self):
        """Test that color fallback works when truecolor is not supported."""
        # Arrange
        renderer = Renderer()

        mock_term = Mock()
        mock_term.move_yx.return_value = "\x1b[1;1H"
        mock_term.color_rgb.side_effect = Exception("Truecolor not supported")
        mock_term.color.return_value = "\x1b[38;5;15m"  # Fallback color
        mock_term.on_color_rgb.side_effect = Exception("Truecolor not supported")
        mock_term.on_color.return_value = "\x1b[48;5;0m"  # Fallback background
        mock_term.normal = "\x1b[0m"

        renderer.term = mock_term

        # Act
        with patch("builtins.print") as mock_print:
            renderer.draw_cell(0, 0, "Z", HEAD_FG, BG)

        # Assert
        mock_term.color_rgb.assert_called_once()
        mock_term.color.assert_called_once()  # Fallback was used
        mock_term.on_color_rgb.assert_called_once()
        mock_term.on_color.assert_called_once()  # Fallback was used

    def test_supports_truecolor_detection(self):
        """Test the supports_truecolor method."""
        # Arrange
        renderer = Renderer()

        # Test with truecolor support
        mock_term_with_truecolor = Mock()
        mock_term_with_truecolor.color_rgb = Mock()
        mock_term_with_truecolor.on_color_rgb = Mock()
        renderer.term = mock_term_with_truecolor

        # Act & Assert
        assert renderer.supports_truecolor() is True

        # Test without truecolor support
        mock_term_without_truecolor = Mock()
        del mock_term_without_truecolor.color_rgb
        del mock_term_without_truecolor.on_color_rgb
        renderer.term = mock_term_without_truecolor

        # Act & Assert
        assert renderer.supports_truecolor() is False

    def test_color_constants_are_correct(self):
        """Test that color constants have the expected values."""
        # Assert
        assert HEAD_FG == (255, 255, 255)  # White
        assert TRAIL_FG == (118, 185, 0)  # NVIDIA green #76b900
        assert BG == (0, 0, 0)  # Black

    def test_draw_cell_updates_cursor_position(self):
        """Test that draw_cell updates the internal cursor position."""
        # Arrange
        renderer = Renderer()

        mock_term = Mock()
        mock_term.move_yx.return_value = "\x1b[5;3H"
        mock_term.color_rgb.return_value = ""
        mock_term.on_color_rgb.return_value = ""
        mock_term.normal = ""

        renderer.term = mock_term

        # Act
        with patch("builtins.print"):
            renderer.draw_cell(5, 3, "W", HEAD_FG, BG)

        # Assert
        assert renderer.current_x == 3
        assert renderer.current_y == 5

    def test_color_conversion_helpers(self):
        """Test the internal color conversion helper methods."""
        # Arrange
        renderer = Renderer()

        mock_term = Mock()
        mock_term.color_rgb.return_value = "\x1b[38;2;100;150;200m"
        mock_term.on_color_rgb.return_value = "\x1b[48;2;50;75;100m"

        renderer.term = mock_term

        # Act
        fg_result = renderer._to_term_color((100, 150, 200))
        bg_result = renderer._to_term_bg((50, 75, 100))

        # Assert
        assert fg_result == "\x1b[38;2;100;150;200m"
        assert bg_result == "\x1b[48;2;50;75;100m"
        mock_term.color_rgb.assert_called_once_with(100, 150, 200)
        mock_term.on_color_rgb.assert_called_once_with(50, 75, 100)
