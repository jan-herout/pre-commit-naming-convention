"""Command-line interface for naming convention linter.

This module provides the CLI entry point and orchestrates the validation workflow.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from naming_convention_linter.config import ConfigError, ConfigLoader
from naming_convention_linter.git_utils import GitError, GitUtils
from naming_convention_linter.validator import NamingConventionValidator, ValidationResult

if TYPE_CHECKING:
    from collections.abc import Sequence


# Exit codes
EXIT_SUCCESS = 0
EXIT_VIOLATIONS = 1
EXIT_CONFIG_ERROR = 2
EXIT_RUNTIME_ERROR = 3


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="naming-convention-linter",
        description="Validate file and directory naming conventions in Git repositories.",
        epilog="""
Examples:
  # Validate staged files (default)
  naming-convention-linter

  # Validate entire repository
  naming-convention-linter --all

  # Validate specific files
  naming-convention-linter src/utils/helper.py src/main.py

  # Use custom config file
  naming-convention-linter --config .naming-convention-exceptions
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Specific files to validate. If not provided, validates staged files "
            "or all files based on --all flag."
        ),
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Validate all files in the repository instead of just staged files.",
    )

    parser.add_argument(
        "-c",
        "--config",
        default=".naming-convention-exceptions",
        help="Path to the exceptions configuration file (default: .naming-convention-exceptions).",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser


def format_violations(result: ValidationResult) -> str:
    """Format validation violations for display.

    Args:
        result: Validation result containing violations.

    Returns:
        Formatted string with all violations.
    """
    lines = [f"  {result.path}"]
    for violation in result.violations:
        lines.append(f"    ✗ {violation.message}")
    return "\n".join(lines)


def print_results(
    results: list[ValidationResult],
    verbose: bool = False,
) -> None:
    """Print validation results.

    Args:
        results: List of validation results.
        verbose: Whether to print verbose output.
    """
    invalid_results = [r for r in results if not r.is_valid]
    valid_count = len(results) - len(invalid_results)

    if invalid_results:
        print("Naming Convention Violations Found:\n")
        for result in invalid_results:
            print(format_violations(result))
            print()

    if verbose:
        print(f"Summary: {valid_count} valid, {len(invalid_results)} invalid")
        print(f"Total files checked: {len(results)}")


def get_files_to_validate(
    args: argparse.Namespace,
    repo_root: str,
) -> list[str]:
    """Determine which files to validate based on arguments.

    Args:
        args: Parsed command-line arguments.
        repo_root: Repository root path.

    Returns:
        List of file paths to validate.

    Behavior:
        - If files provided as arguments: validate those files
        - If --all flag: validate all tracked files
        - Otherwise: validate staged files
    """
    # If files provided as positional arguments, use those
    if args.files:
        return args.files

    # If --all flag, get all tracked files
    if args.all:
        if args.verbose:
            print("Scanning entire repository...")
        return GitUtils.get_all_repo_files(repo_root)

    # Default: get staged files
    if args.verbose:
        print("Checking staged files...")
    return GitUtils.get_staged_files(repo_root)


def validate_files(
    files: list[str],
    validator: NamingConventionValidator,
    repo_root: str,
    verbose: bool = False,
) -> list[ValidationResult]:
    """Validate a list of files.

    Args:
        files: List of file paths to validate.
        validator: Configured validator instance.
        repo_root: Repository root path.
        verbose: Whether to print verbose output.

    Returns:
        List of validation results.
    """
    # Filter to only existing files
    existing_files = GitUtils.validate_paths_exist(files, repo_root)

    if verbose and len(existing_files) < len(files):
        missing = set(files) - set(existing_files)
        print(f"Warning: {len(missing)} file(s) do not exist and will be skipped:")
        for f in missing:
            print(f"  - {f}")
        print()

    if not existing_files:
        if verbose:
            print("No files to validate.")
        return []

    if verbose:
        print(f"Validating {len(existing_files)} file(s)...\n")

    # Validate all files
    results = validator.validate_batch(existing_files)

    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0=success, 1=violations, 2=config error, 3=runtime error).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        # Check if we're in a Git repository
        if not GitUtils.is_git_repo():
            print("Error: Not a Git repository.", file=sys.stderr)
            print("Please run this command from within a Git repository.", file=sys.stderr)
            return EXIT_RUNTIME_ERROR

        # Find repository root
        repo_root = GitUtils.find_repo_root()

        if args.verbose:
            print(f"Repository root: {repo_root}")

        # Load configuration
        try:
            config_loader = ConfigLoader(args.config)
            config = config_loader.load()
            if args.verbose and config_loader.exists():
                print(f"Loaded config from: {args.config}")
                print(f"Exceptions: {len(config.exceptions)}")
        except ConfigError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

        # Create validator
        validator = NamingConventionValidator(config.exceptions)

        # Get files to validate
        try:
            files_to_validate = get_files_to_validate(args, repo_root)
        except GitError as e:
            print(f"Git Error: {e}", file=sys.stderr)
            return EXIT_RUNTIME_ERROR

        if not files_to_validate:
            if args.verbose:
                print("No files to validate.")
            return EXIT_SUCCESS

        # Validate files
        results = validate_files(
            files_to_validate,
            validator,
            repo_root,
            args.verbose,
        )

        # Print results
        print_results(results, args.verbose)

        # Return appropriate exit code
        invalid_count = sum(1 for r in results if not r.is_valid)
        if invalid_count > 0:
            return EXIT_VIOLATIONS

        if args.verbose:
            print("All files pass naming convention checks.")

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        return EXIT_RUNTIME_ERROR
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    sys.exit(main())
