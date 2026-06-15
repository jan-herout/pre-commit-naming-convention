# Pre-Commit Naming Convention Linter - Specification

**Version**: 1.0  
**Status**: Draft  
**Date**: 2026-06-15  
**Toolset**: Python, uv, ruff  

---

## 1. Overview

A pre-commit hook that validates file and directory naming conventions in a Git repository. The linter ensures consistent naming across the codebase by enforcing lowercase alphanumeric names with safe special characters only.

### Purpose

- Enforce consistent naming conventions across repository
- Prevent commits with non-compliant file/directory names
- Provide configurable exceptions for specific paths
- Integrate seamlessly with pre-commit framework

---

## 2. Requirements

### 2.1 Functional Requirements

#### Naming Convention Rules

| Rule | Description | Applies To |
|------|-------------|------------|
| **R1** | All names must be lowercase | Files & Directories |
| **R2** | Only alphanumeric characters (a-z, 0-9) allowed | Files & Directories |
| **R3** | Safe special characters permitted: `-` (hyphen), `_` (underscore), `.` (dot) | Files & Directories |
| **R4** | No whitespace characters (space, tab, newline) | Files & Directories |
| **R5** | No extended/diacritic characters (e.g., č, š, ž, ä, ö, ü, ñ) | Files & Directories |

#### Exception Handling

| Rule | Description |
|------|-------------|
| **E1** | Exceptions defined in `.naming-convention-exceptions` YAML file |
| **E2** | Paths in exceptions file are relative to repository root |
| **E3** | Exceptions are **non-inheritable** - only the specific path is exempt |
| **E4** | Files and subdirectories within an excepted folder are still validated |
| **E5** | Both files and directories can be added to exceptions list |

#### Integration Requirements

| Rule | Description |
|------|-------------|
| **I1** | Must work as pre-commit hook in `.pre-commit-config.yaml` |
| **I2** | Must accept list of files to check as command-line arguments (from pre-commit) |
| **I3** | Exit code 0 on success, non-zero on failure |
| **I4** | Provide clear error messages indicating which files violate conventions |
| **I5** | Must handle staged files only (files passed by pre-commit) |

#### Validation Scope Requirements

| Rule | Description |
|------|-------------|
| **V1** | By default, validate only added/modified files (Git staged files) |
| **V2** | Support `--all` or `-a` flag to validate entire repository |
| **V3** | When `--all` is used, traverse all files and directories from repository root |
| **V4** | Respect `.gitignore` when scanning full repository (skip ignored files) |
| **V5** | Always exclude `.git/` directory from validation |

### 2.2 Non-Functional Requirements

| Requirement | Description |
|-------------|-------------|
| **Performance** | Process 1000 files in under 1 second |
| **Dependencies** | Minimal runtime dependencies (preferably stdlib only) |
| **Python Version** | Support Python 3.9+ |
| **Portability** | Work on Windows, Linux, macOS |
| **Error Output** | Clear, actionable error messages |

---

## 3. Architecture

### 3.1 Project Structure

```
pre-commit-naming-convention/
├── .pre-commit-hooks.yaml          # Hook definition for pre-commit framework
├── pyproject.toml                  # Project metadata, dependencies, ruff config
├── uv.lock                         # uv lock file for reproducible builds
├── README.md                       # User documentation
├── src/
│   └── naming_convention_linter/
│       ├── __init__.py
│       ├── cli.py                  # Command-line interface
│       ├── validator.py            # Core validation logic
│       ├── config.py               # Configuration loading and parsing
│       ├── git_utils.py            # Git operations (staged files, repo scanning)
│       └── exceptions.py           # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── test_validator.py           # Unit tests for validator
│   ├── test_config.py              # Unit tests for config loading
│   ├── test_git_utils.py           # Unit tests for Git utilities
│   └── test_cli.py                 # Integration tests for CLI
└── doc/
    └── specs/
        └── pre-commit-naming-convention-linter.md  # This document
```

