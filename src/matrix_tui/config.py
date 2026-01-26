"""Configuration management for Matrix Rain TUI."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def load_config(verbose=False):
    """Load configuration from environment variables.

    Args:
        verbose (bool): If True, print debug information

    Returns:
        dict: Configuration dictionary with OpenAI settings
    """
    # Try to load .env file from multiple possible locations
    current_dir = Path.cwd()
    project_root = current_dir

    # Look for .env file in current directory and parent directories
    env_paths = [
        current_dir / ".env",
        project_root / ".env",
        Path(__file__).parent.parent.parent / ".env",  # src/matrix_tui/../../.env
    ]

    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            env_loaded = True
            break

    if not env_loaded:
        # Try loading from current directory as fallback
        load_dotenv()

    config = {
        "base_url": os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", "none"),
        "model": os.getenv("OPENAI_MODEL", "llama-3.1-8b-instruct"),
    }

    if verbose:
        print(f"Configuration loaded:")
        print(f"  Base URL: {config['base_url']}")
        print(f"  Model: {config['model']}")
        print(
            f"  API Key: {'*' * len(config['api_key']) if config['api_key'] != 'none' else 'none'}"
        )
        print(f"  Working directory: {Path.cwd()}")
        print(f"  Environment variables:")
        print(f"    OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'not set')}")
        print(
            f"    OPENAI_API_KEY: {'*' * len(os.getenv('OPENAI_API_KEY', '')) if os.getenv('OPENAI_API_KEY') else 'not set'}"
        )
        print(f"    OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'not set')}")
        print(f"    TERM: {os.getenv('TERM', 'not set')}")
        print(f"    SHELL: {os.getenv('SHELL', 'not set')}")

    return config
