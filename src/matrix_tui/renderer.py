"""Terminal renderer using blessed for clean text output."""

from blessed import Terminal

# Color constants
HEAD_FG = (255, 255, 255)  # White for newest character
TRAIL_FG = (118, 185, 0)  # NVIDIA green (#76b900) for older characters
BG = (0, 0, 0)  # Black background


class Renderer:
    """Encapsulates terminal control and rendering methods."""

    def __init__(self):
        """Initialize the renderer with a blessed Terminal instance."""
        self.term = Terminal()
        self.current_x = 0
        self.current_y = 0
        self.height = 0
        self.width = 0

    def init(self):
        """Initialize the terminal for rendering.

        Clears the screen, hides the cursor, and fills background with black.
        Caches terminal dimensions for vertical rendering.
        """
        print(self.term.clear(), end="", flush=True)
        print(self.term.hide_cursor(), end="", flush=True)
        self.current_x = 0
        self.current_y = 0
        self.height = self.term.height
        self.width = self.term.width

        # Fill entire terminal with black background
        self.fill_background(BG)

    def refresh_dims(self):
        """Update cached terminal dimensions.

        Called on terminal resize to maintain accurate height/width.
        """
        self.height = self.term.height
        self.width = self.term.width

    def fill_background(self, bg_rgb: tuple[int, int, int]):
        """Fill the entire terminal with spaces using the specified background color.

        Args:
            bg_rgb (tuple[int, int, int]): RGB tuple for background color
        """
        bg_color = self._to_term_bg(bg_rgb)
        space_char = " "

        # Fill entire terminal with black background spaces
        for row in range(self.height):
            for col in range(self.width):
                print(
                    self.term.move_yx(row, col)
                    + bg_color
                    + space_char
                    + self.term.normal,
                    end="",
                    flush=True,
                )

    def draw_text(self, text: str):
        """Append streamed text to the screen at current cursor position.

        Args:
            text (str): The text content to render
        """
        # For now, just print text (horizontal flow)
        # Later phases will use cursor positioning for vertical display
        print(text, end="", flush=True)

        # Update cursor position tracking
        for char in text:
            if char == "\n":
                self.current_x = 0
                self.current_y += 1
            else:
                self.current_x += 1

    def draw_char(self, row: int, col: int, ch: str):
        """Draw a single character at specific coordinates.

        Args:
            row (int): Row coordinate (0-based)
            col (int): Column coordinate (0-based)
            ch (str): Single character to render
        """
        print(self.term.move_yx(row, col) + ch, end="", flush=True)
        self.current_x = col
        self.current_y = row

    def draw_cell(
        self,
        row: int,
        col: int,
        ch: str,
        fg_rgb: tuple[int, int, int],
        bg_rgb: tuple[int, int, int],
    ):
        """Draw a single character with specific foreground and background colors.

        Args:
            row (int): Row coordinate (0-based)
            col (int): Column coordinate (0-based)
            ch (str): Single character to render
            fg_rgb (tuple[int, int, int]): RGB tuple for foreground color
            bg_rgb (tuple[int, int, int]): RGB tuple for background color
        """
        fg_color = self._to_term_color(fg_rgb)
        bg_color = self._to_term_bg(bg_rgb)

        # Use a more efficient approach - build the output string first
        output = (
            self.term.move_yx(row, col) + fg_color + bg_color + ch + self.term.normal
        )
        print(output, end="", flush=True)
        self.current_x = col
        self.current_y = row

    def _to_term_color(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to blessed terminal color string.

        Attempts truecolor first, falls back to nearest 256-color if unsupported.

        Args:
            rgb (tuple[int, int, int]): RGB color tuple

        Returns:
            str: Blessed color string
        """
        try:
            return self.term.color_rgb(*rgb)
        except Exception:
            # Fallback to nearest 256-color approximation
            r, g, b = rgb
            # Simple approximation: convert to 6x6x6 color cube
            r_idx = min(5, r // 51)
            g_idx = min(5, g // 51)
            b_idx = min(5, b // 51)
            color_index = 16 + (r_idx * 36) + (g_idx * 6) + b_idx
            return self.term.color(color_index)

    def _to_term_bg(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to blessed terminal background color string.

        Attempts truecolor first, falls back to nearest 256-color if unsupported.

        Args:
            rgb (tuple[int, int, int]): RGB color tuple

        Returns:
            str: Blessed background color string
        """
        try:
            return self.term.on_color_rgb(*rgb)
        except Exception:
            # Fallback to nearest 256-color approximation
            r, g, b = rgb
            # Simple approximation: convert to 6x6x6 color cube
            r_idx = min(5, r // 51)
            g_idx = min(5, g // 51)
            b_idx = min(5, b // 51)
            color_index = 16 + (r_idx * 36) + (g_idx * 6) + b_idx
            return self.term.on_color(color_index)

    def supports_truecolor(self) -> bool:
        """Check if terminal supports truecolor (24-bit RGB).

        Returns:
            bool: True if truecolor is supported, False otherwise
        """
        return hasattr(self.term, "color_rgb") and hasattr(self.term, "on_color_rgb")

    def draw_text_at(self, x: int, y: int, text: str):
        """Draw text at specific coordinates (for future vertical display).

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            text (str): The text content to render
        """
        print(self.term.move_xy(x, y) + text, end="", flush=True)
        self.current_x = x + len(text)
        self.current_y = y

    def finalize(self):
        """Restore terminal to normal state.

        Shows the cursor and ensures terminal is in normal mode.
        """
        print(self.term.normal_cursor(), end="", flush=True)