### 3.2 Component Design

#### 3.2.1 CLI Module (`cli.py`)

**Responsibilities**:
- Parse command-line arguments
- Orchestrate validation workflow
- Format and output error messages
- Return appropriate exit codes

**Interface**:
```python
def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns exit code."""
    ...

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments."""
    ...
```

**Arguments**:
- `files`: Positional arguments - list of file paths to validate (from pre-commit). If not provided and `--all` is not set, uses Git staged files
- `--config`: Path to exceptions config file (default: `.naming-convention-exceptions`)
- `--all, -a`: Validate entire repository instead of just staged/modified files
- `--verbose, -v`: Enable verbose output

**Behavior Matrix**:

| Scenario | Files Provided | `--all` Flag | Action |
|----------|----------------|--------------|--------|
| Pre-commit hook | Yes | No | Validate provided staged files |
| Manual (default) | No | No | Get staged files from Git and validate |
| Manual (full repo) | No | Yes | Scan entire repository and validate all files |
| Manual (override) | Yes | Yes | Ignore files, validate entire repository |

**Git Integration**:

```python
def get_staged_files() -> list[str]:
    """Get list of staged files from Git."""
    # Uses: git diff --cached --name-only --diff-filter=ACM
    # Returns: List of file paths relative to repo root
    ...

def get_all_repo_files(repo_root: str) -> list[str]:
    """Get all files in repository, excluding .git/ and respecting .gitignore."""
    # Walk directory tree
    # Skip .git/ directory
    # Skip files matching .gitignore patterns
    # Returns: List of all file paths
    ...
```

#### 3.2.2 Validator Module (`validator.py`)

**Responsibilities**:
- Validate individual file/directory names
- Check against naming convention rules
- Identify violations with specific error types

**Interface**:
```python
class NamingConventionValidator:
    def __init__(self, exceptions: set[str]):
        """Initialize with set of exception paths."""
        ...
    
    def validate(self, path: str) -> ValidationResult:
        """Validate a single file or directory path."""
        ...
    
    def validate_batch(self, paths: list[str]) -> list[ValidationResult]:
        """Validate multiple paths."""
        ...

class ValidationResult:
    path: str
    is_valid: bool
    violations: list[Violation]

class Violation:
    type: ViolationType  # UPPERCASE, INVALID_CHAR, WHITESPACE, DIACRITIC, DOT_IN_DIR
    message: str
    component: str  # Which part of path violated (filename, dirname)
```

**Validation Rules Implementation**:

```python
# Safe characters regex pattern
SAFE_CHARS = re.compile(r'^[a-z0-9_.-]+$')  # For files
SAFE_CHARS_DIR = re.compile(r'^[a-z0-9_-]+$')  # For directories (no dots)

DIACRITIC_PATTERN = re.compile(r'[\u0300-\u036f\u00c0-\u00ff\u0100-\u017f]')
WHITESPACE_PATTERN = re.compile(r'\s')
```

#### 3.2.3 Config Module (`config.py`)

**Responsibilities**:
- Load and parse `.naming-convention-exceptions` YAML file
- Validate config format
- Provide exception lookup

**Interface**:
```python
class ConfigLoader:
    def __init__(self, config_path: str = ".naming-convention-exceptions"):
        ...
    
    def load(self) -> Config:
        """Load and parse config file."""
        ...
    
    def is_exception(self, path: str) -> bool:
        """Check if path is in exceptions list."""
        ...

@dataclass
class Config:
    exceptions: set[str]  # Normalized relative paths
    
    def normalize_path(self, path: str) -> str:
        """Normalize path for comparison."""
        ...
```

**Config File Format** (`.naming-convention-exceptions`):

```yaml
# List of files and directories that are exempt from naming conventions
# Paths are relative to repository root
# Only the specific path is exempt - children are still validated

exceptions:
  - legacy_data/
  - src/old_module/
  - README.md
  - .github/
  - vendor/
```

