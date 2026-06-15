"""Integration tests for the CLI module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from naming_convention_linter.cli import (
    EXIT_CONFIG_ERROR,
    EXIT_RUNTIME_ERROR,
    EXIT_SUCCESS,
    EXIT_VIOLATIONS,
    create_parser,
    format_violations,
    main,
)
from naming_convention_linter.validator import NamingConventionValidator, ValidationResult


class TestCreateParser:
    """Tests for argument parser."""

    def test_parser_creates_argument_parser(self) -> None:
        """Test that create_parser returns an ArgumentParser."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "naming-convention-linter"

    def test_parser_accepts_files_argument(self) -> None:
        """Test parser accepts files as positional arguments."""
        parser = create_parser()
        args = parser.parse_args(["file1.py", "file2.py"])
        assert args.files == ["file1.py", "file2.py"]

    def test_parser_accepts_all_flag(self) -> None:
        """Test parser accepts --all flag."""
        parser = create_parser()
        args = parser.parse_args(["--all"])
        assert args.all is True

    def test_parser_accepts_config_flag(self) -> None:
        """Test parser accepts --config flag."""
        parser = create_parser()
        args = parser.parse_args(["--config", "custom.yaml"])
        assert args.config == "custom.yaml"

    def test_parser_accepts_verbose_flag(self) -> None:
        """Test parser accepts --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_parser_default_values(self) -> None:
        """Test parser default values."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.files == []
        assert args.all is False
        assert args.config == ".naming-convention-exceptions"
        assert args.verbose is False


class TestFormatViolations:
    """Tests for violation formatting."""

    def test_format_no_violations(self) -> None:
        """Test formatting result with no violations."""
        result = ValidationResult(path="good.py")
        formatted = format_violations(result)
        assert "good.py" in formatted
        assert "✗" not in formatted

    def test_format_single_violation(self) -> None:
        """Test formatting result with single violation."""
        validator = NamingConventionValidator()
        result = validator.validate("Bad.py")
        formatted = format_violations(result)
        assert "Bad.py" in formatted
        assert "✗" in formatted

    def test_format_multiple_violations(self) -> None:
        """Test formatting result with multiple violations."""
        validator = NamingConventionValidator()
        result = validator.validate("My File.py")
        formatted = format_violations(result)
        assert "My File.py" in formatted
        # Should have multiple ✗ symbols
        assert formatted.count("✗") >= 2


class TestMainExitCodes:
    """Tests for main function exit codes."""

    def test_exit_success_in_empty_repo(self, tmp_path: Path) -> None:
        """Test returns EXIT_SUCCESS in empty repo."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Change to temp directory so we validate files there, not in the actual repo
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--all"])
            assert exit_code == EXIT_SUCCESS
        finally:
            os.chdir(original_cwd)

    def test_exit_violations_with_bad_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test returns EXIT_VIOLATIONS when violations found."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create a file with invalid name
        (tmp_path / "BadFile.py").write_text("print(1)")

        exit_code = main([str(tmp_path / "BadFile.py")])
        assert exit_code == EXIT_VIOLATIONS

    def test_exit_runtime_error_outside_git_repo(self, tmp_path: Path) -> None:
        """Test returns EXIT_RUNTIME_ERROR outside git repo."""
        # Change to temp directory (not a git repo) to test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--all"])
            assert exit_code == EXIT_RUNTIME_ERROR
        finally:
            os.chdir(original_cwd)

    def test_exit_config_error_with_invalid_yaml(self, tmp_path: Path) -> None:
        """Test returns EXIT_CONFIG_ERROR with invalid YAML."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create invalid YAML config
        config_file = tmp_path / ".naming-convention-exceptions"
        config_file.write_text("invalid: yaml: [")

        exit_code = main(["--config", str(config_file), "--all"])
        assert exit_code == EXIT_CONFIG_ERROR


class TestMainWithFiles:
    """Tests for main function with file arguments."""

    def test_validates_provided_files(self, tmp_path: Path) -> None:
        """Test validates files provided as arguments."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create files
        (tmp_path / "good.py").write_text("print(1)")
        (tmp_path / "Bad.py").write_text("print(2)")

        exit_code = main([str(tmp_path / "good.py")])
        assert exit_code == EXIT_SUCCESS

    def test_validates_multiple_files(self, tmp_path: Path) -> None:
        """Test validates multiple files."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create files
        (tmp_path / "good1.py").write_text("print(1)")
        (tmp_path / "good2.py").write_text("print(2)")

        exit_code = main([str(tmp_path / "good1.py"), str(tmp_path / "good2.py")])
        assert exit_code == EXIT_SUCCESS


class TestMainWithAllFlag:
    """Tests for main function with --all flag."""

    def test_validates_all_tracked_files(self, tmp_path: Path) -> None:
        """Test validates all tracked files with --all."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create and commit valid file
        (tmp_path / "valid.py").write_text("print(1)")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )

        # Change to temp directory so we validate files there
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--all"])
            assert exit_code == EXIT_SUCCESS
        finally:
            os.chdir(original_cwd)

    def test_finds_violations_in_all_files(self, tmp_path: Path) -> None:
        """Test finds violations when scanning all files."""
        import os

        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create and commit file with bad name
        (tmp_path / "BadFile.py").write_text("print(1)")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )

        # Change to temp directory for the test
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--all"])
            assert exit_code == EXIT_VIOLATIONS
        finally:
            os.chdir(original_cwd)


class TestMainWithConfig:
    """Tests for main function with config file."""

    def test_respects_exceptions_from_config(self, tmp_path: Path) -> None:
        """Test respects exceptions from config file."""
        import os

        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create config with exception
        config_file = tmp_path / ".naming-convention-exceptions"
        config_file.write_text("exceptions:\n  - BadFile.py\n")

        # Create file with bad name
        (tmp_path / "BadFile.py").write_text("print(1)")

        # Change to temp directory so paths are relative
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--config", str(config_file), "BadFile.py"])
            assert exit_code == EXIT_SUCCESS
        finally:
            os.chdir(original_cwd)


class TestMainWithVerbose:
    """Tests for main function with verbose flag."""

    def test_verbose_output_includes_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test verbose output includes summary."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        main(["--all", "--verbose"])
        captured = capsys.readouterr()

        assert "Repository root:" in captured.out or "Summary:" in captured.out


class TestPreCommitStyleInvocation:
    """Tests simulating pre-commit style invocation."""

    def test_pre_commit_passes_file_list(self, tmp_path: Path) -> None:
        """Test simulating pre-commit passing list of staged files."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create files
        (tmp_path / "file1.py").write_text("print(1)")
        (tmp_path / "file2.py").write_text("print(2)")

        # Simulate pre-commit passing file list
        exit_code = main(
            [
                str(tmp_path / "file1.py"),
                str(tmp_path / "file2.py"),
            ]
        )

        assert exit_code == EXIT_SUCCESS
