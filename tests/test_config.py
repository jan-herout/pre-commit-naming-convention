"""Unit tests for the config module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from naming_convention_linter.config import Config, ConfigError, ConfigLoader


class TestConfig:
    """Tests for Config class."""

    def test_empty_config(self) -> None:
        """Test empty config has no exceptions."""
        config = Config(exceptions=set())
        assert config.exceptions == set()
        assert not config.is_exception("anything.py")

    def test_config_with_exceptions(self) -> None:
        """Test config with exceptions."""
        config = Config(exceptions={"legacy/", "README.md"})
        assert config.is_exception("legacy/")
        assert config.is_exception("README.md")
        assert not config.is_exception("other.py")

    def test_path_normalization(self) -> None:
        """Test path normalization for exception checking."""
        config = Config(exceptions={"src/utils/"})
        assert config.is_exception("src/utils/")
        assert config.is_exception("./src/utils/")
        assert config.is_exception("src\\utils\\")


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_valid_config(self) -> None:
        """Test loading a valid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions:\n  - legacy/\n  - README.md\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "legacy/" in config.exceptions
            assert "README.md" in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_config(self) -> None:
        """Test loading a non-existent config file returns empty config."""
        loader = ConfigLoader("/nonexistent/path/config.yaml")
        config = loader.load()

        assert config.exceptions == set()

    def test_load_empty_config_file(self) -> None:
        """Test loading an empty config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert config.exceptions == set()
        finally:
            Path(temp_path).unlink()

    def test_load_config_with_comments(self) -> None:
        """Test loading config with YAML comments."""
        yaml_content = """# This is a comment
exceptions:
  - legacy/  # inline comment
  # Another comment
  - README.md
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "legacy/" in config.exceptions
            assert "README.md" in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_load_invalid_yaml(self) -> None:
        """Test loading invalid YAML raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigError) as exc_info:
                loader.load()

            assert "Invalid YAML" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_non_dict_yaml(self) -> None:
        """Test loading YAML that is not a dict raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("just a string")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigError) as exc_info:
                loader.load()

            assert "must contain a YAML object" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_non_list_exceptions(self) -> None:
        """Test loading YAML with non-list exceptions raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions: just_a_string")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigError) as exc_info:
                loader.load()

            assert "must be a list" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_non_string_exception(self) -> None:
        """Test loading YAML with non-string exception item raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions:\n  - 123\n  - valid_string\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigError) as exc_info:
                loader.load()

            assert "must be a string" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_default_config_path(self) -> None:
        """Test default config path is .naming-convention-exceptions."""
        loader = ConfigLoader()
        assert loader.config_path == ".naming-convention-exceptions"

    def test_custom_config_path(self) -> None:
        """Test custom config path can be set."""
        loader = ConfigLoader("custom-config.yaml")
        assert loader.config_path == "custom-config.yaml"

    def test_exists_with_existing_file(self) -> None:
        """Test exists() returns True for existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions: []\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            assert loader.exists() is True
        finally:
            Path(temp_path).unlink()

    def test_exists_with_nonexistent_file(self) -> None:
        """Test exists() returns False for non-existent file."""
        loader = ConfigLoader("/nonexistent/config.yaml")
        assert loader.exists() is False


class TestPathNormalization:
    """Tests for path normalization in config."""

    def test_normalize_leading_dot_slash(self) -> None:
        """Test removal of leading ./ from paths."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions:\n  - ./legacy/\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "legacy/" in config.exceptions
            assert "./legacy/" not in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_normalize_leading_slash(self) -> None:
        """Test removal of leading / from paths."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions:\n  - /absolute/path/\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "absolute/path/" in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_normalize_backslash(self) -> None:
        """Test backslash to forward slash via _normalize_exception_path."""
        loader = ConfigLoader()
        # Test the normalization directly
        normalized = loader._normalize_exception_path("windows\\path\\")
        assert normalized == "windows/path/"

    def test_normalize_trailing_slash(self) -> None:
        """Test handling of trailing slash in directory paths."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions:\n  - src/utils\n  - src/helpers/\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            # Both should be normalized the same way
            assert "src/utils" in config.exceptions or "src/utils/" in config.exceptions
            assert "src/helpers" in config.exceptions or "src/helpers/" in config.exceptions
        finally:
            Path(temp_path).unlink()


class TestConfigWithComplexPaths:
    """Tests for config with complex path patterns."""

    def test_nested_paths(self) -> None:
        """Test loading config with deeply nested paths."""
        yaml_content = """exceptions:
  - src/legacy/v1/
  - vendor/third-party/lib/
  - .github/workflows/
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "src/legacy/v1/" in config.exceptions
            assert "vendor/third-party/lib/" in config.exceptions
            assert ".github/workflows/" in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_file_and_directory_exceptions(self) -> None:
        """Test mixing file and directory exceptions."""
        yaml_content = """exceptions:
  - legacy/
  - README.md
  - LICENSE
  - .gitignore
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert "legacy/" in config.exceptions
            assert "README.md" in config.exceptions
            assert "LICENSE" in config.exceptions
            assert ".gitignore" in config.exceptions
        finally:
            Path(temp_path).unlink()

    def test_empty_exceptions_list(self) -> None:
        """Test config with empty exceptions list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("exceptions: []\n")
            temp_path = f.name

        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()

            assert config.exceptions == set()
        finally:
            Path(temp_path).unlink()