**Config Validation**:
- YAML must be valid
- `exceptions` key must be a list
- Each exception must be a string
- Paths should be relative (no leading `/`)

#### 3.2.4 Git Utilities Module (`git_utils.py`)

**Responsibilities**:
- Retrieve list of staged files from Git
- Scan entire repository for all files
- Respect `.gitignore` patterns
- Find repository root

**Interface**:
```python
class GitUtils:
    @staticmethod
    def get_staged_files(repo_root: str | None = None) -> list[str]:
        """Get list of added/modified staged files from Git.
        
        Uses porcelain command:
        git diff --cached --name-only --diff-filter=ACM
        
        Returns: List of file paths relative to repo root
        """
        ...
    
    @staticmethod
    def get_all_repo_files(repo_root: str | None = None) -> list[str]:
        """Get all tracked files in repository.
        
        Uses porcelain command:
        git ls-files -z  # NUL-delimited for special chars
        
        - Excludes .git/ directory
        - Respects .gitignore patterns
        - Returns: List of file paths relative to repo root
        """
        ...
    
    @staticmethod
    def find_repo_root(start_path: str = ".") -> str:
        """Find Git repository root from given path.
        
        Uses stable plumbing command:
        git rev-parse --show-toplevel
        """
        ...
    
    @staticmethod
    def is_git_repo(path: str = ".") -> bool:
        """Check if path is inside a Git repository.
        
        Uses stable plumbing command:
        git rev-parse --git-dir
        """
        ...
```

**Git Command Details**:

> **Note on Porcelain**: Use Git's porcelain commands and stable output formats for reliable parsing. Porcelain commands guarantee stable, machine-readable output that won't change between Git versions.

```python
# Get staged files (added, copied, modified)
# --name-only: machine-readable list of paths
# --diff-filter=ACM: Only Added, Copied, Modified (not Deleted, Renamed)
git diff --cached --name-only --diff-filter=ACM

# Get all tracked files (porcelain format)
# -z: Use NUL character as delimiter (handles special characters in filenames)
# This is porcelain format - stable output
git ls-files -z

# Alternative for untracked files (if needed):
# --porcelain: Machine-readable format
git status --porcelain

# Find repo root (stable plumbing command)
git rev-parse --show-toplevel

# Check if git repo (stable plumbing command)
git rev-parse --git-dir
```

**Porcelain Command Guidelines**:
- Use `--porcelain` flag where available (e.g., `git status --porcelain`)
- Use `-z` flag with NUL delimiters for filename lists to handle special characters
- Use `-porcelain` or `-name-only` flags instead of parsing human-readable output
- Prefer plumbing commands (`rev-parse`, `ls-files`) over porcelain when appropriate
- Never parse human-formatted output that may change between Git versions

### 3.3 Validation Algorithm

```python
def validate_path(path: str, exceptions: set[str]) -> ValidationResult:
    """
    1. Check if path is in exceptions list
       - If yes, return valid (but continue checking children)
    
    2. Split path into components
       - For file: dirname components + filename
       - For directory: all components
    
    3. Validate each component:
       - Check lowercase
       - Check allowed characters
       - Check no whitespace
       - Check no diacritics
       - For directories: check no dots
    
    4. Return result with all violations
    """
```

**Exception Handling Logic**:

```
Path: src/old_module/utils/helper.py
Exceptions: ["src/old_module/"]

Check 1: Is "src/old_module/utils/helper.py" in exceptions? No
Check 2: Is "src/old_module/utils/" in exceptions? No
Check 3: Is "src/old_module/" in exceptions? Yes -> Skip validation for this component
         But continue checking: "utils/helper.py"
         Validate "utils" - must pass
         Validate "helper.py" - must pass
```

---

## 4. Implementation Details

### 4.1 Pre-Commit Hook Configuration

**.pre-commit-hooks.yaml** (for this repository to be used by others):

