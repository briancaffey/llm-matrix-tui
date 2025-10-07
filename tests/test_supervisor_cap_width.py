"""Test supervisor concurrency cap to terminal width."""

import pytest
from unittest.mock import Mock, AsyncMock
from matrix_tui.supervisor import StreamSupervisor
from matrix_tui.renderer import Renderer
from matrix_tui.llm import LLMClient


@pytest.fixture
def mock_renderer():
    """Create a mock renderer with width=3."""
    renderer = Mock(spec=Renderer)
    renderer.width = 3
    renderer.height = 10
    return renderer


@pytest.fixture
def mock_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)
    return client


@pytest.mark.asyncio
async def test_supervisor_cap_width(mock_renderer, mock_client):
    """Test that supervisor caps columns to terminal width."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method to avoid actual API calls
    mock_client.stream_response = AsyncMock()

    # Start with 10 columns but terminal width is only 3
    await supervisor.start(10)

    # Should only create 3 writers with random positions within terminal width
    assert len(supervisor.writers) == 3
    # Check that all column positions are within valid range
    for writer in supervisor.writers:
        assert 0 <= writer.col < mock_renderer.width
    # Check that all column positions are unique
    cols = [writer.col for writer in supervisor.writers]
    assert len(set(cols)) == len(cols)

    # With fake streaming, we don't use tasks anymore
    # The fake content is distributed directly


@pytest.mark.asyncio
async def test_supervisor_exact_width(mock_renderer, mock_client):
    """Test that supervisor works correctly when columns equals width."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with 3 columns, terminal width is 3
    await supervisor.start(3)

    # Should create exactly 3 writers
    assert len(supervisor.writers) == 3


@pytest.mark.asyncio
async def test_supervisor_less_than_width(mock_renderer, mock_client):
    """Test that supervisor works when columns < width."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with 2 columns, terminal width is 3
    await supervisor.start(2)

    # Should create exactly 2 writers
    assert len(supervisor.writers) == 2
