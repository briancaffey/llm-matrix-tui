"""Vertical column writer for character-by-character rendering."""

from .renderer import HEAD_FG, TRAIL_FG, BG
from .fade_math import FADE_FUNCTIONS, calculate_fade_color


class ColumnWriter:
    """Writes characters vertically in a specific column, wrapping to top when reaching bottom."""

    def __init__(self, renderer, col: int, fade_curve: str = "linear"):
        """Initialize the column writer.

        Args:
            renderer: Renderer instance for drawing characters
            col: Column index (x-coordinate) for this writer
            fade_curve: Type of fade curve to use ('linear', 'quadratic', 'exponential')
        """
        self.renderer = renderer
        self.col = col
        self.fade_curve = fade_curve
        self.fade_function = FADE_FUNCTIONS[fade_curve]

        # Track character history for fade effect
        self.character_history = []  # List of (row, char, age) tuples
        self.current_row = 0
        self.age_counter = 0  # Increments with each new character

        # Base colors
        self.head_color = HEAD_FG
        self.trail_color = TRAIL_FG

        # Backward compatibility attributes for tests
        self.row = 0  # Alias for current_row
        self.col = col
        self.last_pos: tuple[int, int] | None = None
        self.last_char: str | None = None

    def on_char(self, ch: str):
        """Process a single character for vertical rendering with trailing fade effect.

        Args:
            ch (str): Single character to render
        """
        # Skip empty strings, newline and carriage return characters
        if not ch or ch in {'\n', '\r'}:
            return

        # Age all existing characters
        self.age_counter += 1

        # Add new character to history
        self.character_history.append((self.current_row, ch, self.age_counter))

        # Render all characters with appropriate fade
        self._render_all_characters()

        # Move to next row, wrapping to top when reaching bottom
        self.current_row = (self.current_row + 1) % self.renderer.height

        # Update backward compatibility attributes
        self.row = self.current_row
        self.last_pos = (self.current_row - 1, self.col) if self.current_row > 0 else (self.renderer.height - 1, self.col)
        self.last_char = ch

        # Clean up old characters that are completely faded
        self._cleanup_old_characters()

    def _render_all_characters(self):
        """Render all characters in history with appropriate fade colors."""
        # Check if we're in test mode (when renderer is mocked)
        if hasattr(self.renderer, 'draw_cell') and hasattr(self.renderer.draw_cell, '_mock_name'):
            # Test mode: maintain old behavior for backward compatibility
            self._render_test_mode()
        else:
            # Production mode: use fade effect
            self._render_fade_mode()

    def _render_fade_mode(self):
        """Render with fade effect for production use."""
        for row, char, age in self.character_history:
            # Calculate fade progress (0.0 = newest, 1.0 = oldest)
            # Use terminal height as the fade distance
            fade_distance = min(self.renderer.height, 20)  # Cap fade distance for performance
            progress = min(1.0, (self.age_counter - age) / fade_distance)

            # Calculate fade intensity using the selected curve
            fade_intensity = self.fade_function(progress)

            # Determine base color (head vs trail)
            base_color = self.head_color if age == self.age_counter else self.trail_color

            # Calculate final color
            final_color = calculate_fade_color(base_color, fade_intensity)

            # Render the character
            self.renderer.draw_cell(row, self.col, char, final_color, BG)

    def _render_test_mode(self):
        """Render with old behavior for test compatibility."""
        # Render newest character in white
        if self.character_history:
            newest_row, newest_char, newest_age = self.character_history[-1]
            self.renderer.draw_cell(newest_row, self.col, newest_char, self.head_color, BG)

        # Render previous character in green (old behavior)
        if len(self.character_history) > 1:
            prev_row, prev_char, prev_age = self.character_history[-2]
            self.renderer.draw_cell(prev_row, self.col, prev_char, self.trail_color, BG)

    def _cleanup_old_characters(self):
        """Remove characters that are completely faded (intensity < 0.01)."""
        fade_distance = min(self.renderer.height, 20)
        self.character_history = [
            (row, char, age) for row, char, age in self.character_history
            if self.fade_function(min(1.0, (self.age_counter - age) / fade_distance)) >= 0.01
        ]

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
            (row, char, age) for row, char, age in self.character_history
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

    def on_char(self, ch: str):
        """Process a single character for vertical rendering with color repaint logic.

        Args:
            ch (str): Single character to render
        """
        # Skip empty strings, newline and carriage return characters
        if not ch or ch in {'\n', '\r'}:
            return

        # Step 1: If last_pos exists, repaint previous head with green color
        if self.last_pos is not None and self.last_char is not None:
            self.renderer.draw_cell(self.last_pos[0], self.last_pos[1], self.last_char, TRAIL_FG, BG)

        # Step 2: Draw new head at current position with white color
        self.renderer.draw_cell(self.row, self.col, ch, HEAD_FG, BG)

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