```yaml
- id: naming-convention-linter
  name: Naming Convention Linter
  description: Validates file and directory naming conventions
  entry: naming-convention-linter
  language: python
  files: ''  # Run on all files
  pass_filenames: true
  require_serial: false
  additional_dependencies: []
```

**Usage in consumer's `.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/your-org/pre-commit-naming-convention
    rev: v1.0.0
    hooks:
      - id: naming-convention-linter
        args: ['--config', '.naming-convention-exceptions']
```

### 4.2 Command-Line Usage

**Validate staged files only (default)**:
```bash
# In a Git repository, validates only added/modified staged files
naming-convention-linter

# Same as above, explicit
naming-convention-linter --config .naming-convention-exceptions
```

**Validate entire repository**:
```bash
# Scan and validate all files in the repository
naming-convention-linter --all

# Short form
naming-convention-linter -a

# With custom config
naming-convention-linter -a --config .naming-convention-exceptions
```

**Validate specific files (pre-commit mode)**:
```bash
# Used by pre-commit framework - validates provided files
naming-convention-linter src/utils/helper.py src/main.py
```

**Verbose output**:
```bash
naming-convention-linter -v
naming-convention-linter --all --verbose
```

### 4.3 Package Configuration

**pyproject.toml**:

```toml
[project]
name = "pre-commit-naming-convention"
version = "1.0.0"
description = "Pre-commit hook for validating file and directory naming conventions"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
dependencies = [
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
]

[project.scripts]
naming-convention-linter = "naming_convention_linter.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py39"
line-length = 100
select = ["E", "F", "W", "I", "N", "D", "UP", "B", "C4", "SIM"]

[tool.ruff.pydocstyle]
convention = "google"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=src/naming_convention_linter --cov-report=term-missing"
```

### 4.3 Error Messages

**Format**:
```
Naming Convention Violations Found:

  src/MyModule/
    ✗ Directory contains uppercase letters: "MyModule" should be "mymodule"
    ✗ Invalid character in directory name: "MyModule" (only a-z, 0-9, -, _ allowed)

  src/utils/Helper Functions.py
    ✗ File contains uppercase letters: "Helper Functions.py" should be "helper functions.py"
    ✗ File contains whitespace: "Helper Functions.py" should be "helper_functions.py"

  src/data/café.txt
    ✗ File contains diacritic character: "café.txt" should be "cafe.txt"

  src/utils/my file.txt
    ✗ File contains whitespace: "my file.txt" should be "my_file.txt"
