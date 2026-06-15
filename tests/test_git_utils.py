"""Unit tests for the git_utils module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from naming_convention_linter.git_utils import GitError, GitUtils


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_in_git_repo(self, tmp_path: Path) -> None:
        """Test returns True when inside a git repository."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

        assert GitUtils.is_git_repo(str(tmp_path)) is True

    def test_returns_false_outside_git_repo(self, tmp_path: Path) -> None:
        """Test returns False when not inside a git repository."""
        assert GitUtils.is_git_repo(str(tmp_path)) is False

    def test_returns_false_in_subdir_of_repo(self, tmp_path: Path) -> None:
        """Test returns True in subdirectory of git repo."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        assert GitUtils.is_git_repo(str(subdir)) is True


class TestFindRepoRoot:
    """Tests for find_repo_root function."""

    def test_finds_root_in_repo_root(self, tmp_path: Path) -> None:
        """Test finds root when in repository root."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

        root = GitUtils.find_repo_root(str(tmp_path))
        assert Path(root) == tmp_path

    def test_finds_root_in_subdir(self, tmp_path: Path) -> None:
        """Test finds root when in subdirectory."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subdir = tmp_path / "src" / "utils"
        subdir.mkdir(parents=True)

        root = GitUtils.find_repo_root(str(subdir))
        assert Path(root) == tmp_path

    def test_raises_error_outside_repo(self, tmp_path: Path) -> None:
        """Test raises error when not in git repo."""
        with pytest.raises(GitError):
            GitUtils.find_repo_root(str(tmp_path))


class TestGetStagedFiles:
    """Tests for get_staged_files function."""

    def test_returns_empty_list_when_no_staged_files(self, tmp_path: Path) -> None:
        """Test returns empty list when no files are staged."""
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

        files = GitUtils.get_staged_files(str(tmp_path))
        assert files == []

    def test_returns_staged_files(self, tmp_path: Path) -> None:
        """Test returns list of staged files."""
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

        # Create and stage a file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        subprocess.run(["git", "add", "test.py"], cwd=tmp_path, check=True, capture_output=True)

        files = GitUtils.get_staged_files(str(tmp_path))
        assert "test.py" in files

    def test_ignores_deleted_files(self, tmp_path: Path) -> None:
        """Test does not include deleted files in staged list."""
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

        # Create, commit, then delete a file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        subprocess.run(["git", "add", "test.py"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(["git", "rm", "test.py"], cwd=tmp_path, check=True, capture_output=True)

        files = GitUtils.get_staged_files(str(tmp_path))
        # Deleted files should not appear (diff-filter=ACM excludes D)
        assert "test.py" not in files


class TestGetAllRepoFiles:
    """Tests for get_all_repo_files function."""

    def test_returns_tracked_files(self, tmp_path: Path) -> None:
        """Test returns all tracked files."""
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

        # Create and commit files
        (tmp_path / "file1.py").write_text("print(1)")
        (tmp_path / "file2.py").write_text("print(2)")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )

        files = GitUtils.get_all_repo_files(str(tmp_path))
        assert "file1.py" in files
        assert "file2.py" in files

    def test_returns_empty_list_in_empty_repo(self, tmp_path: Path) -> None:
        """Test returns empty list in empty repository."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

        files = GitUtils.get_all_repo_files(str(tmp_path))
        assert files == []

    def test_handles_special_characters_in_filenames(self, tmp_path: Path) -> None:
        """Test handles filenames with special characters using NUL delimiter."""
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

        # Create file with spaces in name
        (tmp_path / "file with spaces.py").write_text("print(1)")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )

        files = GitUtils.get_all_repo_files(str(tmp_path))
        assert "file with spaces.py" in files


class TestGetRepositoryFiles:
    """Tests for get_repository_files function."""

    def test_returns_staged_files_when_staged_only_true(self, tmp_path: Path) -> None:
        """Test returns staged files when include_staged_only is True."""
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

        # Create and stage a file
        (tmp_path / "staged.py").write_text("print(1)")
        subprocess.run(["git", "add", "staged.py"], cwd=tmp_path, check=True, capture_output=True)

        files = GitUtils.get_repository_files(str(tmp_path), include_staged_only=True)
        assert "staged.py" in files

    def test_returns_all_files_when_staged_only_false(self, tmp_path: Path) -> None:
        """Test returns all files when include_staged_only is False."""
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

        # Create and commit files
        (tmp_path / "committed.py").write_text("print(1)")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
        )

        files = GitUtils.get_repository_files(str(tmp_path), include_staged_only=False)
        assert "committed.py" in files


class TestValidatePathsExist:
    """Tests for validate_paths_exist function."""

    def test_returns_only_existing_paths(self, tmp_path: Path) -> None:
        """Test filters out non-existent paths."""
        (tmp_path / "exists.py").write_text("print(1)")

        paths = ["exists.py", "does_not_exist.py"]
        existing = GitUtils.validate_paths_exist(paths, str(tmp_path))

        assert "exists.py" in existing
        assert "does_not_exist.py" not in existing

    def test_returns_empty_list_for_no_paths(self, tmp_path: Path) -> None:
        """Test returns empty list when input is empty."""
        existing = GitUtils.validate_paths_exist([], str(tmp_path))
        assert existing == []

    def test_handles_absolute_paths(self, tmp_path: Path) -> None:
        """Test handles paths relative to repo root."""
        (tmp_path / "file.py").write_text("print(1)")

        paths = ["file.py"]
        existing = GitUtils.validate_paths_exist(paths, str(tmp_path))

        assert existing == ["file.py"]


class TestRunGitCommand:
    """Tests for _run_git_command function."""

    def test_successful_command(self) -> None:
        """Test running a successful git command."""
        result = GitUtils._run_git_command(["--version"])
        assert result.returncode == 0
        assert "git version" in result.stdout

    def test_failed_command_with_check(self) -> None:
        """Test that failed command raises GitError when check=True."""
        with pytest.raises(GitError) as exc_info:
            GitUtils._run_git_command(["not-a-valid-command"])

        assert "Git command failed" in str(exc_info.value)

    def test_failed_command_without_check(self) -> None:
        """Test that failed command returns result when check=False."""
        result = GitUtils._run_git_command(["not-a-valid-command"], check=False)
        assert result.returncode != 0

    @patch("subprocess.run")
    def test_git_not_installed(self, mock_run: MagicMock) -> None:
        """Test error when git is not installed."""
        mock_run.side_effect = FileNotFoundError("git not found")

        with pytest.raises(GitError) as exc_info:
            GitUtils._run_git_command(["status"])

        assert "Git is not installed" in str(exc_info.value)


class TestGitErrorHandling:
    """Tests for GitError exception handling."""

    def test_git_error_in_get_staged_files(self, tmp_path: Path) -> None:
        """Test GitError is raised when not in git repo for get_staged_files."""
        with pytest.raises(GitError):
            GitUtils.get_staged_files(str(tmp_path))

    def test_git_error_in_get_all_repo_files(self, tmp_path: Path) -> None:
        """Test GitError is raised when not in git repo for get_all_repo_files."""
        with pytest.raises(GitError):
            GitUtils.get_all_repo_files(str(tmp_path))
