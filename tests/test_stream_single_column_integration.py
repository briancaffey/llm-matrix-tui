"""Integration tests for stream callback with mocked LLM."""

import pytest
from unittest.mock import Mock, AsyncMock
from matrix_tui.llm import LLMClient
from matrix_tui.renderer import Renderer, HEAD_FG, TRAIL_FG, BG
from matrix_tui.vertical_column import SingleColumnWriter


def create_mock_renderer(height=10):
    """Create a mock renderer with color properties set."""
    mock_renderer = Mock()
    mock_renderer.height = height
    mock_renderer.draw_cell = Mock()
    mock_renderer.head_color = HEAD_FG
    mock_renderer.trail_color = TRAIL_FG
    mock_renderer.background_color = BG
    return mock_renderer


class TestStreamSingleColumnIntegration:
    """Integration tests for streaming with SingleColumnWriter."""

    @pytest.mark.asyncio
    async def test_stream_fragment_processing(self):
        """Test that stream fragments are processed character by character."""
        # Mock renderer
        mock_renderer = create_mock_renderer(height=10)

        # Create writer
        writer = SingleColumnWriter(mock_renderer)

        # Mock LLM client
        mock_client = Mock(spec=LLMClient)

        # Create mock response that yields fragments "He" then "llo"
        async def mock_stream_response(system, user, on_fragment):
            await on_fragment("He")
            await on_fragment("llo")

        mock_client.stream_response = AsyncMock(side_effect=mock_stream_response)

        # Define fragment callback that processes each character
        async def on_fragment(fragment: str):
            """Process each fragment by iterating through characters."""
            for char in fragment:
                writer.on_char(char)

        # Call the mocked stream
        await mock_client.stream_response(
            system="You are a helpful assistant.",
            user="Hello",
            on_fragment=on_fragment,
        )

        # Verify characters were processed in sequence: H, e, l, l, o with color repaint
        expected_calls = [
            ((0, 0, "H", HEAD_FG, BG), {}),  # H in white
            ((0, 0, "H", TRAIL_FG, BG), {}),  # H repainted green
            ((1, 0, "e", HEAD_FG, BG), {}),  # e in white
            ((1, 0, "e", TRAIL_FG, BG), {}),  # e repainted green
            ((2, 0, "l", HEAD_FG, BG), {}),  # l in white
            ((2, 0, "l", TRAIL_FG, BG), {}),  # l repainted green
            ((3, 0, "l", HEAD_FG, BG), {}),  # l in white
            ((3, 0, "l", TRAIL_FG, BG), {}),  # l repainted green
            ((4, 0, "o", HEAD_FG, BG), {}),  # o in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_renderer_init_and_finalize_called(self):
        """Test that renderer.init() and renderer.finalize() are called exactly once."""
        # Mock renderer with init/finalize tracking
        mock_renderer = Mock()
        mock_renderer.height = 10
        mock_renderer.draw_cell = Mock()
        mock_renderer.init = Mock()
        mock_renderer.finalize = Mock()

        # Create writer
        writer = SingleColumnWriter(mock_renderer)

        # Mock LLM client
        mock_client = Mock(spec=LLMClient)

        # Create mock response
        async def mock_stream_response(system, user, on_fragment):
            await on_fragment("Test")

        mock_client.stream_response = AsyncMock(side_effect=mock_stream_response)

        # Define fragment callback
        async def on_fragment(fragment: str):
            for char in fragment:
                writer.on_char(char)

        # Simulate the main flow
        mock_renderer.init()
        await mock_client.stream_response(
            system="You are a helpful assistant.",
            user="Test",
            on_fragment=on_fragment,
        )
        mock_renderer.finalize()

        # Verify init and finalize were called exactly once
        mock_renderer.init.assert_called_once()
        mock_renderer.finalize.assert_called_once()

    @pytest.mark.asyncio
    async def test_newline_skipping_in_stream(self):
        """Test that newlines in stream fragments are properly skipped."""
        # Mock renderer
        mock_renderer = create_mock_renderer(height=10)

        # Create writer
        writer = SingleColumnWriter(mock_renderer)

        # Mock LLM client
        mock_client = Mock(spec=LLMClient)

        # Create mock response with newlines
        async def mock_stream_response(system, user, on_fragment):
            await on_fragment("Hello\n")
            await on_fragment("\rWorld")

        mock_client.stream_response = AsyncMock(side_effect=mock_stream_response)

        # Define fragment callback
        async def on_fragment(fragment: str):
            for char in fragment:
                writer.on_char(char)

        # Call the mocked stream
        await mock_client.stream_response(
            system="You are a helpful assistant.",
            user="Hello World",
            on_fragment=on_fragment,
        )

        # Verify only printable characters were drawn (skipping \n and \r) with color repaint
        expected_calls = [
            ((0, 0, "H", HEAD_FG, BG), {}),  # H in white
            ((0, 0, "H", TRAIL_FG, BG), {}),  # H repainted green
            ((1, 0, "e", HEAD_FG, BG), {}),  # e in white
            ((1, 0, "e", TRAIL_FG, BG), {}),  # e repainted green
            ((2, 0, "l", HEAD_FG, BG), {}),  # l in white
            ((2, 0, "l", TRAIL_FG, BG), {}),  # l repainted green
            ((3, 0, "l", HEAD_FG, BG), {}),  # l in white
            ((3, 0, "l", TRAIL_FG, BG), {}),  # l repainted green
            ((4, 0, "o", HEAD_FG, BG), {}),  # o in white
            ((4, 0, "o", TRAIL_FG, BG), {}),  # o repainted green
            ((5, 0, "W", HEAD_FG, BG), {}),  # W in white
            ((5, 0, "W", TRAIL_FG, BG), {}),  # W repainted green
            ((6, 0, "o", HEAD_FG, BG), {}),  # o in white
            ((6, 0, "o", TRAIL_FG, BG), {}),  # o repainted green
            ((7, 0, "r", HEAD_FG, BG), {}),  # r in white
            ((7, 0, "r", TRAIL_FG, BG), {}),  # r repainted green
            ((8, 0, "l", HEAD_FG, BG), {}),  # l in white
            ((8, 0, "l", TRAIL_FG, BG), {}),  # l repainted green
            ((9, 0, "d", HEAD_FG, BG), {}),  # d in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_empty_fragments_handling(self):
        """Test handling of empty fragments in stream."""
        # Mock renderer
        mock_renderer = create_mock_renderer(height=10)

        # Create writer
        writer = SingleColumnWriter(mock_renderer)

        # Mock LLM client
        mock_client = Mock(spec=LLMClient)

        # Create mock response with empty fragments
        async def mock_stream_response(system, user, on_fragment):
            await on_fragment("")
            await on_fragment("A")
            await on_fragment("")
            await on_fragment("B")

        mock_client.stream_response = AsyncMock(side_effect=mock_stream_response)

        # Define fragment callback
        async def on_fragment(fragment: str):
            for char in fragment:
                writer.on_char(char)

        # Call the mocked stream
        await mock_client.stream_response(
            system="You are a helpful assistant.",
            user="AB",
            on_fragment=on_fragment,
        )

        # Verify only A and B were drawn with color repaint
        expected_calls = [
            ((0, 0, "A", HEAD_FG, BG), {}),  # A in white
            ((0, 0, "A", TRAIL_FG, BG), {}),  # A repainted green
            ((1, 0, "B", HEAD_FG, BG), {}),  # B in white
        ]
        mock_renderer.draw_cell.assert_has_calls(expected_calls)
