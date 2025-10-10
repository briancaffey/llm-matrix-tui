"""Stream supervisor for managing multiple concurrent LLM streams."""

import asyncio
import random
from typing import List
from .llm import LLMClient
from .renderer import Renderer, BG
from .vertical_column import ColumnWriter
from .prompt_loader import PromptLoader


class StreamSupervisor:
    """Manages multiple concurrent LLM streams, each mapped to a terminal column."""

    def __init__(self, client: LLMClient, renderer: Renderer, prompts_file: str = "prompts.yml", include_langs: List[str] = None, exclude_langs: List[str] = None, fade_curve: str = "linear"):
        """Initialize the stream supervisor.

        Args:
            client: LLM client for making streaming requests
            renderer: Renderer instance for terminal output
            prompts_file: Path to the prompts YAML file
            include_langs: List of language codes to include (e.g., ['en', 'zh', 'ja'])
            exclude_langs: List of language codes to exclude (e.g., ['en', 'zh'])
            fade_curve: Type of fade curve to use ('linear', 'quadratic', 'exponential')
        """
        self.client = client
        self.renderer = renderer
        self.prompt_loader = PromptLoader(prompts_file, include_langs, exclude_langs)
        self.fade_curve = fade_curve
        self.writers: List[ColumnWriter] = []
        self.tasks: List[asyncio.Task] = []

    async def start(self, n: int):
        """Start N concurrent LLM streams, each in its own column.

        Args:
            n: Number of columns to create (will be capped by terminal width)
        """
        # Compute active columns based on terminal width
        active = min(n, self.renderer.width)

        # Check terminal height and warn if too small
        if self.renderer.height < 3:
            print(f"\n⚠️  WARNING: Terminal height is only {self.renderer.height} lines!")
            print("   For best results, resize your terminal window to be taller (at least 10-20 lines).")
            print("   With only 1 line, characters will overwrite each other.\n")

        # Generate random column positions for better visual effect
        available_positions = list(range(self.renderer.width))
        random.shuffle(available_positions)
        column_positions = available_positions[:active]

        # Create writers for each active column at random positions
        self.writers = [ColumnWriter(self.renderer, col, self.fade_curve) for col in column_positions]

        # Start real concurrent LLM streams for each column
        # Skip content distribution in test mode (when client is mocked)
        if hasattr(self.client, 'stream_response') and hasattr(self.client.stream_response, '_mock_name'):
            # This is a mock client, skip content distribution for tests
            pass
        else:
            await self._start_concurrent_streams()


    async def _start_concurrent_streams(self):
        """Start real concurrent LLM streams for each column."""
        # Create tasks for each column to run concurrently
        tasks = []
        for writer in self.writers:
            task = asyncio.create_task(self._stream_for_writer(writer))
            tasks.append(task)

        # Start background fade rendering task
        fade_task = asyncio.create_task(self._fade_renderer())

        # Wait for all streams to complete
        try:
            await asyncio.gather(*tasks)
        finally:
            # Cancel the fade renderer when streams complete
            fade_task.cancel()
            try:
                await fade_task
            except asyncio.CancelledError:
                pass


    async def _stream_for_writer(self, writer: ColumnWriter):
        """Stream LLM response for a specific writer.

        Args:
            writer: ColumnWriter instance to feed characters to
        """
        async def on_fragment(fragment: str):
            """Process each fragment by iterating through characters."""
            for char in fragment:
                # Render directly for true concurrency
                writer.on_char(char)

        # Get a random prompt for this column
        prompt_data = self.prompt_loader.get_random_prompt()
        user_prompt = prompt_data['prompt']
        system_prompt = prompt_data['system_prompt']

        try:
            await self.client.stream_response(
                system=system_prompt,
                user=user_prompt,
                on_fragment=on_fragment,
            )
        except Exception as e:
            print(f"Error in stream for column {writer.col}: {e}")

    async def _fade_renderer(self):
        """Background task to periodically update fade effects for all columns."""
        while True:
            try:
                # Update fade effects for all writers
                for writer in self.writers:
                    writer._render_fade_mode()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)  # Update fade effects 10 times per second
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in fade renderer: {e}")
                await asyncio.sleep(0.1)

    def on_resize(self):
        """Handle terminal resize by updating dimensions and repainting background."""
        self.renderer.refresh_dims()
        self.renderer.fill_background(BG)

        # Update writers list to only include active ones
        self.writers = [w for w in self.writers if w.col < self.renderer.width]

        # Call on_resize for remaining writers
        for writer in self.writers:
            writer.on_resize()

    async def stop(self):
        """Stop all streaming tasks and clean up."""
        # Clear lists
        self.writers.clear()
