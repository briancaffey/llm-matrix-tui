"""Animation configuration and state management for Matrix Rain TUI."""

import random
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class AnimationConfig:
    """Global animation configuration settings.

    Attributes:
        min_fall_speed: Minimum fall speed multiplier (1.0 = normal speed)
        max_fall_speed: Maximum fall speed multiplier
        min_trail_length: Minimum trail length in characters
        max_trail_length: Maximum trail length in characters
        min_start_delay: Minimum delay before column starts (seconds)
        max_start_delay: Maximum delay before column starts (seconds)
        flash_probability: Probability of a flash effect on each character (0.0-1.0)
        mutation_probability: Probability of character mutation (0.0-1.0)
        column_density: Fraction of columns that should be active (0.0-1.0)
    """

    min_fall_speed: float = 0.5
    max_fall_speed: float = 2.0
    min_trail_length: int = 10
    max_trail_length: int = 30
    min_start_delay: float = 0.0
    max_start_delay: float = 2.0
    flash_probability: float = 0.02
    mutation_probability: float = 0.01
    column_density: float = 0.6

    def random_fall_speed(self) -> float:
        """Generate a random fall speed within configured range."""
        return random.uniform(self.min_fall_speed, self.max_fall_speed)

    def random_trail_length(self) -> int:
        """Generate a random trail length within configured range."""
        return random.randint(self.min_trail_length, self.max_trail_length)

    def random_start_delay(self) -> float:
        """Generate a random start delay within configured range."""
        return random.uniform(self.min_start_delay, self.max_start_delay)

    def should_flash(self) -> bool:
        """Determine if a flash effect should occur."""
        return random.random() < self.flash_probability

    def should_mutate(self) -> bool:
        """Determine if a character should mutate."""
        return random.random() < self.mutation_probability


@dataclass
class ColumnAnimationState:
    """Per-column animation state.

    Attributes:
        fall_speed: Speed multiplier for this column (1.0 = normal)
        trail_length: Maximum trail length for this column
        start_delay: Delay before this column starts (seconds)
        is_active: Whether this column is currently active
        accumulated_time: Time accumulated for speed modulation
        flash_active: Whether a flash is currently active
        flash_duration: Remaining duration of flash effect
    """

    fall_speed: float = 1.0
    trail_length: int = 20
    start_delay: float = 0.0
    is_active: bool = True
    accumulated_time: float = 0.0
    flash_active: bool = False
    flash_duration: float = 0.0

    @classmethod
    def from_config(cls, config: AnimationConfig) -> "ColumnAnimationState":
        """Create a new ColumnAnimationState with randomized values from config."""
        return cls(
            fall_speed=config.random_fall_speed(),
            trail_length=config.random_trail_length(),
            start_delay=config.random_start_delay(),
            is_active=random.random() < config.column_density,
        )

    def update(self, delta_time: float) -> None:
        """Update animation state based on elapsed time.

        Args:
            delta_time: Time elapsed since last update (seconds)
        """
        self.accumulated_time += delta_time

        # Update flash duration
        if self.flash_active:
            self.flash_duration -= delta_time
            if self.flash_duration <= 0:
                self.flash_active = False
                self.flash_duration = 0.0

    def trigger_flash(self, duration: float = 0.1) -> None:
        """Trigger a flash effect on this column.

        Args:
            duration: How long the flash should last (seconds)
        """
        self.flash_active = True
        self.flash_duration = duration


# Animation presets
ANIMATION_PRESETS: Dict[str, AnimationConfig] = {
    "calm": AnimationConfig(
        min_fall_speed=0.3,
        max_fall_speed=0.8,
        min_trail_length=15,
        max_trail_length=40,
        min_start_delay=0.5,
        max_start_delay=3.0,
        flash_probability=0.005,
        mutation_probability=0.002,
        column_density=0.4,
    ),
    "default": AnimationConfig(
        min_fall_speed=0.5,
        max_fall_speed=2.0,
        min_trail_length=10,
        max_trail_length=30,
        min_start_delay=0.0,
        max_start_delay=2.0,
        flash_probability=0.02,
        mutation_probability=0.01,
        column_density=0.6,
    ),
    "intense": AnimationConfig(
        min_fall_speed=1.0,
        max_fall_speed=3.0,
        min_trail_length=8,
        max_trail_length=25,
        min_start_delay=0.0,
        max_start_delay=0.5,
        flash_probability=0.05,
        mutation_probability=0.03,
        column_density=0.8,
    ),
    "chaos": AnimationConfig(
        min_fall_speed=0.2,
        max_fall_speed=5.0,
        min_trail_length=5,
        max_trail_length=50,
        min_start_delay=0.0,
        max_start_delay=1.0,
        flash_probability=0.1,
        mutation_probability=0.08,
        column_density=0.9,
    ),
}


def get_animation_preset(name: str) -> Optional[AnimationConfig]:
    """Get an animation preset by name.

    Args:
        name: Preset name ('calm', 'default', 'intense', 'chaos')

    Returns:
        AnimationConfig if found, None otherwise
    """
    return ANIMATION_PRESETS.get(name)


def get_default_animation_config() -> AnimationConfig:
    """Get the default animation configuration.

    Returns:
        The default AnimationConfig
    """
    return ANIMATION_PRESETS["default"]


# Characters that can be used for mutation (Matrix-style)
MUTATION_CHARACTERS = (
    # Half-width katakana
    "ｦｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    # Numbers
    "0123456789"
    # Latin letters
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    # Special characters
    "@#$%^&*()_+-=[]{}|;:,.<>?"
)


def get_random_mutation_char() -> str:
    """Get a random character for mutation effect.

    Returns:
        A random character from the mutation character set
    """
    return random.choice(MUTATION_CHARACTERS)
