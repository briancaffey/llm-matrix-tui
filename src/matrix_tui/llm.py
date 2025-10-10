"""LLM client for streaming responses."""

from typing import Callable, Awaitable
from openai import AsyncOpenAI


class LLMClient:
    """Client for interacting with OpenAI-compatible LLM endpoints."""

    def __init__(self, config):
        """Initialize the LLM client.

        Args:
            config (dict): Configuration dictionary with base_url, api_key, and model
        """
        self.client = AsyncOpenAI(
            base_url=config["base_url"], api_key=config["api_key"]
        )
        self.model = config["model"]

    async def stream_response(
        self, system: str, user: str, on_fragment: Callable[[str], Awaitable[None]], max_tokens: int = 100
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
                if delta and delta.content:
                    await on_fragment(delta.content)

        except Exception as e:
            print(f"\nError: {e}")
            raise
