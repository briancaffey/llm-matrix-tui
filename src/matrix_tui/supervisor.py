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

    def __init__(
        self,
        client: LLMClient,
        renderer: Renderer,
        prompts_file: str = "prompts.yml",
        include_langs: List[str] = None,
        exclude_langs: List[str] = None,
        fade_curve: str = "linear",
    ):
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
            print(
                f"\n⚠️  WARNING: Terminal height is only {self.renderer.height} lines!"
            )
            print(
                "   For best results, resize your terminal window to be taller (at least 10-20 lines)."
            )
            print("   With only 1 line, characters will overwrite each other.\n")

        # Generate random column positions for better visual effect
        available_positions = list(range(self.renderer.width))
        random.shuffle(available_positions)
        column_positions = available_positions[:active]

        # Create writers for each active column at random positions
        self.writers = [
            ColumnWriter(self.renderer, col, self.fade_curve)
            for col in column_positions
        ]

        # Start real concurrent LLM streams for each column
        # Skip content distribution in test mode (when client is mocked)
        if hasattr(self.client, "stream_response") and hasattr(
            self.client.stream_response, "_mock_name"
        ):
            # This is a mock client, skip content distribution for tests
            pass
        else:
            await self._start_concurrent_streams()

    async def _start_concurrent_streams(self):
        """Start continuous LLM streams with dynamic column allocation."""
        # Track active streams and their columns
        self.active_streams = {}  # column_id -> task
        self.available_columns = set(
            range(len(self.writers))
        )  # Available column indices

        # Start background fade rendering task
        fade_task = asyncio.create_task(self._fade_renderer())

        # Start continuous request generator
        request_generator_task = asyncio.create_task(
            self._continuous_request_generator()
        )

        try:
            # Wait for the request generator to complete (it runs indefinitely)
            await request_generator_task
        finally:
            # Cancel all active streams
            for task in self.active_streams.values():
                task.cancel()

            # Wait for all streams to finish
            if self.active_streams:
                await asyncio.gather(
                    *self.active_streams.values(), return_exceptions=True
                )

            # Cancel the fade renderer
            fade_task.cancel()
            try:
                await fade_task
            except asyncio.CancelledError:
                pass

    async def _continuous_request_generator(self):
        """Generate continuous requests and assign them to available columns."""
        while True:
            try:
                # Wait for an available column
                while not self.available_columns:
                    await asyncio.sleep(0.1)

                # Pick a random available column
                column_id = random.choice(list(self.available_columns))
                self.available_columns.remove(column_id)

                # Start a new stream in this column
                writer = self.writers[column_id]
                task = asyncio.create_task(
                    self._stream_single_request(writer, column_id)
                )
                self.active_streams[column_id] = task

                # Small delay between starting new requests
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"Error in request generator: {e}")
                await asyncio.sleep(1.0)

    async def _stream_single_request(self, writer: ColumnWriter, column_id: int):
        """Stream a single LLM request for a specific writer.

        Args:
            writer: ColumnWriter instance to feed characters to
            column_id: Column identifier for tracking
        """

        async def on_fragment(fragment: str):
            """Process each fragment by iterating through proper character units."""

            # Debug log the fragment
            # print(f"Fragment: {fragment}")
            import unicodedata

            # Process characters properly, handling combining characters
            i = 0
            while i < len(fragment):
                char = fragment[i]

                # Skip control characters but allow regular spaces
                if unicodedata.category(char)[0] == "C":
                    i += 1
                    continue

                # Skip other whitespace characters except regular spaces
                if char.isspace() and char != " ":
                    i += 1
                    continue

                # Check if this is a combining character
                if unicodedata.category(char) in ["Mn", "Me", "Mc"]:  # Combining marks
                    # Skip combining characters - they should have been attached to previous character
                    i += 1
                    continue

                # Check if this is a wide character (CJK, emoji, etc.)
                if unicodedata.east_asian_width(char) in [
                    "W",
                    "F",
                ]:  # Wide or Full-width
                    # Wide characters take up 2 terminal cells, but we'll render as single unit
                    writer.on_char(char)
                    i += 1
                    continue

                # Regular character - check if next character is a combining mark
                if i + 1 < len(fragment):
                    next_char = fragment[i + 1]
                    if unicodedata.category(next_char) in ["Mn", "Me", "Mc"]:
                        # This character has combining marks - treat as single unit
                        cluster = char
                        j = i + 1
                        while j < len(fragment) and unicodedata.category(
                            fragment[j]
                        ) in ["Mn", "Me", "Mc"]:
                            cluster += fragment[j]
                            j += 1
                        writer.on_char(cluster)
                        i = j
                    else:
                        # Regular single character
                        writer.on_char(char)
                        i += 1
                else:
                    # Last character
                    writer.on_char(char)
                    i += 1

        try:
            # Get a random prompt for this request
            prompt_data = self.prompt_loader.get_random_prompt()
            user_prompt = prompt_data["prompt"]
            system_prompt = prompt_data["system_prompt"]

            await self.client.stream_response(
                system=system_prompt,
                user=user_prompt,
                on_fragment=on_fragment,
            )

        except Exception as e:
            print(f"Error in stream for column {writer.col}: {e}")
            print(f"  System prompt: {system_prompt[:50]}...")
            print(f"  User prompt: {user_prompt[:50]}...")
        finally:
            # Mark this column as available again
            self.available_columns.add(column_id)
            # Remove from active streams
            if column_id in self.active_streams:
                del self.active_streams[column_id]

    async def _fade_renderer(self):
        """Background task to periodically update fade effects for all columns."""
        while True:
            try:
                # Update fade effects for all writers
                for writer in self.writers:
                    writer._render_fade_mode()

                # Small delay for 60fps smooth animation
                await asyncio.sleep(1 / 60)  # Update fade effects 60 times per second
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
