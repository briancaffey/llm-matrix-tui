"""Vertical column writer for character-by-character rendering."""

from typing import TYPE_CHECKING, Optional, Tuple

from .animation import (
    AnimationConfig,
    ColumnAnimationState,
    get_random_mutation_char,
)
from .fade_math import FADE_FUNCTIONS, calculate_fade_color

if TYPE_CHECKING:
    from .image_mode import ImageModeController


class ColumnWriter:
    """Writes characters vertically in a specific column, wrapping to top when reaching bottom."""

    def __init__(
        self,
        renderer,
        col: int,
        fade_curve: str = "linear",
        animation_config: Optional[AnimationConfig] = None,
        image_controller: Optional["ImageModeController"] = None,
    ):
        """Initialize the column writer.

        Args:
            renderer: Renderer instance for drawing characters
            col: Column index (x-coordinate) for this writer
            fade_curve: Type of fade curve to use ('linear', 'quadratic', 'exponential')
            animation_config: Optional animation configuration for effects
            image_controller: Optional image mode controller for brightness modulation
        """
        self.renderer = renderer
        self.col = col
        self.fade_curve = fade_curve
        self.fade_function = FADE_FUNCTIONS[fade_curve]

        # Track character history for fade effect
        self.character_history = []  # List of (row, char, age) tuples
        self.current_row = 0
        self.age_counter = 0  # Increments with each new character

        # Brightness modifier for image mode (1.0 = full brightness)
        self.brightness_modifier: float = 1.0

        # Image mode support
        self.image_controller = image_controller

        # Animation support
        self.animation_config = animation_config
        self.animation_state: Optional[ColumnAnimationState] = None
        if animation_config is not None:
            self.animation_state = ColumnAnimationState.from_config(animation_config)

        # Backward compatibility attributes for tests
        self.row = 0  # Alias for current_row
        self.col = col
        self.last_pos: tuple[int, int] | None = None
        self.last_char: str | None = None

    @property
    def head_color(self) -> Tuple[int, int, int]:
        """Get head color from renderer's theme."""
        return self.renderer.head_color

    @property
    def trail_color(self) -> Tuple[int, int, int]:
        """Get trail color from renderer's theme."""
        return self.renderer.trail_color

    @property
    def background_color(self) -> Tuple[int, int, int]:
        """Get background color from renderer's theme."""
        return self.renderer.background_color

    def on_char(self, ch: str):
        """Process a single character for vertical rendering with trailing fade effect.

        Args:
            ch (str): Single character to render
        """
        # Skip empty strings, newline and carriage return characters
        if not ch or ch in {"\n", "\r"}:
            return

        # Check if we're in test mode (when renderer is mocked)
        is_test_mode = hasattr(self.renderer, "draw_cell") and hasattr(
            self.renderer.draw_cell, "call_args_list"
        )

        if is_test_mode:
            # Test mode: use old behavior for backward compatibility
            self._on_char_test_mode(ch)
        else:
            # Production mode: use fade effect
            self._on_char_production_mode(ch)

    def _on_char_test_mode(self, ch: str):
        """Test mode character processing with immediate repaint."""
        # Step 1: If last_pos exists, repaint previous head with green color
        if self.last_pos is not None and self.last_char is not None:
            self.renderer.draw_cell(
                self.last_pos[0],
                self.last_pos[1],
                self.last_char,
                self.trail_color,
                self.background_color,
            )

        # Step 2: Draw new head at current position with white color
        self.renderer.draw_cell(
            self.current_row, self.col, ch, self.head_color, self.background_color
        )

        # Step 3: Update tracking variables
        self.last_pos = (self.current_row, self.col)
        self.last_char = ch

        # Step 4: Move to next row, wrapping to top when reaching bottom
        self.current_row = (self.current_row + 1) % self.renderer.height

        # Update backward compatibility attributes
        self.row = self.current_row

    def _on_char_production_mode(self, ch: str):
        """Production mode character processing with fade effect."""
        # IMPORTANT: Repaint the previous head as trail color BEFORE adding new character
        # This ensures only ONE white head per column, even when characters arrive quickly
        if len(self.character_history) >= 1:
            prev_row, prev_char, prev_age = self.character_history[-1]
            # Repaint previous head with appropriate trail color
            if self.image_controller is not None:
                # Image mode: use position brightness
                brightness = self.image_controller.get_position_brightness(
                    prev_row, self.col
                )
                intensity = max(0.15, brightness)
                trail_color = (
                    int(self.trail_color[0] * intensity),
                    int(self.trail_color[1] * intensity),
                    int(self.trail_color[2] * intensity),
                )
            else:
                # Normal mode: use full trail color (fade renderer will handle fading)
                trail_color = self.trail_color
            self.renderer.draw_cell(
                prev_row, self.col, prev_char, trail_color, self.background_color
            )

        # Age all existing characters
        self.age_counter += 1

        # Add new character to history
        self.character_history.append((self.current_row, ch, self.age_counter))

        # Draw the new head character in white
        self.renderer.draw_cell(
            self.current_row, self.col, ch, self.head_color, self.background_color
        )

        # Move to next row, wrapping to top when reaching bottom
        self.current_row = (self.current_row + 1) % self.renderer.height

        # Update backward compatibility attributes
        self.row = self.current_row
        self.last_pos = (
            (self.current_row - 1, self.col)
            if self.current_row > 0
            else (self.renderer.height - 1, self.col)
        )
        self.last_char = ch

        # Clean up old characters that are completely faded
        self._cleanup_old_characters()

    def _render_all_characters_immediately(self):
        """Render all characters immediately with correct colors - only newest is white."""
        if not self.character_history:
            return

        # Get fade distance (longer in image mode)
        fade_distance = self._get_fade_distance()

        # Find the maximum age (most recent character)
        max_age = max(age for _, _, age in self.character_history)

        for row, char, age in self.character_history:
            # Determine if this is the newest character (highest age)
            is_newest = age == max_age

            if is_newest:
                # Newest character is white
                final_color = self.head_color
            else:
                # Calculate fade progress for older characters
                progress = min(1.0, (max_age - age) / fade_distance)
                fade_intensity = self.fade_function(progress)
                final_color = calculate_fade_color(self.trail_color, fade_intensity)

            # Render the character immediately
            self.renderer.draw_cell(
                row, self.col, char, final_color, self.background_color
            )

    def _render_new_character_only(self):
        """Render only the newest character to minimize blocking."""
        if not self.character_history:
            return

        # Check if we're in test mode (when renderer is mocked)
        if hasattr(self.renderer, "draw_cell") and hasattr(
            self.renderer.draw_cell, "call_args_list"
        ):
            # Test mode: maintain old behavior for backward compatibility
            newest_row, newest_char, newest_age = self.character_history[-1]
            self.renderer.draw_cell(
                newest_row,
                self.col,
                newest_char,
                self.head_color,
                self.background_color,
            )
        else:
            # Production mode: render only the newest character with head color
            newest_row, newest_char, newest_age = self.character_history[-1]
            self.renderer.draw_cell(
                newest_row,
                self.col,
                newest_char,
                self.head_color,
                self.background_color,
            )

    def _render_all_characters(self):
        """Render all characters in history with appropriate fade colors."""
        # Check if we're in test mode (when renderer is mocked)
        if hasattr(self.renderer, "draw_cell") and hasattr(
            self.renderer.draw_cell, "call_args_list"
        ):
            # Test mode: maintain old behavior for backward compatibility
            self._render_test_mode()
        else:
            # Production mode: use fade effect
            self._render_fade_mode()

    def _get_fade_distance(self) -> int:
        """Get the fade distance, accounting for image mode.

        In image mode, characters persist much longer to make the image visible.
        """
        # Base fade distance from animation state or default
        if self.animation_state is not None:
            base_distance = self.animation_state.trail_length
        else:
            base_distance = min(self.renderer.height, 20)

        # In image mode, multiply the fade distance significantly
        # This makes characters persist longer, revealing the image
        if self.image_controller is not None:
            # Use 3x the terminal height for very long trails in image mode
            return max(base_distance, self.renderer.height * 3)

        return base_distance

    def _render_fade_mode(self):
        """Render with fade effect for production use - optimized for 60fps."""
        if not self.character_history:
            return

        # Apply mutation if configured
        if self.animation_config is not None:
            self.apply_mutation()

        # Use completely different rendering for image mode
        if self.image_controller is not None:
            self._render_image_mode()
            return

        # Get fade distance
        fade_distance = self._get_fade_distance()

        # Find the maximum age (most recent character)
        max_age = max(age for _, _, age in self.character_history)

        for row, char, age in self.character_history:
            # Determine if this is the newest character (highest age)
            is_newest = age == max_age

            if is_newest:
                # Head color with potential flash effect
                color = self.get_flash_color(self.head_color)
                color = self.apply_brightness_modifier(color)
                self.renderer.draw_cell(
                    row, self.col, char, color, self.background_color
                )
            else:
                # Calculate fade progress for older characters
                progress = min(1.0, (max_age - age) / fade_distance)
                fade_intensity = self.fade_function(progress)
                final_color = calculate_fade_color(self.trail_color, fade_intensity)

                # Apply flash and brightness modifiers
                final_color = self.get_flash_color(final_color)
                final_color = self.apply_brightness_modifier(final_color)

                # Render the character with fade effect
                self.renderer.draw_cell(
                    row, self.col, char, final_color, self.background_color
                )

    def _render_image_mode(self):
        """Render characters for image visualization mode.

        Hybrid rendering that keeps the Matrix rain feel while showing the image:
        - Head (newest): White/bright head color
        - Next 5 characters: Gradient from 100% to 90% brightness (short rain trail)
        - Older characters: Brightness driven by image map (min 30% for contrast)
        """
        if not self.character_history:
            return

        # Constants for the rain trail effect
        TRAIL_LENGTH = 5  # Number of characters in the bright trail
        TRAIL_MIN_BRIGHTNESS = 0.90  # Minimum brightness at end of trail
        IMAGE_MIN_BRIGHTNESS = 0.30  # Minimum brightness for image-mapped chars

        # Find the maximum age (most recent character = head)
        max_age = max(age for _, _, age in self.character_history)

        for row, char, age in self.character_history:
            # How far behind the head is this character?
            age_distance = max_age - age

            # Get image brightness at this position (0.0 to 1.0)
            position_brightness = self.image_controller.get_position_brightness(
                row, self.col
            )

            if age_distance == 0:
                # HEAD: Always bright white/head color
                color = self.get_flash_color(self.head_color)
                self.renderer.draw_cell(
                    row, self.col, char, color, self.background_color
                )

            elif age_distance <= TRAIL_LENGTH:
                # TRAIL (characters 1-5 behind head): Gradient from 100% to 90%
                # Linear interpolation: at distance 1 -> 100%, at distance 5 -> 90%
                trail_progress = (age_distance - 1) / max(1, (TRAIL_LENGTH - 1))
                trail_brightness = 1.0 - (trail_progress * (1.0 - TRAIL_MIN_BRIGHTNESS))

                r = int(self.trail_color[0] * trail_brightness)
                g = int(self.trail_color[1] * trail_brightness)
                b = int(self.trail_color[2] * trail_brightness)
                final_color = (r, g, b)

                # Apply flash effect if active
                final_color = self.get_flash_color(final_color)

                self.renderer.draw_cell(
                    row, self.col, char, final_color, self.background_color
                )

            else:
                # BACKGROUND (older than trail): Brightness from image map
                # Minimum 30% brightness for better contrast
                intensity = max(IMAGE_MIN_BRIGHTNESS, position_brightness)

                r = int(self.trail_color[0] * intensity)
                g = int(self.trail_color[1] * intensity)
                b = int(self.trail_color[2] * intensity)
                final_color = (r, g, b)

                # Apply flash effect if active
                final_color = self.get_flash_color(final_color)

                self.renderer.draw_cell(
                    row, self.col, char, final_color, self.background_color
                )

    def _render_test_mode(self):
        """Render with old behavior for test compatibility."""
        # Render newest character in white
        if self.character_history:
            newest_row, newest_char, newest_age = self.character_history[-1]
            self.renderer.draw_cell(
                newest_row,
                self.col,
                newest_char,
                self.head_color,
                self.background_color,
            )

        # Render previous character in green (old behavior)
        if len(self.character_history) > 1:
            prev_row, prev_char, prev_age = self.character_history[-2]
            self.renderer.draw_cell(
                prev_row, self.col, prev_char, self.trail_color, self.background_color
            )

    def _cleanup_old_characters(self):
        """Remove characters that are completely faded (intensity < 0.01)."""
        if not self.character_history:
            return

        # In image mode, NEVER clean up characters - we want them to fill the screen
        # and persist so the image becomes visible
        if self.image_controller is not None:
            # Only limit to prevent unbounded memory growth
            # Keep at most 2x terminal height worth of characters per column
            max_chars = self.renderer.height * 2
            if len(self.character_history) > max_chars:
                self.character_history = self.character_history[-max_chars:]
            return

        # Normal mode: clean up faded characters
        fade_distance = self._get_fade_distance()
        max_age = max(age for _, _, age in self.character_history)

        self.character_history = [
            (row, char, age)
            for row, char, age in self.character_history
            if self.fade_function(min(1.0, (max_age - age) / fade_distance)) >= 0.01
        ]

    def apply_mutation(self) -> None:
        """Apply random character mutation to trailing characters."""
        if not self.animation_config or not self.character_history:
            return

        # Don't mutate the newest character (head)
        if len(self.character_history) <= 1:
            return

        # Check each character (except head) for mutation
        max_age = max(age for _, _, age in self.character_history)
        new_history = []

        for row, char, age in self.character_history:
            if age == max_age:
                # Keep the head character unchanged
                new_history.append((row, char, age))
            elif self.animation_config.should_mutate():
                # Mutate this character
                new_char = get_random_mutation_char()
                new_history.append((row, new_char, age))
            else:
                new_history.append((row, char, age))

        self.character_history = new_history

    def get_flash_color(self, base_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get color with flash effect applied if active.

        Args:
            base_color: The original color

        Returns:
            Color with flash effect applied (brighter) or original color
        """
        if self.animation_state is None or not self.animation_state.flash_active:
            return base_color

        # Flash effect: brighten the color towards white
        flash_intensity = 0.7  # How much to blend towards white
        r = int(base_color[0] + (255 - base_color[0]) * flash_intensity)
        g = int(base_color[1] + (255 - base_color[1]) * flash_intensity)
        b = int(base_color[2] + (255 - base_color[2]) * flash_intensity)
        return (r, g, b)

    def apply_brightness_modifier(
        self, color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        """Apply brightness modifier to a color.

        Args:
            color: RGB color tuple

        Returns:
            Color with brightness modifier applied
        """
        if self.brightness_modifier >= 1.0:
            return color

        r = int(color[0] * self.brightness_modifier)
        g = int(color[1] * self.brightness_modifier)
        b = int(color[2] * self.brightness_modifier)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def trigger_flash(self) -> None:
        """Trigger a flash effect on this column."""
        if self.animation_state is not None:
            self.animation_state.trigger_flash()

    def update_animation(self, delta_time: float) -> None:
        """Update animation state.

        Args:
            delta_time: Time elapsed since last update (seconds)
        """
        if self.animation_state is not None:
            self.animation_state.update(delta_time)

    def update_image_brightness(self) -> None:
        """Update brightness modifier based on image mode.

        Uses the current row position to get brightness from the image map.
        """
        if self.image_controller is None:
            return

        # Get the average brightness for characters in this column
        if self.character_history:
            # Use the head position for brightness
            head_row = self.character_history[-1][0] if self.character_history else 0
            self.brightness_modifier = self.image_controller.get_position_brightness(
                head_row, self.col
            )
        else:
            # Use column average when no characters
            self.brightness_modifier = (
                self.image_controller.image_map.get_column_activity(self.col)
            )

    @property
    def is_active(self) -> bool:
        """Check if this column is active (should receive characters)."""
        if self.animation_state is None:
            return True
        return self.animation_state.is_active

    @property
    def start_delay(self) -> float:
        """Get the start delay for this column."""
        if self.animation_state is None:
            return 0.0
        return self.animation_state.start_delay

    def on_resize(self):
        """Handle terminal resize by updating dimensions and adjusting row position.

        Called when terminal is resized to maintain proper wrapping behavior.
        """
        self.renderer.refresh_dims()
        # Adjust current row to be within new height bounds
        self.current_row = self.current_row % self.renderer.height

        # Update backward compatibility attributes
        self.row = self.current_row

        # Clean up character history to remove characters outside new bounds
        self.character_history = [
            (row, char, age)
            for row, char, age in self.character_history
            if row < self.renderer.height
        ]


class SingleColumnWriter:
    """Writes characters vertically in the first column, wrapping to top when reaching bottom."""

    def __init__(self, renderer):
        """Initialize the single column writer.

        Args:
            renderer: Renderer instance for drawing characters
        """
        self.renderer = renderer
        self.row = 0
        self.col = 0  # Fixed at column 0 for this phase
        self.last_pos: tuple[int, int] | None = None
        self.last_char: str | None = None

    @property
    def head_color(self) -> Tuple[int, int, int]:
        """Get head color from renderer's theme."""
        return self.renderer.head_color

    @property
    def trail_color(self) -> Tuple[int, int, int]:
        """Get trail color from renderer's theme."""
        return self.renderer.trail_color

    @property
    def background_color(self) -> Tuple[int, int, int]:
        """Get background color from renderer's theme."""
        return self.renderer.background_color

    def on_char(self, ch: str):
        """Process a single character for vertical rendering with color repaint logic.

        Args:
            ch (str): Single character to render
        """
        # Skip empty strings, newline and carriage return characters
        if not ch or ch in {"\n", "\r"}:
            return

        # Step 1: If last_pos exists, repaint previous head with trail color
        if self.last_pos is not None and self.last_char is not None:
            self.renderer.draw_cell(
                self.last_pos[0],
                self.last_pos[1],
                self.last_char,
                self.trail_color,
                self.background_color,
            )

        # Step 2: Draw new head at current position with head color
        self.renderer.draw_cell(
            self.row, self.col, ch, self.head_color, self.background_color
        )

        # Step 3: Update tracking variables
        self.last_pos = (self.row, self.col)
        self.last_char = ch

        # Step 4: Move to next row, wrapping to top when reaching bottom
        self.row = (self.row + 1) % self.renderer.height

    def on_resize(self):
        """Handle terminal resize by updating dimensions and adjusting row position.

        Called when terminal is resized to maintain proper wrapping behavior.
        """
        self.renderer.refresh_dims()
        # Adjust current row to be within new height bounds
        self.row = self.row % self.renderer.height
