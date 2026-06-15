"""Git utilities for naming convention linter.

This module provides functions to interact with Git repositories using
porcelain commands for reliable, machine-readable output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class GitError(Exception):
    """Exception raised for Git-related errors."""

    pass


class GitUtils:
    """Utility class for Git operations.

    All methods use porcelain commands to ensure stable, machine-readable
    output that won't change between Git versions.
    """

    @staticmethod
    def _run_git_command(
        args: Sequence[str],
        cwd: str | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a Git command and return the result.

        Args:
            args: Git command arguments.
            cwd: Working directory for the command.
            check: Whether to raise an exception on non-zero exit code.

        Returns:
            CompletedProcess with stdout, stderr, and returncode.

        Raises:
            GitError: If the command fails and check is True.
        """
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
                check=False,
            )

            if check and result.returncode != 0:
                raise GitError(f"Git command failed: {' '.join(args)}\nstderr: {result.stderr}")

            return result
        except FileNotFoundError as e:
            raise GitError("Git is not installed or not in PATH") from e
        except OSError as e:
            raise GitError(f"Failed to run Git command: {e}") from e

    @staticmethod
    def is_git_repo(path: str = ".") -> bool:
        """Check if the given path is inside a Git repository.

        Uses the plumbing command: git rev-parse --git-dir

        Args:
            path: Path to check (default: current directory).

        Returns:
            True if inside a Git repository, False otherwise.
        """
        try:
            result = GitUtils._run_git_command(
                ["rev-parse", "--git-dir"],
                cwd=path,
                check=False,
            )
            return result.returncode == 0
        except GitError:
            return False

    @staticmethod
    def find_repo_root(start_path: str = ".") -> str:
        """Find the Git repository root from the given path.

        Uses the plumbing command: git rev-parse --show-toplevel

        Args:
            start_path: Path to start searching from (default: current directory).

        Returns:
            Absolute path to the repository root.

        Raises:
            GitError: If not inside a Git repository.
        """
        result = GitUtils._run_git_command(
            ["rev-parse", "--show-toplevel"],
            cwd=start_path,
        )
        return result.stdout.strip()

    @staticmethod
    def get_staged_files(repo_root: str | None = None) -> list[str]:
        """Get list of added/modified staged files.

        Uses the porcelain command:
        git diff --cached --name-only --diff-filter=ACM

        This returns only Added, Copied, and Modified files (not Deleted or Renamed).
        Output is one filename per line, suitable for machine parsing.

        Args:
            repo_root: Repository root path. If None, uses current directory.

        Returns:
            List of file paths relative to repository root.

        Raises:
            GitError: If not inside a Git repository or Git command fails.
        """
        # Use porcelain command for machine-readable output
        result = GitUtils._run_git_command(
            ["diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_root,
        )

        # Parse output - one file per line
        if not result.stdout.strip():
            return []

        # Split by newlines and filter empty lines
        files = [line for line in result.stdout.strip().split("\n") if line]
        return files

    @staticmethod
    def get_all_repo_files(repo_root: str | None = None) -> list[str]:
        """Get all tracked files in the repository.

        Uses the porcelain command with NUL-delimited output:
        git ls-files -z

        The -z flag uses NUL characters as delimiters instead of newlines,
        which correctly handles filenames containing special characters
        like spaces, newlines, or quotes.

        Args:
            repo_root: Repository root path. If None, uses current directory.

        Returns:
            List of all tracked file paths relative to repository root.

        Raises:
            GitError: If not inside a Git repository or Git command fails.
        """
        # Use porcelain command with NUL-delimited output for special chars
        result = GitUtils._run_git_command(
            ["ls-files", "-z"],
            cwd=repo_root,
        )

        # Parse NUL-delimited output
        if not result.stdout:
            return []

        # Split by NUL character and filter empty entries
        files = [f for f in result.stdout.split("\x00") if f]
        return files

    @staticmethod
    def get_repository_files(
        repo_root: str | None = None,
        include_staged_only: bool = False,
    ) -> list[str]:
        """Get files to validate from the repository.

        This is a convenience method that returns either staged files only
        or all tracked files based on the include_staged_only parameter.

        Args:
            repo_root: Repository root path. If None, uses current directory.
            include_staged_only: If True, return only staged files.
                               If False, return all tracked files.

        Returns:
            List of file paths relative to repository root.
        """
        if include_staged_only:
            return GitUtils.get_staged_files(repo_root)
        return GitUtils.get_all_repo_files(repo_root)

    @staticmethod
    def validate_paths_exist(paths: list[str], repo_root: str | None = None) -> list[str]:
        """Filter paths to only include those that exist.

        Args:
            paths: List of paths to validate.
            repo_root: Repository root path. If None, uses current directory.

        Returns:
            List of paths that exist.
        """
        if repo_root is None:
            repo_root = "."

        existing_paths = []
        root = Path(repo_root)

        for path in paths:
            full_path = root / path
            if full_path.exists():
                existing_paths.append(path)

        return existing_paths
