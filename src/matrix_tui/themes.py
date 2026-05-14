"""Color theme system for Matrix Rain TUI."""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class ColorTheme:
    """Represents a color theme for the Matrix Rain effect.

    Attributes:
        name: Theme identifier (e.g., 'classic', 'nvidia')
        head_fg: RGB tuple for the newest character (head of the trail)
        trail_fg: RGB tuple for trailing characters
        background: RGB tuple for background color
        description: Human-readable description of the theme
    """

    name: str
    head_fg: Tuple[int, int, int]
    trail_fg: Tuple[int, int, int]
    background: Tuple[int, int, int] = (0, 0, 0)
    description: str = ""

    def to_dict(self) -> Dict:
        """Convert theme to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "head_fg": list(self.head_fg),
            "trail_fg": list(self.trail_fg),
            "background": list(self.background),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ColorTheme":
        """Create a ColorTheme from a dictionary."""
        return cls(
            name=data["name"],
            head_fg=tuple(data["head_fg"]),
            trail_fg=tuple(data["trail_fg"]),
            background=tuple(data.get("background", [0, 0, 0])),
            description=data.get("description", ""),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "ColorTheme":
        """Load a ColorTheme from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


# Builtin themes
BUILTIN_THEMES: Dict[str, ColorTheme] = {
    "classic": ColorTheme(
        name="classic",
        head_fg=(255, 255, 255),
        trail_fg=(0, 255, 0),
        background=(0, 0, 0),
        description="Classic Matrix green (#00FF00)",
    ),
    "nvidia": ColorTheme(
        name="nvidia",
        head_fg=(255, 255, 255),
        trail_fg=(118, 185, 0),
        background=(0, 0, 0),
        description="NVIDIA green (#76B900) - default theme",
    ),
    "amber": ColorTheme(
        name="amber",
        head_fg=(255, 255, 200),
        trail_fg=(255, 176, 0),
        background=(0, 0, 0),
        description="Retro amber terminal",
    ),
    "cyan": ColorTheme(
        name="cyan",
        head_fg=(255, 255, 255),
        trail_fg=(0, 255, 255),
        background=(0, 0, 0),
        description="Cyan/aqua theme",
    ),
    "hacker": ColorTheme(
        name="hacker",
        head_fg=(255, 50, 50),
        trail_fg=(50, 100, 255),
        background=(0, 0, 0),
        description="Red head, blue trail",
    ),
    "purple": ColorTheme(
        name="purple",
        head_fg=(255, 200, 255),
        trail_fg=(148, 0, 211),
        background=(0, 0, 0),
        description="Purple/violet theme",
    ),
    "fire": ColorTheme(
        name="fire",
        head_fg=(255, 255, 100),
        trail_fg=(255, 69, 0),
        background=(0, 0, 0),
        description="Yellow head, orange-red trail",
    ),
    "ice": ColorTheme(
        name="ice",
        head_fg=(255, 255, 255),
        trail_fg=(135, 206, 250),
        background=(0, 0, 30),
        description="Ice blue with dark blue background",
    ),
    "blood": ColorTheme(
        name="blood",
        head_fg=(255, 100, 100),
        trail_fg=(139, 0, 0),
        background=(0, 0, 0),
        description="Dark red theme",
    ),
    "gold": ColorTheme(
        name="gold",
        head_fg=(255, 255, 200),
        trail_fg=(255, 215, 0),
        background=(0, 0, 0),
        description="Golden theme",
    ),
}


class ThemeRegistry:
    """Registry for managing color themes."""

    def __init__(self):
        """Initialize the theme registry with builtin themes."""
        self._themes: Dict[str, ColorTheme] = dict(BUILTIN_THEMES)

    def get(self, name: str) -> Optional[ColorTheme]:
        """Get a theme by name.

        Args:
            name: Theme name to look up

        Returns:
            ColorTheme if found, None otherwise
        """
        return self._themes.get(name)

    def register(self, theme: ColorTheme) -> None:
        """Register a new theme.

        Args:
            theme: ColorTheme to register
        """
        self._themes[theme.name] = theme

    def list_themes(self) -> Dict[str, ColorTheme]:
        """Get all registered themes.

        Returns:
            Dictionary mapping theme names to ColorTheme objects
        """
        return dict(self._themes)

    def load_custom_theme(self, path: str) -> ColorTheme:
        """Load a custom theme from a JSON file and register it.

        Args:
            path: Path to the JSON theme file

        Returns:
            The loaded ColorTheme
        """
        theme = ColorTheme.from_json_file(path)
        self.register(theme)
        return theme


# Default theme registry instance
_default_registry = ThemeRegistry()


def get_theme(name: str) -> Optional[ColorTheme]:
    """Get a theme by name from the default registry.

    Args:
        name: Theme name to look up

    Returns:
        ColorTheme if found, None otherwise
    """
    return _default_registry.get(name)


def list_themes() -> Dict[str, ColorTheme]:
    """Get all registered themes from the default registry.

    Returns:
        Dictionary mapping theme names to ColorTheme objects
    """
    return _default_registry.list_themes()


def load_custom_theme(path: str) -> ColorTheme:
    """Load a custom theme from a JSON file.

    Args:
        path: Path to the JSON theme file

    Returns:
        The loaded ColorTheme
    """
    return _default_registry.load_custom_theme(path)


def get_default_theme() -> ColorTheme:
    """Get the default theme (nvidia).

    Returns:
        The default NVIDIA theme
    """
    return BUILTIN_THEMES["nvidia"]
