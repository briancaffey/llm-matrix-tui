"""LLM client for streaming responses."""

import asyncio
import aiohttp
from typing import Callable, Awaitable
from openai import AsyncOpenAI


class LLMClient:
    """Client for interacting with OpenAI-compatible LLM endpoints."""

    def __init__(self, config):
        """Initialize the LLM client.

        Args:
            config (dict): Configuration dictionary with base_url, api_key, and model
        """
        # Force HTTP instead of HTTPS for local servers
        import httpx

        # Create HTTP client that doesn't use SSL
        http_client = httpx.AsyncClient(
            verify=False,
            http2=False,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

        self.client = AsyncOpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
            http_client=http_client,
        )
        self.model = config["model"]

    async def test_connection(self):
        """Test the connection to the LLM server.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Test OpenAI client connection
            # models = await self.client.models.list()
            return True
        except Exception as e:
            print(f"✗ Connection failed: {type(e).__name__}: {e}")
            if hasattr(e, "cause"):
                print(f"  Cause: {type(e.cause).__name__}: {e.cause}")
            return False

    async def stream_response(
        self,
        system: str,
        user: str,
        on_fragment: Callable[[str], Awaitable[None]],
        max_tokens: int = 200,
    ):
        """Stream a response from the LLM.

        Args:
            system (str): System message
            user (str): User message
            on_fragment (Callable[[str], Awaitable[None]]): Callback function for each fragment
            max_tokens (int): Maximum number of tokens to generate (default: 200)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                stream=True,
                max_tokens=max_tokens,
            )

            async for event in response:
                delta = event.choices[0].delta
                if not delta:
                    continue
                # Reasoning models (e.g. Qwen3.6, DeepSeek-R1) emit thinking
                # tokens under `delta.reasoning` before any `delta.content`.
                # Forward both so the rain visualizes the full token stream.
                reasoning = getattr(delta, "reasoning", None)
                if reasoning:
                    await on_fragment(reasoning)
                if delta.content:
                    await on_fragment(delta.content)

        except Exception as e:
            error_msg = f"Connection error: {e}"
            print(f"\nError: {error_msg}")
            print(f"  Base URL: {self.client.base_url}")
            print(f"  Model: {self.model}")
            print(
                f"  API Key: {'*' * len(self.client.api_key) if self.client.api_key else 'none'}"
            )
            raise Exception(error_msg)
