"""Unit tests for the validator module."""

from __future__ import annotations

from naming_convention_linter.validator import (
    NamingConventionValidator,
    ValidationResult,
    Violation,
    ViolationType,
)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_valid_result(self) -> None:
        """Test ValidationResult with no violations."""
        result = ValidationResult(path="test.py")
        assert result.path == "test.py"
        assert result.is_valid is True
        assert result.violations == []

    def test_invalid_result(self) -> None:
        """Test ValidationResult with violations."""
        result = ValidationResult(path="Test.py")
        violation = Violation(
            type=ViolationType.UPPERCASE,
            message="Contains uppercase",
            component="Test.py",
        )
        result.add_violation(violation)

        assert result.is_valid is False
        assert len(result.violations) == 1
        assert result.violations[0].type == ViolationType.UPPERCASE


class TestValidNames:
    """Tests for valid file and directory names."""

    def test_valid_lowercase_file(self) -> None:
        """Test valid lowercase file name."""
        validator = NamingConventionValidator()
        result = validator.validate("src/utils/helper.py")
        assert result.is_valid is True

    def test_valid_file_with_hyphen(self) -> None:
        """Test valid file name with hyphen."""
        validator = NamingConventionValidator()
        result = validator.validate("my-file.txt")
        assert result.is_valid is True

    def test_valid_file_with_underscore(self) -> None:
        """Test valid file name with underscore."""
        validator = NamingConventionValidator()
        result = validator.validate("my_file.txt")
        assert result.is_valid is True

    def test_valid_file_with_numbers(self) -> None:
        """Test valid file name with numbers."""
        validator = NamingConventionValidator()
        result = validator.validate("file123.py")
        assert result.is_valid is True

    def test_valid_file_with_multiple_dots(self) -> None:
        """Test valid file name with multiple dots."""
        validator = NamingConventionValidator()
        result = validator.validate("archive.tar.gz")
        assert result.is_valid is True

    def test_valid_directory(self) -> None:
        """Test valid directory name."""
        validator = NamingConventionValidator()
        result = validator.validate("src/utils/")
        assert result.is_valid is True

    def test_valid_nested_path(self) -> None:
        """Test valid nested path."""
        validator = NamingConventionValidator()
        result = validator.validate("src/my-package/utils/helper.py")
        assert result.is_valid is True


