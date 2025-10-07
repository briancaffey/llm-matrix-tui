"""Test resize shrink cancel functionality."""

import pytest
from unittest.mock import Mock, AsyncMock
from matrix_tui.supervisor import StreamSupervisor
from matrix_tui.renderer import Renderer
from matrix_tui.llm import LLMClient


@pytest.fixture
def mock_renderer():
    """Create a mock renderer that can change width."""
    renderer = Mock(spec=Renderer)
    renderer.width = 3  # Start with width 3
    renderer.height = 10
    return renderer


@pytest.fixture
def mock_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)
    return client


@pytest.mark.asyncio
async def test_resize_shrink_cancel(mock_renderer, mock_client):
    """Test that writers are cancelled when terminal shrinks."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with width=3, columns=3
    await supervisor.start(3)

    # Should have 3 writers initially
    assert len(supervisor.writers) == 3

    # Simulate terminal resize to width=1
    mock_renderer.width = 1

    # Call on_resize
    supervisor.on_resize()

    # Should now have only 1 writer within the new width
    assert len(supervisor.writers) == 1
    assert 0 <= supervisor.writers[0].col < mock_renderer.width

    # Verify tasks were cancelled (we can't easily test this with mocks,
    # but the logic should be there)


@pytest.mark.asyncio
async def test_resize_shrink_partial_cancel(mock_renderer, mock_client):
    """Test partial cancellation when shrinking."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with width=5, columns=5
    mock_renderer.width = 5
    await supervisor.start(5)

    # Should have 5 writers initially
    assert len(supervisor.writers) == 5

    # Simulate terminal resize to width=2
    mock_renderer.width = 2

    # Call on_resize
    supervisor.on_resize()

    # Should now have only 2 writers within the new width
    assert len(supervisor.writers) == 2
    for writer in supervisor.writers:
        assert 0 <= writer.col < mock_renderer.width


@pytest.mark.asyncio
async def test_resize_no_change(mock_renderer, mock_client):
    """Test that no cancellation occurs when width doesn't change."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with width=3, columns=3
    await supervisor.start(3)

    # Should have 3 writers initially
    assert len(supervisor.writers) == 3

    # Call on_resize without changing width
    supervisor.on_resize()

    # Should still have 3 writers within the width
    assert len(supervisor.writers) == 3
    for writer in supervisor.writers:
        assert 0 <= writer.col < mock_renderer.width


@pytest.mark.asyncio
async def test_resize_grow_no_action(mock_renderer, mock_client):
    """Test that growing terminal doesn't spawn new writers (as per PRD)."""
    supervisor = StreamSupervisor(mock_client, mock_renderer)

    # Mock the stream_response method
    mock_client.stream_response = AsyncMock()

    # Start with width=2, columns=2
    mock_renderer.width = 2
    await supervisor.start(2)

    # Should have 2 writers initially
    assert len(supervisor.writers) == 2

    # Simulate terminal resize to width=5
    mock_renderer.width = 5

    # Call on_resize
    supervisor.on_resize()

    # Should still have only 2 writers within the width
    assert len(supervisor.writers) == 2
    for writer in supervisor.writers:
        assert 0 <= writer.col < mock_renderer.width
