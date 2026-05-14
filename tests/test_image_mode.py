"""Tests for image visualization mode."""

import tempfile
from pathlib import Path

import pytest

from matrix_tui.image_mode import (
    ImageMap,
    ImageModeController,
    is_pillow_available,
)

# Skip all tests if Pillow is not available
pytestmark = pytest.mark.skipif(
    not is_pillow_available(),
    reason="Pillow is required for image mode tests",
)


def create_test_image(width: int, height: int, color: tuple) -> str:
    """Create a test image file and return its path.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color: RGB tuple for fill color

    Returns:
        Path to the temporary image file
    """
    from PIL import Image

    img = Image.new("RGB", (width, height), color)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name)
        return f.name


def create_gradient_image(width: int, height: int) -> str:
    """Create a horizontal gradient test image.

    Left side is black, right side is white.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Path to the temporary image file
    """
    from PIL import Image

    img = Image.new("L", (width, height))
    for x in range(width):
        brightness = int((x / width) * 255)
        for y in range(height):
            img.putpixel((x, y), brightness)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name)
        return f.name


class TestImageMap:
    """Tests for ImageMap class."""

    def test_create_from_white_image(self):
        """Test creating map from all-white image."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            image_map = ImageMap(path, 20, 10)

            # All positions should be bright (1.0)
            assert image_map.get_brightness(0, 0) == pytest.approx(1.0, abs=0.01)
            assert image_map.get_brightness(5, 10) == pytest.approx(1.0, abs=0.01)
            assert image_map.get_column_activity(0) == pytest.approx(1.0, abs=0.01)
        finally:
            Path(path).unlink()

    def test_create_from_black_image(self):
        """Test creating map from all-black image."""
        path = create_test_image(100, 50, (0, 0, 0))
        try:
            image_map = ImageMap(path, 20, 10)

            # All positions should be dark (0.0)
            assert image_map.get_brightness(0, 0) == pytest.approx(0.0, abs=0.01)
            assert image_map.get_brightness(5, 10) == pytest.approx(0.0, abs=0.01)
            assert image_map.get_column_activity(0) == pytest.approx(0.0, abs=0.01)
        finally:
            Path(path).unlink()

    def test_create_from_gradient(self):
        """Test creating map from gradient image."""
        path = create_gradient_image(100, 50)
        try:
            image_map = ImageMap(path, 20, 10)

            # Left side should be dark, right side should be bright
            left_activity = image_map.get_column_activity(0)
            right_activity = image_map.get_column_activity(19)

            assert left_activity < 0.3
            assert right_activity > 0.7
        finally:
            Path(path).unlink()

    def test_invert_mode(self):
        """Test invert mode reverses brightness."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            # Without invert - should be bright
            normal_map = ImageMap(path, 20, 10, invert=False)
            assert normal_map.get_brightness(0, 0) == pytest.approx(1.0, abs=0.01)

            # With invert - should be dark
            inverted_map = ImageMap(path, 20, 10, invert=True)
            assert inverted_map.get_brightness(0, 0) == pytest.approx(0.0, abs=0.01)
        finally:
            Path(path).unlink()

    def test_out_of_bounds_returns_zero(self):
        """Test that out-of-bounds positions return 0."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            image_map = ImageMap(path, 20, 10)

            assert image_map.get_brightness(-1, 0) == 0.0
            assert image_map.get_brightness(0, -1) == 0.0
            assert image_map.get_brightness(100, 0) == 0.0
            assert image_map.get_brightness(0, 100) == 0.0
            assert image_map.get_column_activity(-1) == 0.0
            assert image_map.get_column_activity(100) == 0.0
        finally:
            Path(path).unlink()


class TestImageModeController:
    """Tests for ImageModeController class."""

    def test_should_column_be_active_bright(self):
        """Test column activity for bright image areas."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            controller = ImageModeController(path, 20, 10, activity_threshold=0.5)

            # All columns should be active (image is all white)
            for col in range(20):
                assert controller.should_column_be_active(col)
        finally:
            Path(path).unlink()

    def test_should_column_be_active_dark(self):
        """Test column activity for dark image areas."""
        path = create_test_image(100, 50, (0, 0, 0))
        try:
            controller = ImageModeController(path, 20, 10, activity_threshold=0.5)

            # No columns should be active (image is all black)
            for col in range(20):
                assert not controller.should_column_be_active(col)
        finally:
            Path(path).unlink()

    def test_activity_threshold(self):
        """Test activity threshold affects column selection."""
        path = create_test_image(100, 50, (128, 128, 128))  # 50% gray
        try:
            # With low threshold, should be active
            low_threshold = ImageModeController(path, 20, 10, activity_threshold=0.3)
            assert low_threshold.should_column_be_active(0)

            # With high threshold, should not be active
            high_threshold = ImageModeController(path, 20, 10, activity_threshold=0.7)
            assert not high_threshold.should_column_be_active(0)
        finally:
            Path(path).unlink()

    def test_get_position_brightness(self):
        """Test getting brightness at specific position."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            controller = ImageModeController(path, 20, 10)

            brightness = controller.get_position_brightness(5, 10)
            assert brightness == pytest.approx(1.0, abs=0.01)
        finally:
            Path(path).unlink()

    def test_get_active_columns(self):
        """Test getting list of active columns."""
        path = create_test_image(100, 50, (255, 255, 255))
        try:
            controller = ImageModeController(path, 20, 10, activity_threshold=0.5)

            active_cols = controller.get_active_columns(20)
            # All columns should be active for white image
            assert len(active_cols) == 20
            assert list(range(20)) == active_cols
        finally:
            Path(path).unlink()

    def test_get_active_columns_dark_image(self):
        """Test getting active columns for dark image."""
        path = create_test_image(100, 50, (0, 0, 0))
        try:
            controller = ImageModeController(path, 20, 10, activity_threshold=0.5)

            active_cols = controller.get_active_columns(20)
            # No columns should be active for black image
            assert len(active_cols) == 0
        finally:
            Path(path).unlink()


class TestPillowAvailability:
    """Tests for Pillow availability checking."""

    def test_is_pillow_available(self):
        """Test is_pillow_available returns True when Pillow is installed."""
        # This test runs only when Pillow is available (due to pytestmark)
        assert is_pillow_available() is True


class TestImageMapFileErrors:
    """Tests for file error handling."""

    def test_nonexistent_file(self):
        """Test that FileNotFoundError is raised for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            ImageMap("/nonexistent/path/to/image.png", 20, 10)

    def test_invalid_image_file(self):
        """Test that error is raised for invalid image file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"not an image")
            f.flush()
            path = f.name

        try:
            with pytest.raises(Exception):  # PIL.UnidentifiedImageError
                ImageMap(path, 20, 10)
        finally:
            Path(path).unlink()
