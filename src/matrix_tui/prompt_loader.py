"""Prompt loader for managing multilingual prompts from YAML file."""

import random
import yaml
from pathlib import Path
from typing import List, Dict, Any


class PromptLoader:
    """Loads and manages prompts from prompts.yml file."""

    def __init__(
        self,
        prompts_file: str = "prompts.yml",
        include_langs: List[str] = None,
        exclude_langs: List[str] = None,
    ):
        """Initialize the prompt loader.

        Args:
            prompts_file: Path to the prompts YAML file
            include_langs: List of language codes to include (e.g., ['en', 'zh', 'ja'])
            exclude_langs: List of language codes to exclude (e.g., ['en', 'zh'])
        """
        self.prompts_file = Path(prompts_file)
        self.include_langs = include_langs
        self.exclude_langs = exclude_langs
        self.prompts: List[Dict[str, Any]] = []
        self.load_prompts()

    def load_prompts(self):
        """Load prompts from the YAML file."""
        try:
            if not self.prompts_file.exists():
                raise FileNotFoundError(f"Prompts file not found: {self.prompts_file}")

            with open(self.prompts_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if "prompts" not in data:
                raise ValueError("Invalid prompts file: missing 'prompts' key")

            self.prompts = data["prompts"]

            if not self.prompts:
                raise ValueError("No prompts found in prompts file")

            # Validate prompt structure
            for i, prompt in enumerate(self.prompts):
                if not all(
                    key in prompt for key in ["prompt", "system_prompt", "lang"]
                ):
                    raise ValueError(
                        f"Invalid prompt at index {i}: missing required fields"
                    )

            # Apply language filtering
            self.prompts = self._apply_language_filtering(self.prompts)

            if not self.prompts:
                raise ValueError("No prompts remain after language filtering")

        except Exception as e:
            print(f"Error loading prompts: {e}")
            # Only fallback to default prompts if it's not a filtering issue
            if "No prompts remain after language filtering" in str(e):
                raise  # Re-raise filtering errors
            # Fallback to default prompts for other errors
            self.prompts = self._get_fallback_prompts()

    def get_random_prompt(self) -> Dict[str, str]:
        """Get a random prompt from the loaded prompts.

        Returns:
            Dictionary containing 'prompt', 'system_prompt', and 'lang'
        """
        if not self.prompts:
            return self._get_fallback_prompts()[0]
        return random.choice(self.prompts)

    def get_prompts_by_language(self, lang: str) -> List[Dict[str, str]]:
        """Get all prompts for a specific language.

        Args:
            lang: Language code (e.g., 'en', 'zh', 'ja')

        Returns:
            List of prompts for the specified language
        """
        return [p for p in self.prompts if p.get("lang") == lang]

    def get_available_languages(self) -> List[str]:
        """Get list of available language codes.

        Returns:
            List of unique language codes
        """
        return list(set(p.get("lang", "en") for p in self.prompts))

    def _apply_language_filtering(
        self, prompts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply language filtering to the prompts list.

        Args:
            prompts: List of prompts to filter

        Returns:
            Filtered list of prompts
        """
        filtered_prompts = prompts.copy()

        # First, exclude languages if specified
        if self.exclude_langs:
            # Strip spaces from language codes
            exclude_langs = [lang.strip() for lang in self.exclude_langs]
            filtered_prompts = [
                prompt
                for prompt in filtered_prompts
                if prompt.get("lang", "en") not in exclude_langs
            ]

        # Then, include only specified languages if specified
        if self.include_langs and len(self.include_langs) > 0:
            # Strip spaces from language codes
            include_langs = [lang.strip() for lang in self.include_langs]
            filtered_prompts = [
                prompt
                for prompt in filtered_prompts
                if prompt.get("lang", "en") in include_langs
            ]

        return filtered_prompts

    def _get_fallback_prompts(self) -> List[Dict[str, str]]:
        """Get fallback prompts in case the YAML file cannot be loaded.

        Returns:
            List of default prompts
        """
        return [
            {
                "prompt": "Explain artificial intelligence in detail.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Describe machine learning algorithms and their applications.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Discuss the future of technology and automation.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Explain quantum computing and its potential impact.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Describe blockchain technology and cryptocurrencies.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Discuss renewable energy and sustainability.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Explain space exploration and Mars missions.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
            {
                "prompt": "Describe biotechnology and genetic engineering.",
                "system_prompt": "You are a helpful assistant.",
                "lang": "en",
            },
        ]
