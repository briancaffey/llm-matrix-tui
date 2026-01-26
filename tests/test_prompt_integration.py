"""Test prompt loader integration with supervisor."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from matrix_tui.supervisor import StreamSupervisor
from matrix_tui.llm import LLMClient
from matrix_tui.renderer import Renderer
from matrix_tui.prompt_loader import PromptLoader


@pytest.mark.asyncio
async def test_supervisor_uses_different_prompts():
    """Test that supervisor uses different prompts for different columns."""
    # Create mock objects
    mock_client = AsyncMock(spec=LLMClient)
    mock_renderer = MagicMock(spec=Renderer)
    mock_renderer.width = 3

    # Mock the render queue
    mock_queue = AsyncMock()
    mock_queue.put = AsyncMock()

    # Create supervisor with mock prompt loader
    supervisor = StreamSupervisor(mock_client, mock_renderer)
    supervisor.render_queue = mock_queue

    # Mock the prompt loader to return predictable prompts
    mock_prompt_loader = MagicMock(spec=PromptLoader)
    mock_prompt_loader.get_random_prompt.side_effect = [
        {
            "prompt": "English prompt",
            "system_prompt": "Answer in English",
            "lang": "en",
        },
        {"prompt": "Chinese prompt", "system_prompt": "用中文回答", "lang": "zh"},
        {
            "prompt": "Japanese prompt",
            "system_prompt": "日本語で答えてください",
            "lang": "ja",
        },
    ]
    supervisor.prompt_loader = mock_prompt_loader

    # Mock writers
    mock_writers = [MagicMock() for _ in range(3)]
    for i, writer in enumerate(mock_writers):
        writer.col = i
    supervisor.writers = mock_writers

    # Mock the render task
    supervisor.render_task = AsyncMock()

    # Add required attributes for _stream_single_request
    supervisor.available_columns = set(range(3))
    supervisor.active_streams = {}

    # Test the _stream_single_request method
    await supervisor._stream_single_request(mock_writers[0], 0)
    await supervisor._stream_single_request(mock_writers[1], 1)
    await supervisor._stream_single_request(mock_writers[2], 2)

    # Verify that different prompts were used
    assert mock_client.stream_response.call_count == 3

    # Check that different system prompts were used
    calls = mock_client.stream_response.call_args_list
    system_prompts = [call[1]["system"] for call in calls]

    # Should have different system prompts
    assert (
        len(set(system_prompts)) > 1
    ), f"Expected different system prompts, got: {system_prompts}"

    # Verify the prompts were called with correct parameters
    for i, call in enumerate(calls):
        assert "system" in call[1]
        assert "user" in call[1]
        assert "on_fragment" in call[1]


def test_prompt_loader_random_selection():
    """Test that prompt loader returns different prompts on multiple calls."""
    loader = PromptLoader()

    # Get multiple prompts
    prompts = [loader.get_random_prompt() for _ in range(10)]

    # Should have some variety in languages
    languages = [p["lang"] for p in prompts]
    unique_languages = set(languages)

    # With 105 prompts across 9 languages, we should see variety
    assert (
        len(unique_languages) > 1
    ), f"Expected multiple languages, got: {unique_languages}"

    # Verify all prompts have required fields
    for prompt in prompts:
        assert "prompt" in prompt
        assert "system_prompt" in prompt
        assert "lang" in prompt
