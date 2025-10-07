"""Tests for LLM streaming functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from matrix_tui.llm import LLMClient


@pytest.mark.asyncio
async def test_stream_response_prints_tokens(capsys):
    """Test that stream_response calls on_fragment callback with tokens incrementally."""
    # Create mock streaming events
    fake_stream = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello "))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="World"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
    ]

    # Create async iterator for the stream
    async def async_iter():
        for event in fake_stream:
            yield event

    # Create mock client
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = async_iter()

    # Create mock on_fragment callback
    mock_on_fragment = AsyncMock()

    # Initialize LLMClient with test config
    cfg = {
        "base_url": "http://localhost:8000",
        "api_key": "test-key",
        "model": "test-model",
    }
    llm = LLMClient(cfg)
    llm.client = mock_client

    # Call stream_response
    await llm.stream_response("system message", "user message", mock_on_fragment)

    # Verify the callback was called correctly
    assert mock_on_fragment.call_count == 3  # 3 tokens
    mock_on_fragment.assert_any_call("Hello ")
    mock_on_fragment.assert_any_call("World")
    mock_on_fragment.assert_any_call("!")

    # Verify the client was called correctly
    mock_client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[
            {"role": "system", "content": "system message"},
            {"role": "user", "content": "user message"},
        ],
        stream=True,
        max_tokens=2000,
    )


@pytest.mark.asyncio
async def test_stream_response_handles_empty_delta(capsys):
    """Test that stream_response handles events with empty delta content."""
    # Create mock streaming events with some empty deltas
    fake_stream = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello "))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # Empty delta
        MagicMock(choices=[MagicMock(delta=MagicMock(content="World"))]),
        MagicMock(choices=[MagicMock(delta=None)]),  # No delta
    ]

    # Create async iterator for the stream
    async def async_iter():
        for event in fake_stream:
            yield event

    # Create mock client
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = async_iter()

    # Create mock on_fragment callback
    mock_on_fragment = AsyncMock()

    # Initialize LLMClient with test config
    cfg = {
        "base_url": "http://localhost:8000",
        "api_key": "test-key",
        "model": "test-model",
    }
    llm = LLMClient(cfg)
    llm.client = mock_client

    # Call stream_response
    await llm.stream_response("system", "user", mock_on_fragment)

    # Verify only non-empty content was passed to callback
    assert mock_on_fragment.call_count == 2  # 2 tokens
    mock_on_fragment.assert_any_call("Hello ")
    mock_on_fragment.assert_any_call("World")


@pytest.mark.asyncio
async def test_stream_response_handles_exceptions():
    """Test that stream_response handles exceptions gracefully."""
    # Create mock client that raises an exception
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("Connection failed")

    # Create mock on_fragment callback
    mock_on_fragment = AsyncMock()

    # Initialize LLMClient with test config
    cfg = {
        "base_url": "http://localhost:8000",
        "api_key": "test-key",
        "model": "test-model",
    }
    llm = LLMClient(cfg)
    llm.client = mock_client

    # Call stream_response and expect exception
    with pytest.raises(Exception, match="Connection failed"):
        await llm.stream_response("system", "user", mock_on_fragment)


def test_llm_client_initialization():
    """Test that LLMClient initializes correctly."""
    cfg = {
        "base_url": "http://localhost:8000",
        "api_key": "test-key",
        "model": "test-model",
    }

    llm = LLMClient(cfg)

    assert llm.model == "test-model"
    assert llm.client is not None
