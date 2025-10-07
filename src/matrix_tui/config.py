"""Configuration management for Matrix Rain TUI."""

import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from environment variables.

    Returns:
        dict: Configuration dictionary with OpenAI settings
    """
    load_dotenv()

    return {
        "base_url": os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", "none"),
        "model": os.getenv("OPENAI_MODEL", "llama-3.1-8b-instruct"),
    }
