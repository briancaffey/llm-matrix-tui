"""Tests for language filtering functionality."""

import pytest
import tempfile
import yaml
from pathlib import Path
from matrix_tui.prompt_loader import PromptLoader


class TestLanguageFiltering:
    """Test language filtering functionality."""

    def create_test_prompts_file(self, prompts_data):
        """Create a temporary prompts file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        yaml.dump(prompts_data, temp_file, allow_unicode=True)
        temp_file.close()
        return temp_file.name

    def test_no_filtering_returns_all_prompts(self):
        """Test that no filtering returns all prompts."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            loader = PromptLoader(temp_file)
            assert len(loader.prompts) == 3
            langs = loader.get_available_languages()
            assert len(langs) == 3
            assert "en" in langs
            assert "zh" in langs
            assert "ja" in langs
        finally:
            Path(temp_file).unlink()

    def test_include_langs_filtering(self):
        """Test include_langs filtering."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
                {
                    "prompt": "Korean prompt",
                    "system_prompt": "Korean system",
                    "lang": "ko",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Test including only English and Chinese
            loader = PromptLoader(temp_file, include_langs=["en", "zh"])
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "en" in langs
            assert "zh" in langs
            assert "ja" not in langs
            assert "ko" not in langs
        finally:
            Path(temp_file).unlink()

    def test_exclude_langs_filtering(self):
        """Test exclude_langs filtering."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
                {
                    "prompt": "Korean prompt",
                    "system_prompt": "Korean system",
                    "lang": "ko",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Test excluding English and Chinese
            loader = PromptLoader(temp_file, exclude_langs=["en", "zh"])
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "ja" in langs
            assert "ko" in langs
            assert "en" not in langs
            assert "zh" not in langs
        finally:
            Path(temp_file).unlink()

    def test_include_and_exclude_together(self):
        """Test using both include_langs and exclude_langs together."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
                {
                    "prompt": "Korean prompt",
                    "system_prompt": "Korean system",
                    "lang": "ko",
                },
                {
                    "prompt": "Russian prompt",
                    "system_prompt": "Russian system",
                    "lang": "ru",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # First exclude 'en' and 'zh', then include only 'ja' and 'ko'
            loader = PromptLoader(
                temp_file, include_langs=["ja", "ko"], exclude_langs=["en", "zh"]
            )
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "ja" in langs
            assert "ko" in langs
            assert "en" not in langs
            assert "zh" not in langs
            assert "ru" not in langs
        finally:
            Path(temp_file).unlink()

    def test_include_langs_with_spaces(self):
        """Test include_langs with spaces in comma-separated values."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Test with spaces in the language list - should work because spaces are stripped in CLI
            loader = PromptLoader(temp_file, include_langs=[" en ", " zh "])
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "en" in langs
            assert "zh" in langs
            assert "ja" not in langs
        finally:
            Path(temp_file).unlink()

    def test_exclude_langs_with_spaces(self):
        """Test exclude_langs with spaces in comma-separated values."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Test with spaces in the language list
            loader = PromptLoader(temp_file, exclude_langs=[" en ", " zh "])
            assert len(loader.prompts) == 1
            langs = [p["lang"] for p in loader.prompts]
            assert "ja" in langs
            assert "en" not in langs
            assert "zh" not in langs
        finally:
            Path(temp_file).unlink()

    def test_empty_include_langs_returns_nothing(self):
        """Test that empty include_langs returns no prompts."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Empty include_langs should not filter anything (same as no filtering)
            loader = PromptLoader(temp_file, include_langs=[])
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "en" in langs
            assert "zh" in langs
        finally:
            Path(temp_file).unlink()

    def test_exclude_all_langs_returns_nothing(self):
        """Test that excluding all languages returns no prompts."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            with pytest.raises(
                ValueError, match="No prompts remain after language filtering"
            ):
                PromptLoader(temp_file, exclude_langs=["en", "zh"])
        finally:
            Path(temp_file).unlink()

    def test_nonexistent_language_in_include(self):
        """Test that including a nonexistent language returns no prompts."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            with pytest.raises(
                ValueError, match="No prompts remain after language filtering"
            ):
                PromptLoader(temp_file, include_langs=["nonexistent"])
        finally:
            Path(temp_file).unlink()

    def test_nonexistent_language_in_exclude(self):
        """Test that excluding a nonexistent language has no effect."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            loader = PromptLoader(temp_file, exclude_langs=["nonexistent"])
            assert len(loader.prompts) == 2
            langs = [p["lang"] for p in loader.prompts]
            assert "en" in langs
            assert "zh" in langs
        finally:
            Path(temp_file).unlink()

    def test_case_sensitive_language_codes(self):
        """Test that language codes are case sensitive."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            # Test with uppercase language codes
            with pytest.raises(
                ValueError, match="No prompts remain after language filtering"
            ):
                PromptLoader(temp_file, include_langs=["EN", "ZH"])
        finally:
            Path(temp_file).unlink()

    def test_random_prompt_from_filtered_set(self):
        """Test that get_random_prompt returns prompts only from filtered set."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt 1",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "English prompt 2",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            loader = PromptLoader(temp_file, include_langs=["en"])

            # Get multiple random prompts and verify they're all English
            for _ in range(10):
                prompt = loader.get_random_prompt()
                assert prompt["lang"] == "en"
                assert "English" in prompt["prompt"]
        finally:
            Path(temp_file).unlink()

    def test_get_prompts_by_lang_with_filtering(self):
        """Test get_prompts_by_lang works with filtered prompts."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt 1",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "English prompt 2",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            loader = PromptLoader(temp_file, include_langs=["en", "zh"])

            # Test getting English prompts
            en_prompts = loader.get_prompts_by_language("en")
            assert len(en_prompts) == 2
            assert all(p["lang"] == "en" for p in en_prompts)

            # Test getting Chinese prompts
            zh_prompts = loader.get_prompts_by_language("zh")
            assert len(zh_prompts) == 1
            assert all(p["lang"] == "zh" for p in zh_prompts)

            # Test getting Japanese prompts (should be empty due to filtering)
            ja_prompts = loader.get_prompts_by_language("ja")
            assert len(ja_prompts) == 0
        finally:
            Path(temp_file).unlink()

    def test_get_available_languages_with_filtering(self):
        """Test get_available_languages returns only filtered languages."""
        prompts_data = {
            "prompts": [
                {
                    "prompt": "English prompt",
                    "system_prompt": "English system",
                    "lang": "en",
                },
                {
                    "prompt": "Chinese prompt",
                    "system_prompt": "Chinese system",
                    "lang": "zh",
                },
                {
                    "prompt": "Japanese prompt",
                    "system_prompt": "Japanese system",
                    "lang": "ja",
                },
                {
                    "prompt": "Korean prompt",
                    "system_prompt": "Korean system",
                    "lang": "ko",
                },
            ]
        }

        temp_file = self.create_test_prompts_file(prompts_data)
        try:
            loader = PromptLoader(temp_file, include_langs=["en", "zh"])
            available_langs = loader.get_available_languages()
            assert len(available_langs) == 2
            assert "en" in available_langs
            assert "zh" in available_langs
            assert "ja" not in available_langs
            assert "ko" not in available_langs
        finally:
            Path(temp_file).unlink()
