"""Tests for the animation system."""

import pytest

from matrix_tui.animation import (
    ANIMATION_PRESETS,
    AnimationConfig,
    ColumnAnimationState,
    get_animation_preset,
    get_default_animation_config,
    get_random_mutation_char,
    MUTATION_CHARACTERS,
)


class TestAnimationConfig:
    """Tests for AnimationConfig dataclass."""

    def test_default_values(self):
        """Test default animation config values."""
        config = AnimationConfig()
        assert config.min_fall_speed == 0.5
        assert config.max_fall_speed == 2.0
        assert config.min_trail_length == 10
        assert config.max_trail_length == 30
        assert config.min_start_delay == 0.0
        assert config.max_start_delay == 2.0
        assert config.flash_probability == 0.02
        assert config.mutation_probability == 0.01
        assert config.column_density == 0.6

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = AnimationConfig(
            min_fall_speed=1.0,
            max_fall_speed=5.0,
            min_trail_length=5,
            max_trail_length=50,
            flash_probability=0.1,
        )
        assert config.min_fall_speed == 1.0
        assert config.max_fall_speed == 5.0
        assert config.min_trail_length == 5
        assert config.max_trail_length == 50
        assert config.flash_probability == 0.1

    def test_random_fall_speed(self):
        """Test random fall speed generation."""
        config = AnimationConfig(min_fall_speed=1.0, max_fall_speed=2.0)
        for _ in range(100):
            speed = config.random_fall_speed()
            assert 1.0 <= speed <= 2.0

    def test_random_trail_length(self):
        """Test random trail length generation."""
        config = AnimationConfig(min_trail_length=10, max_trail_length=20)
        for _ in range(100):
            length = config.random_trail_length()
            assert 10 <= length <= 20

    def test_random_start_delay(self):
        """Test random start delay generation."""
        config = AnimationConfig(min_start_delay=0.5, max_start_delay=1.5)
        for _ in range(100):
            delay = config.random_start_delay()
            assert 0.5 <= delay <= 1.5

    def test_should_flash_probability(self):
        """Test flash probability check."""
        # With 0% probability, should never flash
        config = AnimationConfig(flash_probability=0.0)
        for _ in range(100):
            assert not config.should_flash()

        # With 100% probability, should always flash
        config = AnimationConfig(flash_probability=1.0)
        for _ in range(100):
            assert config.should_flash()

    def test_should_mutate_probability(self):
        """Test mutation probability check."""
        # With 0% probability, should never mutate
        config = AnimationConfig(mutation_probability=0.0)
        for _ in range(100):
            assert not config.should_mutate()

        # With 100% probability, should always mutate
        config = AnimationConfig(mutation_probability=1.0)
        for _ in range(100):
            assert config.should_mutate()


class TestColumnAnimationState:
    """Tests for ColumnAnimationState dataclass."""

    def test_default_values(self):
        """Test default column animation state values."""
        state = ColumnAnimationState()
        assert state.fall_speed == 1.0
        assert state.trail_length == 20
        assert state.start_delay == 0.0
        assert state.is_active is True
        assert state.accumulated_time == 0.0
        assert state.flash_active is False
        assert state.flash_duration == 0.0

    def test_from_config(self):
        """Test creating state from config."""
        config = AnimationConfig(
            min_fall_speed=1.0,
            max_fall_speed=2.0,
            min_trail_length=10,
            max_trail_length=20,
            min_start_delay=0.5,
            max_start_delay=1.0,
            column_density=1.0,  # Always active
        )
        state = ColumnAnimationState.from_config(config)
        assert 1.0 <= state.fall_speed <= 2.0
        assert 10 <= state.trail_length <= 20
        assert 0.5 <= state.start_delay <= 1.0
        assert state.is_active is True

    def test_update_time(self):
        """Test updating animation state with delta time."""
        state = ColumnAnimationState()
        state.update(0.5)
        assert state.accumulated_time == 0.5
        state.update(0.3)
        assert state.accumulated_time == 0.8

    def test_trigger_flash(self):
        """Test triggering a flash effect."""
        state = ColumnAnimationState()
        assert not state.flash_active

        state.trigger_flash(0.2)
        assert state.flash_active
        assert state.flash_duration == 0.2

    def test_flash_duration_decreases(self):
        """Test that flash duration decreases over time."""
        state = ColumnAnimationState()
        state.trigger_flash(0.2)

        state.update(0.1)
        assert state.flash_active
        assert state.flash_duration == pytest.approx(0.1, abs=0.001)

        state.update(0.1)
        assert not state.flash_active
        assert state.flash_duration == 0.0


class TestAnimationPresets:
    """Tests for animation presets."""

    def test_all_presets_exist(self):
        """Test that all expected presets exist."""
        expected = ["calm", "default", "intense", "chaos"]
        for name in expected:
            assert name in ANIMATION_PRESETS
            assert isinstance(ANIMATION_PRESETS[name], AnimationConfig)

    def test_calm_preset(self):
        """Test calm preset has slow, sparse settings."""
        calm = ANIMATION_PRESETS["calm"]
        assert calm.min_fall_speed < 0.5
        assert calm.column_density < 0.5
        assert calm.flash_probability < 0.01

    def test_chaos_preset(self):
        """Test chaos preset has fast, dense settings."""
        chaos = ANIMATION_PRESETS["chaos"]
        assert chaos.max_fall_speed > 3.0
        assert chaos.column_density > 0.8
        assert chaos.flash_probability > 0.05

    def test_get_animation_preset(self):
        """Test get_animation_preset function."""
        preset = get_animation_preset("default")
        assert preset is not None
        assert isinstance(preset, AnimationConfig)

    def test_get_animation_preset_nonexistent(self):
        """Test get_animation_preset with nonexistent preset."""
        preset = get_animation_preset("nonexistent")
        assert preset is None

    def test_get_default_animation_config(self):
        """Test get_default_animation_config function."""
        config = get_default_animation_config()
        assert config is not None
        assert config == ANIMATION_PRESETS["default"]


class TestMutationCharacters:
    """Tests for mutation character generation."""

    def test_mutation_characters_not_empty(self):
        """Test that mutation characters string is not empty."""
        assert len(MUTATION_CHARACTERS) > 0

    def test_get_random_mutation_char(self):
        """Test getting random mutation characters."""
        chars_seen = set()
        for _ in range(1000):
            char = get_random_mutation_char()
            assert len(char) == 1
            assert char in MUTATION_CHARACTERS
            chars_seen.add(char)

        # Should see a variety of characters
        assert len(chars_seen) > 10

    def test_mutation_characters_include_katakana(self):
        """Test that mutation characters include half-width katakana."""
        # Check for some katakana characters
        assert "ｱ" in MUTATION_CHARACTERS or "ｳ" in MUTATION_CHARACTERS

    def test_mutation_characters_include_numbers(self):
        """Test that mutation characters include numbers."""
        for digit in "0123456789":
            assert digit in MUTATION_CHARACTERS

    def test_mutation_characters_include_letters(self):
        """Test that mutation characters include uppercase letters."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert letter in MUTATION_CHARACTERS
