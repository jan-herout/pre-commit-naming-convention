# Pre-Commit Naming Convention Linter

A pre-commit hook that validates file and directory naming conventions in Git repositories.

## ⚠️ Disclaimer

**This code was AI-generated** and is intended as a **single-purpose tool** created for a specific project. It is provided as-is without warranty of any kind. **Use at your own risk.** While the code has been tested, it may contain bugs or edge cases not covered by the test suite. Please review the code thoroughly before using it in production environments.

## Features

- ✅ Validates file and directory names against naming conventions
- ✅ Enforces lowercase alphanumeric names with safe special characters
- ✅ Configurable exceptions via YAML file
- ✅ Supports staged files (default) or full repository scan
- ✅ Integrates with pre-commit framework
- ✅ Cross-platform (Windows, Linux, macOS)

## Installation

### As a Pre-commit Hook

Add to your `.pre-commit-config.yaml`:

#### Option 1: Using the latest commit on main branch (for development)

```yaml
repos:
  - repo: https://github.com/jan-herout/pre-commit-naming-convention
    rev: main  # or use specific commit SHA for reproducibility
    hooks:
      - id: naming-convention-linter
```

#### Option 2: Using a specific commit SHA (recommended for reproducibility)

First, get the latest commit SHA:
```bash
git ls-remote https://github.com/jan-herout/pre-commit-naming-convention.git HEAD
```

Then use it in your config:
```yaml
repos:
  - repo: https://github.com/jan-herout/pre-commit-naming-convention
    rev: <commit-sha>  # e.g., 'abc1234'
    hooks:
      - id: naming-convention-linter
```

**Note**: The `rev` field must be a valid git reference (branch name, tag, or commit SHA). Since this repository doesn't have version tags yet, use `main` or a specific commit SHA.

### Standalone Installation

```bash
pip install pre-commit-naming-convention
```

## Usage

### Command Line

```bash
# Validate staged files (default)
naming-convention-linter

# Validate entire repository
naming-convention-linter --all

# Validate specific files
naming-convention-linter file1.py file2.py

# Use custom config file
naming-convention-linter --config .naming-convention-exceptions

# Verbose output
naming-convention-linter --all --verbose
```

## Naming Convention Rules

All file and directory names must:

- Be lowercase (`a-z`)
- Contain only alphanumeric characters and safe special characters
- Safe special characters allowed:
  - Files: `-` (hyphen), `_` (underscore), `.` (dot)
  - Directories: `-` (hyphen), `_` (underscore)
- Not contain whitespace
- Not contain diacritic characters (e.g., `á`, `é`, `ü`, `ñ`)
- Directories cannot contain dots

### Examples

| Name | Status | Reason |
|------|--------|--------|
| `src/utils/helper.py` | ✅ Valid | - |
| `my-file.txt` | ✅ Valid | - |
| `MyFile.py` | ❌ Invalid | Uppercase letters |
| `my file.txt` | ❌ Invalid | Whitespace |
| `café.txt` | ❌ Invalid | Diacritic character |
| `file@name.txt` | ❌ Invalid | Invalid character `@` |
| `src/.config/` | ❌ Invalid | Dot in directory name |

## Configuration

Create a `.naming-convention-exceptions` file in your repository root:

```yaml
# Files and directories exempt from naming conventions
# Paths are relative to repository root
# Only the specific path is exempt - children are still validated

exceptions:
  - legacy/
  - vendor/
  - README.md
  - LICENSE
  - .github/
```

### Exception Behavior

Exceptions are **non-inheritable**:

```yaml
exceptions:
  - legacy/
```

- ✅ `legacy/` - Exempt from validation
- ❌ `legacy/file.py` - Still validated (child of exempt directory)
- ❌ `legacy/subdir/` - Still validated (child of exempt directory)

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - all files pass validation |
| 1 | Violations found |
| 2 | Configuration error (invalid YAML) |
| 3 | Runtime error |

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/jan-herout/pre-commit-naming-convention
cd pre-commit-naming-convention

# Create virtual environment
uv venv

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests
ruff format src tests
```

### Project Structure

```
src/naming_convention_linter/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface
├── validator.py         # Core validation logic
├── config.py            # Configuration loading
├── git_utils.py         # Git operations
└── exceptions.py        # Custom exceptions
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Note**: This software was generated with AI assistance. It is a single-purpose tool created for a specific use case. Use at your own risk and verify it meets your requirements before deploying in production environments.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest`
2. Code is formatted: `ruff format src tests`
3. Linting passes: `ruff check src tests`
4. Coverage remains above 90%
