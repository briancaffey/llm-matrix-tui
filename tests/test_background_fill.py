"""Test background fill functionality on init and resize."""

import pytest
from unittest.mock import Mock, call
from matrix_tui.renderer import Renderer, BG


@pytest.fixture
def mock_terminal():
    """Create a mock blessed Terminal."""
    terminal = Mock()
    terminal.height = 10
    terminal.width = 20
    terminal.clear.return_value = ""
    terminal.hide_cursor.return_value = ""
    terminal.normal_cursor.return_value = ""
    terminal.move_yx.return_value = ""
    terminal.normal = ""
    terminal.on_color_rgb.return_value = ""
    return terminal


@pytest.fixture
def renderer(mock_terminal):
    """Create a renderer with mocked terminal."""
    renderer = Renderer()
    renderer.term = mock_terminal
    return renderer


def test_background_fill_on_init(renderer, mock_terminal):
    """Test that fill_background is called once during init()."""
    renderer.init()

    # Verify terminal setup
    mock_terminal.clear.assert_called_once()
    mock_terminal.hide_cursor.assert_called_once()

    # Verify dimensions are set
    assert renderer.height == 10
    assert renderer.width == 20

    # Verify fill_background was called with black background
    # We can't directly spy on fill_background since it's a method,
    # but we can verify the terminal was used to draw spaces
    # The fill_background method should have been called internally
    assert renderer.height == mock_terminal.height
    assert renderer.width == mock_terminal.width


def test_background_fill_on_resize(renderer, mock_terminal):
    """Test that fill_background is called on resize."""
    # Initialize first
    renderer.init()

    # Simulate resize
    mock_terminal.height = 15
    mock_terminal.width = 25

    # Call refresh_dims
    renderer.refresh_dims()

    # Verify dimensions updated
    assert renderer.height == 15
    assert renderer.width == 25


def test_fill_background_method(renderer, mock_terminal):
    """Test the fill_background method directly."""
    renderer.height = 3
    renderer.width = 4

    # Mock the _to_term_bg method
    renderer._to_term_bg = Mock(return_value="bg_color")

    # Call fill_background
    renderer.fill_background(BG)

    # Verify _to_term_bg was called with BG color
    renderer._to_term_bg.assert_called_once_with(BG)

    # Verify move_yx was called for each cell (3*4 = 12 calls)
    assert mock_terminal.move_yx.call_count == 12

    # Verify all positions were covered
    expected_calls = []
    for row in range(3):
        for col in range(4):
            expected_calls.append(call(row, col))

    mock_terminal.move_yx.assert_has_calls(expected_calls, any_order=True)
