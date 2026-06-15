"""Custom exceptions for naming convention linter."""

from __future__ import annotations


class NamingConventionError(Exception):
    """Base exception for naming convention linter."""

    pass


class ValidationError(NamingConventionError):
    """Exception raised during validation."""

    pass


class ConfigError(NamingConventionError):
    """Exception raised for configuration errors."""

    pass


class GitError(NamingConventionError):
    """Exception raised for Git-related errors."""

    pass
