"""Configuration loading and parsing for naming convention linter.

This module handles loading and parsing of the .naming-convention-exceptions
YAML configuration file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


@dataclass(frozen=True)
class Config:
    """Configuration for naming convention linter.

    Attributes:
        exceptions: Set of paths that are exempt from validation.
                   Paths are relative to repository root.
    """

    exceptions: set[str]

    def is_exception(self, path: str) -> bool:
        """Check if a path is in the exceptions list.

        Args:
            path: The path to check (relative to repository root).

        Returns:
            True if path is in exceptions, False otherwise.
        """
        normalized = self._normalize_path(path)
        return normalized in self.exceptions

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize a path for comparison.

        Args:
            path: The path to normalize.

        Returns:
            Normalized path with consistent separators and no leading ./
        """
        # Remove leading ./ if present
        path = path.removeprefix("./")
        # Ensure consistent path separators
        path = path.replace("\\", "/")
        # Note: We preserve trailing slashes to maintain consistency with
        # how exceptions are stored (directories typically have trailing slashes)
        return path


class ConfigLoader:
    """Loader for naming convention linter configuration.

    Loads and parses the .naming-convention-exceptions YAML file.

    Attributes:
        config_path: Path to the configuration file.
    """

    DEFAULT_CONFIG_FILE = ".naming-convention-exceptions"

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize config loader.

        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE

    def load(self) -> Config:
        """Load and parse configuration file.

        Returns:
            Config object with loaded exceptions.

        Raises:
            ConfigError: If configuration file is invalid or cannot be parsed.
        """
        config_file = Path(self.config_path)

        # If config file doesn't exist, return empty config
        if not config_file.exists():
            return Config(exceptions=set())

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e
        except OSError as e:
            raise ConfigError(f"Cannot read config file: {e}") from e

        # If file is empty, return empty config
        if data is None:
            return Config(exceptions=set())

        # Validate config structure
        if not isinstance(data, dict):
            raise ConfigError(f"Config file must contain a YAML object, got {type(data).__name__}")

        # Get exceptions list
        exceptions = data.get("exceptions", [])

        if not isinstance(exceptions, list):
            raise ConfigError(f"'exceptions' must be a list, got {type(exceptions).__name__}")

        # Validate and normalize each exception
        normalized_exceptions = set()
        for i, exc in enumerate(exceptions):
            if not isinstance(exc, str):
                raise ConfigError(
                    f"Exception at index {i} must be a string, got {type(exc).__name__}"
                )

            # Normalize the exception path
            normalized = self._normalize_exception_path(exc)
            normalized_exceptions.add(normalized)

        return Config(exceptions=normalized_exceptions)

    def _normalize_exception_path(self, path: str) -> str:
        """Normalize an exception path.

        Args:
            path: The exception path to normalize.

        Returns:
            Normalized path.
        """
        # Remove leading ./ if present
        path = path.removeprefix("./")
        # Ensure consistent path separators
        path = path.replace("\\", "/")
        # Remove leading / if present
        path = path.removeprefix("/")
        return path

    def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            True if config file exists, False otherwise.
        """
        return Path(self.config_path).exists()
