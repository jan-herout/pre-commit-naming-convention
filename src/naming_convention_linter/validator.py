"""Core validation logic for naming convention linter.

This module provides the NamingConventionValidator class that validates
file and directory names against the naming convention rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Set


class ViolationType(Enum):
    """Types of naming convention violations."""

    UPPERCASE = auto()
    INVALID_CHAR = auto()
    WHITESPACE = auto()
    DIACRITIC = auto()


@dataclass(frozen=True)
class Violation:
    """A single naming convention violation.

    Attributes:
        type: The type of violation.
        message: Human-readable description of the violation.
        component: The path component that violated (e.g., filename, dirname).
    """

    type: ViolationType
    message: str
    component: str


@dataclass
class ValidationResult:
    """Result of validating a path.

    Attributes:
        path: The path that was validated.
        is_valid: True if no violations found, False otherwise.
        violations: List of violations found.
    """

    path: str
    is_valid: bool = field(init=False)
    violations: list[Violation] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Compute is_valid from violations."""
        object.__setattr__(self, "is_valid", len(self.violations) == 0)

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to the result."""
        self.violations.append(violation)
        object.__setattr__(self, "is_valid", False)


class NamingConventionValidator:
    """Validator for file and directory naming conventions.

    Validates that names conform to:
    - Lowercase letters only (a-z)
    - Digits (0-9)
    - Safe special characters: -, _, . (allowed in both files and directories)
    - No whitespace
    - No diacritic characters

    Attributes:
        exceptions: Set of paths that are exempt from validation.
    """

    # Regex patterns for validation
    # Both files and directories can contain dots
    SAFE_CHARS = re.compile(r"^[a-z0-9_.-]+$")
    WHITESPACE_PATTERN = re.compile(r"\s")
    DIACRITIC_PATTERN = re.compile(r"[\u0300-\u036f\u00c0-\u00ff\u0100-\u017f]")
    UPPERCASE_PATTERN = re.compile(r"[A-Z]")

    def __init__(self, exceptions: Set[str] | None = None) -> None:
        """Initialize validator with exception paths.

        Args:
            exceptions: Set of paths that are exempt from validation.
                       Paths should be relative to repository root.
        """
        self.exceptions = exceptions or set()
        # Normalize exceptions for comparison
        self._normalized_exceptions = {self._normalize_path(exc) for exc in self.exceptions}

    def _normalize_path(self, path: str) -> str:
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
        return path

    def _is_exception(self, path: str) -> bool:
        """Check if a path is in the exceptions list.

        Args:
            path: The path to check.

        Returns:
            True if the path is an exception, False otherwise.
        """
        normalized = self._normalize_path(path)
        return normalized in self._normalized_exceptions

    def _check_lowercase(self, name: str, component_type: str) -> Violation | None:
        """Check if name contains uppercase letters.

        Args:
            name: The name to check.
            component_type: Type of component ("file" or "directory").

        Returns:
            Violation if uppercase found, None otherwise.
        """
        if self.UPPERCASE_PATTERN.search(name):
            msg = (
                f"{component_type.capitalize()} contains uppercase letters: "
                f'"{name}" should be "{name.lower()}"'
            )
            return Violation(
                type=ViolationType.UPPERCASE,
                message=msg,
                component=name,
            )
        return None

    def _check_whitespace(self, name: str, component_type: str) -> Violation | None:
        """Check if name contains whitespace.

        Args:
            name: The name to check.
            component_type: Type of component ("file" or "directory").

        Returns:
            Violation if whitespace found, None otherwise.
        """
        if self.WHITESPACE_PATTERN.search(name):
            suggestion = self.WHITESPACE_PATTERN.sub("_", name)
            msg = (
                f"{component_type.capitalize()} contains whitespace: "
                f'"{name}" should be "{suggestion}"'
            )
            return Violation(
                type=ViolationType.WHITESPACE,
                message=msg,
                component=name,
            )
        return None

    def _check_diacritics(self, name: str, component_type: str) -> Violation | None:
        """Check if name contains diacritic characters.

        Args:
            name: The name to check.
            component_type: Type of component ("file" or "directory").

        Returns:
            Violation if diacritics found, None otherwise.
        """
        if self.DIACRITIC_PATTERN.search(name):
            # Simple transliteration for common diacritics
            import unicodedata

            suggestion = "".join(
                c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c)
            )
            msg = (
                f"{component_type.capitalize()} contains diacritic character: "
                f'"{name}" should be "{suggestion}"'
            )
            return Violation(
                type=ViolationType.DIACRITIC,
                message=msg,
                component=name,
            )
        return None

    def _check_invalid_chars(
        self, name: str, component_type: str, is_file: bool
    ) -> Violation | None:
        """Check if name contains invalid characters.

        Args:
            name: The name to check.
            component_type: Type of component ("file" or "directory").
            is_file: True if this is a file name, False if directory.

        Returns:
            Violation if invalid characters found, None otherwise.
        """
        if not self.SAFE_CHARS.match(name):
            msg = (
                f"{component_type.capitalize()} contains invalid characters: "
                f'"{name}" (only a-z, 0-9, -, _, . allowed)'
            )
            return Violation(
                type=ViolationType.INVALID_CHAR,
                message=msg,
                component=name,
            )
        return None

    def _validate_component(self, name: str, component_type: str, is_file: bool) -> list[Violation]:
        """Validate a single path component.

        Args:
            name: The component name to validate.
            component_type: Type of component ("file" or "directory").
            is_file: True if this is a file name, False if directory.

        Returns:
            List of violations found.
        """
        violations = []

        # Check for empty name
        if not name or name == "." or name == "..":
            return violations

        # Check uppercase
        if violation := self._check_lowercase(name, component_type):
            violations.append(violation)

        # Check whitespace
        if violation := self._check_whitespace(name, component_type):
            violations.append(violation)

        # Check diacritics
        if violation := self._check_diacritics(name, component_type):
            violations.append(violation)

        # Check invalid characters
        if violation := self._check_invalid_chars(name, component_type, is_file):
            violations.append(violation)

        return violations

    def validate(self, path: str) -> ValidationResult:
        """Validate a file or directory path.

        Validates all path components against naming conventions.
        Exceptions are non-inheritable - only the exact path in exceptions
        is exempt, but child components are still validated.

        Args:
            path: The path to validate (relative to repository root).

        Returns:
            ValidationResult with violations found.
        """
        result = ValidationResult(path=path)

        # Normalize path
        normalized_path = self._normalize_path(path)

        # Check if entire path is an exception
        if self._is_exception(normalized_path):
            return result

        # Split path into components
        components = normalized_path.split("/")

        # Build up path progressively to check for exceptions at each level
        current_path = ""

        for i, component in enumerate(components):
            # Skip empty components (e.g., leading /)
            if not component:
                continue

            # Build current path
            current_path = f"{current_path}/{component}" if current_path else component

            # Check if this specific path component is an exception
            # If so, skip validation for this component but continue checking children
            if self._is_exception(current_path):
                continue

            # Determine if this is a file (last component and has extension-like dot)
            # or if it's explicitly the last component
            is_last = i == len(components) - 1
            is_file = is_last

            # Validate this component
            component_type = "file" if is_file else "directory"
            violations = self._validate_component(component, component_type, is_file)

            for violation in violations:
                result.add_violation(violation)

        return result

    def validate_batch(self, paths: list[str]) -> list[ValidationResult]:
        """Validate multiple paths.

        Args:
            paths: List of paths to validate.

        Returns:
            List of ValidationResult objects.
        """
        return [self.validate(path) for path in paths]
