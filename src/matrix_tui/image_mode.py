"""Image visualization mode for Matrix Rain TUI.

This module provides functionality to display images through the rain effect,
similar to how Neo sees the Matrix.
"""

from typing import List, Optional, Tuple

try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class ImageMap:
    """Converts an image to a brightness map for modulating the rain effect.

    The brightness map is used to control which columns are active and how
    bright characters appear at each position.
    """

    def __init__(
        self,
        image_path: str,
        terminal_width: int,
        terminal_height: int,
        invert: bool = False,
    ):
        """Initialize the ImageMap from an image file.

        Args:
            image_path: Path to the image file
            terminal_width: Terminal width in characters
            terminal_height: Terminal height in characters
            invert: If True, dark areas become bright and vice versa

        Raises:
            ImportError: If Pillow is not installed
            FileNotFoundError: If image file doesn't exist
            PIL.UnidentifiedImageError: If file is not a valid image
        """
        if not PILLOW_AVAILABLE:
            raise ImportError(
                "Pillow is required for image mode. "
                "Install with: pip install Pillow>=10.0.0"
            )

        self.terminal_width = terminal_width
        self.terminal_height = terminal_height
        self.invert = invert

        # Load and process the image
        with Image.open(image_path) as img:
            # Convert to grayscale
            grayscale = img.convert("L")

            # Resize to terminal dimensions
            resized = grayscale.resize(
                (terminal_width, terminal_height), Image.Resampling.LANCZOS
            )

            # Convert to brightness values (0.0 - 1.0)
            self._brightness_map: List[List[float]] = []
            for y in range(terminal_height):
                row = []
                for x in range(terminal_width):
                    pixel = resized.getpixel((x, y))
                    brightness = pixel / 255.0
                    if invert:
                        brightness = 1.0 - brightness
                    row.append(brightness)
                self._brightness_map.append(row)

        # Pre-calculate column averages for activity control
        self._column_averages: List[float] = []
        for col in range(terminal_width):
            total = sum(
                self._brightness_map[row][col] for row in range(terminal_height)
            )
            self._column_averages.append(total / terminal_height)

    def get_brightness(self, row: int, col: int) -> float:
        """Get brightness at a specific position.

        Args:
            row: Row coordinate (0-based)
            col: Column coordinate (0-based)

        Returns:
            Brightness value from 0.0 (dark) to 1.0 (bright)
        """
        if 0 <= row < self.terminal_height and 0 <= col < self.terminal_width:
            return self._brightness_map[row][col]
        return 0.0

    def get_column_activity(self, col: int) -> float:
        """Get average brightness for a column.

        This is used to determine how active a column should be.

        Args:
            col: Column coordinate (0-based)

        Returns:
            Average brightness for the column (0.0 - 1.0)
        """
        if 0 <= col < self.terminal_width:
            return self._column_averages[col]
        return 0.0

    def resize(self, new_width: int, new_height: int) -> None:
        """Resize the brightness map to new terminal dimensions.

        Args:
            new_width: New terminal width
            new_height: New terminal height
        """
        # This would require re-loading the image, so for simplicity
        # we just update dimensions (the map will be clipped/extended)
        self.terminal_width = new_width
        self.terminal_height = new_height


class ImageModeController:
    """Controls the image visualization mode.

    This controller modulates the rain effect based on an image:
    - Bright image areas = more active, brighter rain
    - Dark image areas = less/no activity, dimmer characters
    """

    def __init__(
        self,
        image_path: str,
        terminal_width: int,
        terminal_height: int,
        activity_threshold: float = 0.2,
        invert: bool = False,
    ):
        """Initialize the ImageModeController.

        Args:
            image_path: Path to the image file
            terminal_width: Terminal width in characters
            terminal_height: Terminal height in characters
            activity_threshold: Minimum brightness for column activity (0.0-1.0)
            invert: If True, invert the image (dark becomes bright)

        Raises:
            ImportError: If Pillow is not installed
            FileNotFoundError: If image file doesn't exist
        """
        self.image_map = ImageMap(
            image_path, terminal_width, terminal_height, invert=invert
        )
        self.activity_threshold = activity_threshold

    def should_column_be_active(self, col: int) -> bool:
        """Determine if a column should be active based on image brightness.

        Columns in bright image areas are active, dark areas are inactive.

        Args:
            col: Column coordinate (0-based)

        Returns:
            True if column should be active, False otherwise
        """
        activity = self.image_map.get_column_activity(col)
        return activity >= self.activity_threshold

    def get_position_brightness(self, row: int, col: int) -> float:
        """Get brightness modifier for a specific position.

        This is used to modulate character brightness based on the image.

        Args:
            row: Row coordinate (0-based)
            col: Column coordinate (0-based)

        Returns:
            Brightness modifier from 0.0 (completely dark) to 1.0 (full brightness)
        """
        return self.image_map.get_brightness(row, col)

    def get_active_columns(self, total_columns: int) -> List[int]:
        """Get list of columns that should be active based on the image.

        Args:
            total_columns: Total number of columns requested

        Returns:
            List of column indices that should be active
        """
        active = []
        for col in range(min(total_columns, self.image_map.terminal_width)):
            if self.should_column_be_active(col):
                active.append(col)
        return active

    def resize(self, new_width: int, new_height: int) -> None:
        """Handle terminal resize.

        Args:
            new_width: New terminal width
            new_height: New terminal height
        """
        self.image_map.resize(new_width, new_height)


def is_pillow_available() -> bool:
    """Check if Pillow is available for image mode.

    Returns:
        True if Pillow is installed, False otherwise
    """
    return PILLOW_AVAILABLE