```

**Exit Codes**:
- `0`: All files pass validation
- `1`: One or more violations found
- `2`: Configuration error (invalid YAML, etc.)
- `3`: Runtime error

---

## 5. Testing Strategy

### 5.1 Unit Tests

**test_validator.py**:
- Test valid names (lowercase, alphanumeric, safe chars)
- Test uppercase detection
- Test invalid character detection
- Test whitespace detection
- Test diacritic detection
- Test dot in directory detection
- Test exception matching

**test_config.py**:
- Test config loading from YAML
- Test invalid YAML handling
- Test missing config file handling
- Test path normalization
- Test exception lookup

**test_git_utils.py**:
- Test getting staged files from Git using porcelain commands
- Test scanning entire repository with NUL-delimited output
- Test handling filenames with special characters (spaces, quotes, etc.)
- Test .gitignore respect
- Test finding repo root
- Test handling non-git directories
- Test porcelain output parsing stability

**test_cli.py**:
- Test argument parsing
- Test exit codes
- Test output formatting
- Test verbose mode
- Test `--all` flag for full repo validation
- Test integration with pre-commit style invocation

### 5.2 Test Cases

| Test Case | Input | Expected |
|-----------|-------|----------|
| Valid file | `src/utils/helper.py` | Pass |
| Valid dir | `src/my-module/` | Pass |
| Valid dir with dot | `src/.config/` | Pass - dots allowed in dirs |
| Valid dir version | `src/v1.0.0/` | Pass - dots allowed in dirs |
| Uppercase | `src/MyFile.txt` | Fail - uppercase |
| Whitespace | `src/my file.txt` | Fail - whitespace |
| Diacritic | `src/café.txt` | Fail - diacritic |
| Invalid char | `src/file@name.txt` | Fail - invalid char |
| Exception match | `legacy/` in exceptions | Pass for `legacy/` only |
| Exception child | `legacy/data.txt` | Fail (child not exempt) |
| Multiple violations | `My File@.txt` | Fail - multiple errors |
| **Staged files** | Run without args in repo with staged `BadFile.txt` | Fail - validates staged files |
| **Full repo scan** | Run with `--all` flag | Validates all files in repo |
| **Gitignore respect** | File in `node_modules/` | Skipped in full repo scan |
| **Non-git dir** | Run outside Git repo | Error - not a git repository |

---

## 6. Development Plan

### Phase 1: Core Implementation
1. Set up project structure with `pyproject.toml`
2. Implement `validator.py` with validation logic
3. Implement `config.py` for YAML config loading
4. Implement `git_utils.py` for Git operations
5. Implement `cli.py` with argument parsing and scope selection

### Phase 2: Testing
1. Write comprehensive unit tests
2. Add integration tests
3. Set up ruff for linting
4. Achieve 90%+ test coverage

### Phase 3: Documentation
1. Write README.md with usage instructions
2. Add examples and configuration guide
3. Create `.pre-commit-hooks.yaml`

### Phase 4: Release
1. Tag version 1.0.0
2. Publish to PyPI (optional)
3. Test integration with real pre-commit setup

---

## 7. Configuration Examples

### 7.1 Basic Example

```yaml
# .naming-convention-exceptions
exceptions:
  - README.md
  - LICENSE
  - .github/
```

### 7.2 Complex Example

```yaml
# .naming-convention-exceptions
# Comments are supported

exceptions:
  # Legacy code that cannot be renamed
  - legacy/
  - old_migrations/
  
  # Third-party vendored code
  - vendor/
  - third_party/
  
  # Special files
  - README.md
  - CHANGELOG.md
  - CONTRIBUTING.md
  
  # Hidden directories
  - .github/
  - .vscode/
```

---

## 8. Success Criteria

- [ ] Linter validates staged files by default
- [ ] Linter validates all repository files with `--all` flag
- [ ] Respects `.gitignore` in full repository scan
- [ ] Linter exits with code 0 on success, non-zero on failure
- [ ] Exceptions file works as specified (non-inheritable)
- [ ] Clear, actionable error messages
- [ ] Works on Windows, Linux, and macOS
- [ ] Python 3.9+ compatible
- [ ] 90%+ test coverage
- [ ] Passes ruff linting
- [ ] Successfully integrates with pre-commit framework

---

## 9. Open Questions

1. Should we support regex patterns in exceptions?
2. Should we allow configuration of allowed characters?
3. Should we support case-insensitive exceptions matching?
4. Should we provide an auto-fix mode that renames files?

**Decision**: Start with simple literal matching for exceptions. Consider regex support in v2.0 if requested.

---

## Appendix A: Safe Characters Reference

**Allowed in both files and directories**:
- Lowercase letters: `a-z`
- Digits: `0-9`
- Hyphen: `-`
- Underscore: `_`

**Allowed only in files**:
- Dot: `.` (for extensions)

**Not allowed**:
- Uppercase letters: `A-Z`
- Whitespace: ` `, `\t`, `\n`
- Diacritics: `á`, `é`, `í`, `ó`, `ú`, `ñ`, `ç`, `ü`, `ö`, `ä`, etc.
- Special chars: `@`, `#`, `$`, `%`, `&`, `*`, `(`, `)`, `[`, `]`, `{`, `}`, etc.
- Path separators: `/`, `\` (these separate components, not part of names)