class TestUppercaseViolations:
    """Tests for uppercase letter detection."""

    def test_file_with_uppercase(self) -> None:
        """Test file with uppercase letters."""
        validator = NamingConventionValidator()
        result = validator.validate("MyFile.py")

        assert result.is_valid is False
        # Note: MyFile.py triggers both UPPERCASE and INVALID_CHAR violations
        assert len(result.violations) == 2
        assert any(v.type == ViolationType.UPPERCASE for v in result.violations)
        uppercase_violation = next(
            v for v in result.violations if v.type == ViolationType.UPPERCASE
        )
        assert "MyFile" in uppercase_violation.message

    def test_directory_with_uppercase(self) -> None:
        """Test directory with uppercase letters."""
        validator = NamingConventionValidator()
        result = validator.validate("src/MyModule/file.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.UPPERCASE for v in result.violations)

    def test_multiple_uppercase_components(self) -> None:
        """Test path with multiple uppercase components."""
        validator = NamingConventionValidator()
        result = validator.validate("Src/MyModule/BadFile.py")

        assert result.is_valid is False
        uppercase_violations = [v for v in result.violations if v.type == ViolationType.UPPERCASE]
        assert len(uppercase_violations) >= 2


class TestWhitespaceViolations:
    """Tests for whitespace detection."""

    def test_file_with_space(self) -> None:
        """Test file with space in name."""
        validator = NamingConventionValidator()
        result = validator.validate("my file.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.WHITESPACE for v in result.violations)

    def test_file_with_tab(self) -> None:
        """Test file with tab in name."""
        validator = NamingConventionValidator()
        result = validator.validate("my\tfile.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.WHITESPACE for v in result.violations)

    def test_directory_with_space(self) -> None:
        """Test directory with space in name."""
        validator = NamingConventionValidator()
        result = validator.validate("my folder/file.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.WHITESPACE for v in result.violations)


class TestDiacriticViolations:
    """Tests for diacritic character detection."""

    def test_file_with_acute_accent(self) -> None:
        """Test file with acute accent (café)."""
        validator = NamingConventionValidator()
        result = validator.validate("café.txt")

        assert result.is_valid is False
        assert any(v.type == ViolationType.DIACRITIC for v in result.violations)

    def test_file_with_umlaut(self) -> None:
        """Test file with umlaut (über)."""
        validator = NamingConventionValidator()
        result = validator.validate("über.txt")

        assert result.is_valid is False
        assert any(v.type == ViolationType.DIACRITIC for v in result.violations)

    def test_file_with_tilde(self) -> None:
        """Test file with tilde (señor)."""
        validator = NamingConventionValidator()
        result = validator.validate("señor.txt")

        assert result.is_valid is False
        assert any(v.type == ViolationType.DIACRITIC for v in result.violations)

    def test_file_with_czech_characters(self) -> None:
        """Test file with Czech characters."""
        validator = NamingConventionValidator()
        result = validator.validate("přílišžluťoučkýkůň.txt")

        assert result.is_valid is False
        diacritic_violations = [v for v in result.violations if v.type == ViolationType.DIACRITIC]
        assert len(diacritic_violations) > 0


class TestInvalidCharacterViolations:
    """Tests for invalid character detection."""

    def test_file_with_at_symbol(self) -> None:
        """Test file with @ symbol."""
        validator = NamingConventionValidator()
        result = validator.validate("file@name.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.INVALID_CHAR for v in result.violations)

    def test_file_with_hash(self) -> None:
        """Test file with # symbol."""
        validator = NamingConventionValidator()
        result = validator.validate("file#name.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.INVALID_CHAR for v in result.violations)

    def test_file_with_dollar(self) -> None:
        """Test file with $ symbol."""
        validator = NamingConventionValidator()
        result = validator.validate("file$name.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.INVALID_CHAR for v in result.violations)

    def test_file_with_ampersand(self) -> None:
        """Test file with & symbol."""
        validator = NamingConventionValidator()
        result = validator.validate("file&name.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.INVALID_CHAR for v in result.violations)


class TestDotInDirectoryAllowed:
    """Tests that dots are now allowed in directory names."""

    def test_directory_with_dot(self) -> None:
        """Test directory with dot in name is now allowed."""
        validator = NamingConventionValidator()
        result = validator.validate(".config/file.py")

        assert result.is_valid is True

    def test_hidden_directory(self) -> None:
        """Test hidden directory (starts with dot) is now allowed."""
        validator = NamingConventionValidator()
        result = validator.validate("src/.hidden/file.py")

        assert result.is_valid is True

    def test_directory_with_version(self) -> None:
        """Test directory with version number (e.g., v1.0) is now allowed."""
        validator = NamingConventionValidator()
        result = validator.validate("src/v1.0/module.py")

        assert result.is_valid is True


class TestMultipleViolations:
    """Tests for multiple violations in single path."""

    def test_file_with_uppercase_and_space(self) -> None:
        """Test file with both uppercase and space."""
        validator = NamingConventionValidator()
        result = validator.validate("My File.py")

        assert result.is_valid is False
        violation_types = {v.type for v in result.violations}
        assert ViolationType.UPPERCASE in violation_types
        assert ViolationType.WHITESPACE in violation_types

    def test_file_with_multiple_issues(self) -> None:
        """Test file with multiple issues."""
        validator = NamingConventionValidator()
        result = validator.validate("My Bad@File.py")

        assert result.is_valid is False
        assert len(result.violations) >= 3


class TestExceptions:
    """Tests for exception handling."""

    def test_exact_path_exception(self) -> None:
        """Test that exact path exception works."""
        validator = NamingConventionValidator(exceptions={"BadFile.py"})
        result = validator.validate("BadFile.py")

        assert result.is_valid is True

    def test_directory_exception(self) -> None:
        """Test that directory exception works."""
        validator = NamingConventionValidator(exceptions={"legacy/"})
        result = validator.validate("legacy/")

        assert result.is_valid is True

    def test_exception_not_inherited(self) -> None:
        """Test that exceptions are not inherited by children."""
        validator = NamingConventionValidator(exceptions={"legacy/"})
        result = validator.validate("legacy/BadFile.py")

        assert result.is_valid is False
        assert any(v.type == ViolationType.UPPERCASE for v in result.violations)

    def test_partial_path_exception(self) -> None:
        """Test exception for partial path."""
        validator = NamingConventionValidator(exceptions={"src/legacy/"})
        result = validator.validate("src/legacy/BadFile.py")

        # The legacy/ directory is exempt, but BadFile.py is not
        assert result.is_valid is False
        assert any(v.type == ViolationType.UPPERCASE for v in result.violations)

    def test_nested_exception(self) -> None:
        """Test nested path with exception at intermediate level."""
        validator = NamingConventionValidator(exceptions={"vendor/"})
        result = validator.validate("vendor/SomeLib/BadFile.py")

        # vendor/ is exempt, but SomeLib and BadFile.py are not
        assert result.is_valid is False
        violation_components = {v.component for v in result.violations}
        assert "SomeLib" in violation_components or "BadFile.py" in violation_components


class TestPathNormalization:
    """Tests for path normalization."""

    def test_leading_dot_slash(self) -> None:
        """Test path with leading ./ is normalized."""
        validator = NamingConventionValidator(exceptions={"file.py"})
        result = validator.validate("./file.py")

        assert result.is_valid is True

    def test_backslash_conversion(self) -> None:
        """Test backslash is converted to forward slash."""
        validator = NamingConventionValidator()
        result = validator.validate("src\\utils\\helper.py")

        assert result.is_valid is True

    def test_exception_with_different_separators(self) -> None:
        """Test exception matching with different separators."""
        validator = NamingConventionValidator(exceptions={"src/utils/"})
        result = validator.validate("src\\utils\\file.py")

        assert result.is_valid is True


class TestValidateBatch:
    """Tests for validate_batch method."""

    def test_batch_validation(self) -> None:
        """Test validating multiple files at once."""
        validator = NamingConventionValidator()
        paths = ["good.py", "Bad.py", "also_good.py"]
        results = validator.validate_batch(paths)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is True

    def test_empty_batch(self) -> None:
        """Test validating empty batch."""
        validator = NamingConventionValidator()
        results = validator.validate_batch([])

        assert results == []
