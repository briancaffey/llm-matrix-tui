"""Tests for the color theme system."""

import json
import tempfile
from pathlib import Path

import pytest

from matrix_tui.themes import (
    BUILTIN_THEMES,
    ColorTheme,
    ThemeRegistry,
    get_default_theme,
    get_theme,
    list_themes,
    load_custom_theme,
)


class TestColorTheme:
    """Tests for ColorTheme dataclass."""

    def test_create_theme(self):
        """Test creating a theme with all attributes."""
        theme = ColorTheme(
            name="test",
            head_fg=(255, 255, 255),
            trail_fg=(0, 255, 0),
            background=(0, 0, 0),
            description="Test theme",
        )
        assert theme.name == "test"
        assert theme.head_fg == (255, 255, 255)
        assert theme.trail_fg == (0, 255, 0)
        assert theme.background == (0, 0, 0)
        assert theme.description == "Test theme"

    def test_default_background(self):
        """Test that background defaults to black."""
        theme = ColorTheme(
            name="test",
            head_fg=(255, 255, 255),
            trail_fg=(0, 255, 0),
        )
        assert theme.background == (0, 0, 0)

    def test_to_dict(self):
        """Test converting theme to dictionary."""
        theme = ColorTheme(
            name="test",
            head_fg=(255, 255, 255),
            trail_fg=(0, 255, 0),
            background=(10, 20, 30),
            description="Test theme",
        )
        data = theme.to_dict()
        assert data["name"] == "test"
        assert data["head_fg"] == [255, 255, 255]
        assert data["trail_fg"] == [0, 255, 0]
        assert data["background"] == [10, 20, 30]
        assert data["description"] == "Test theme"

    def test_from_dict(self):
        """Test creating theme from dictionary."""
        data = {
            "name": "test",
            "head_fg": [255, 255, 255],
            "trail_fg": [0, 255, 0],
            "background": [10, 20, 30],
            "description": "Test theme",
        }
        theme = ColorTheme.from_dict(data)
        assert theme.name == "test"
        assert theme.head_fg == (255, 255, 255)
        assert theme.trail_fg == (0, 255, 0)
        assert theme.background == (10, 20, 30)
        assert theme.description == "Test theme"

    def test_from_dict_default_background(self):
        """Test that background defaults when not in dict."""
        data = {
            "name": "test",
            "head_fg": [255, 255, 255],
            "trail_fg": [0, 255, 0],
        }
        theme = ColorTheme.from_dict(data)
        assert theme.background == (0, 0, 0)

    def test_from_json_file(self):
        """Test loading theme from JSON file."""
        theme_data = {
            "name": "custom",
            "head_fg": [200, 200, 200],
            "trail_fg": [100, 100, 100],
            "background": [5, 5, 5],
            "description": "Custom theme",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(theme_data, f)
            f.flush()
            theme = ColorTheme.from_json_file(f.name)

        assert theme.name == "custom"
        assert theme.head_fg == (200, 200, 200)
        assert theme.trail_fg == (100, 100, 100)
        assert theme.background == (5, 5, 5)
        assert theme.description == "Custom theme"

        # Clean up
        Path(f.name).unlink()


class TestBuiltinThemes:
    """Tests for builtin themes."""

    def test_builtin_themes_exist(self):
        """Test that all expected builtin themes exist."""
        expected_themes = [
            "classic",
            "nvidia",
            "amber",
            "cyan",
            "hacker",
            "purple",
            "fire",
            "ice",
            "blood",
            "gold",
        ]
        for theme_name in expected_themes:
            assert theme_name in BUILTIN_THEMES
            theme = BUILTIN_THEMES[theme_name]
            assert isinstance(theme, ColorTheme)
            assert theme.name == theme_name

    def test_nvidia_is_default(self):
        """Test that nvidia is the default theme."""
        default = get_default_theme()
        assert default.name == "nvidia"
        assert default.trail_fg == (118, 185, 0)  # NVIDIA green

    def test_classic_matrix_green(self):
        """Test classic theme has Matrix green."""
        classic = BUILTIN_THEMES["classic"]
        assert classic.trail_fg == (0, 255, 0)  # Pure green

    def test_all_themes_have_descriptions(self):
        """Test that all builtin themes have descriptions."""
        for name, theme in BUILTIN_THEMES.items():
            assert theme.description, f"Theme {name} has no description"


class TestThemeRegistry:
    """Tests for ThemeRegistry."""

    def test_get_builtin_theme(self):
        """Test getting a builtin theme."""
        registry = ThemeRegistry()
        theme = registry.get("nvidia")
        assert theme is not None
        assert theme.name == "nvidia"

    def test_get_nonexistent_theme(self):
        """Test getting a theme that doesn't exist."""
        registry = ThemeRegistry()
        theme = registry.get("nonexistent")
        assert theme is None

    def test_register_custom_theme(self):
        """Test registering a custom theme."""
        registry = ThemeRegistry()
        custom = ColorTheme(
            name="custom",
            head_fg=(255, 0, 0),
            trail_fg=(128, 0, 0),
        )
        registry.register(custom)
        retrieved = registry.get("custom")
        assert retrieved is not None
        assert retrieved.name == "custom"
        assert retrieved.head_fg == (255, 0, 0)

    def test_list_themes(self):
        """Test listing all themes."""
        registry = ThemeRegistry()
        themes = registry.list_themes()
        assert len(themes) >= 10  # At least the builtin themes
        assert "nvidia" in themes
        assert "classic" in themes

    def test_load_custom_theme(self):
        """Test loading a custom theme from file."""
        theme_data = {
            "name": "file_custom",
            "head_fg": [255, 128, 0],
            "trail_fg": [200, 100, 0],
            "description": "File custom theme",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(theme_data, f)
            f.flush()

            registry = ThemeRegistry()
            theme = registry.load_custom_theme(f.name)

        assert theme.name == "file_custom"
        # Theme should also be registered
        assert registry.get("file_custom") is not None

        # Clean up
        Path(f.name).unlink()


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_theme(self):
        """Test get_theme function."""
        theme = get_theme("classic")
        assert theme is not None
        assert theme.name == "classic"

    def test_get_theme_nonexistent(self):
        """Test get_theme with nonexistent theme."""
        theme = get_theme("nonexistent")
        assert theme is None

    def test_list_themes_function(self):
        """Test list_themes function."""
        themes = list_themes()
        assert isinstance(themes, dict)
        assert len(themes) >= 10
        assert "nvidia" in themes

    def test_load_custom_theme_function(self):
        """Test load_custom_theme function."""
        theme_data = {
            "name": "func_custom",
            "head_fg": [100, 200, 100],
            "trail_fg": [50, 100, 50],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(theme_data, f)
            f.flush()

            theme = load_custom_theme(f.name)

        assert theme.name == "func_custom"

        # Clean up
        Path(f.name).unlink()
