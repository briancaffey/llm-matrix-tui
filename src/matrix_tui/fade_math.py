"""Mathematical functions for character fade effects."""

import math
from typing import Tuple


def linear_fade(progress: float) -> float:
    """Linear fade function.

    Args:
        progress: Progress from 0.0 (newest) to 1.0 (oldest)

    Returns:
        Fade intensity from 1.0 (full color) to 0.0 (black)
    """
    return max(0.0, 1.0 - progress)


def quadratic_fade(progress: float) -> float:
    """Quadratic fade function for smoother transition.

    Args:
        progress: Progress from 0.0 (newest) to 1.0 (oldest)

    Returns:
        Fade intensity from 1.0 (full color) to 0.0 (black)
    """
    return max(0.0, (1.0 - progress) ** 2)


def exponential_fade(progress: float) -> float:
    """Exponential fade function for rapid initial fade.

    Args:
        progress: Progress from 0.0 (newest) to 1.0 (oldest)

    Returns:
        Fade intensity from 1.0 (full color) to 0.0 (black)
    """
    if progress >= 1.0:
        return 0.0
    # Use exponential decay with base 2 for smooth fade
    return max(0.0, math.exp(-3.0 * progress))


def interpolate_color(start_color: Tuple[int, int, int], end_color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Interpolate between two RGB colors.

    Args:
        start_color: Starting RGB color tuple
        end_color: Ending RGB color tuple
        factor: Interpolation factor from 0.0 (start) to 1.0 (end)

    Returns:
        Interpolated RGB color tuple
    """
    r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
    g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
    b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)

    # Clamp values to valid RGB range
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def calculate_fade_color(base_color: Tuple[int, int, int], fade_intensity: float) -> Tuple[int, int, int]:
    """Calculate the faded color based on intensity.

    Args:
        base_color: Base RGB color to fade from
        fade_intensity: Intensity from 1.0 (full color) to 0.0 (black)

    Returns:
        Faded RGB color tuple
    """
    black = (0, 0, 0)
    return interpolate_color(base_color, black, 1.0 - fade_intensity)


# Fade function mapping
FADE_FUNCTIONS = {
    "linear": linear_fade,
    "quadratic": quadratic_fade,
    "exponential": exponential_fade,
}
