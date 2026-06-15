# Pre-Commit Naming Convention Linter - Implementation Plan

**Version**: 1.0  
**Status**: Draft  
**Date**: 2026-06-15  
**Estimated Duration**: 2-3 days  

---

## Executive Summary

This document outlines the implementation plan for the pre-commit naming convention linter. The project is organized into 4 phases with a total of 15 deliverables.

**Success Criteria**:
- All tests passing with 90%+ coverage
- Passes ruff linting with zero warnings
- Successfully validates staged files by default
- Successfully validates full repository with `--all` flag
- Works as pre-commit hook in real repositories

---

## Phase 1: Project Setup & Core Implementation

**Duration**: Day 1 (Morning - Afternoon)  
**Goal**: Create working MVP with all core functionality  

### Task 1.1: Project Structure Setup
**Priority**: High  
**Estimated Time**: 30 minutes  
**Dependencies**: None  

**Deliverables**:
- [ ] Create directory structure
- [ ] Initialize `pyproject.toml` with project metadata
- [ ] Set up ruff configuration
- [ ] Configure pytest with coverage
- [ ] Create `.gitignore`

**Commands**:
```bash
mkdir -p src/naming_convention_linter tests doc/specs
touch src/naming_convention_linter/__init__.py
touch tests/__init__.py
```

**Acceptance Criteria**:
- `pyproject.toml` contains all required metadata
- `uv sync` installs dependencies successfully
- `ruff check` runs without errors on empty files

---

### Task 1.2: Validator Module (`validator.py`)
**Priority**: High  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.1  

**Deliverables**:
- [ ] Create `ValidationResult` dataclass
- [ ] Create `Violation` dataclass with `ViolationType` enum
- [ ] Implement `NamingConventionValidator` class
- [ ] Implement validation rules:
  - [ ] R1: Lowercase check
  - [ ] R2: Alphanumeric characters only
  - [ ] R3: Safe special characters (`-`, `_`, `.` for files)
  - [ ] R4: No whitespace
  - [ ] R5: No diacritics
  - [ ] R6: No dots in directory names
- [ ] Implement non-inheritable exception logic
- [ ] Add comprehensive docstrings

**Key Implementation Details**:
```python
# Regex patterns
SAFE_CHARS_FILE = re.compile(r'^[a-z0-9_.-]+$')
SAFE_CHARS_DIR = re.compile(r'^[a-z0-9_-]+$')
WHITESPACE_PATTERN = re.compile(r'\s')
DIACRITIC_PATTERN = re.compile(r'[\u0300-\u036f\u00c0-\u00ff\u0100-\u017f]')
```

**Test-Driven Development**:
Write tests first, then implement to make them pass.

**Acceptance Criteria**:
- All validation rules implemented according to spec
- Exception handling works correctly (non-inheritable)
- 100% unit test coverage for validator module

---

### Task 1.3: Configuration Module (`config.py`)
**Priority**: High  
Estimated Time: 45 minutes  
**Dependencies**: Task 1.1  

**Deliverables**:
- [ ] Create `Config` dataclass
- [ ] Implement `ConfigLoader` class
- [ ] Implement YAML parsing with PyYAML
- [ ] Implement path normalization
- [ ] Add config validation
- [ ] Handle missing config file gracefully
- [ ] Add comprehensive docstrings

**Configuration Schema**:
```yaml
exceptions:
  - path/to/exception/
  - another_file.txt
```

**Error Handling**:
- Invalid YAML: Exit code 2 with clear error message
- Missing config: Continue with empty exceptions list
- Invalid path format: Warning, skip invalid entry

**Acceptance Criteria**:
- Successfully loads valid YAML config
- Handles missing config file (empty exceptions)
- Validates config structure
- Normalizes paths for comparison

---

### Task 1.4: Git Utilities Module (`git_utils.py`)
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.1  

**Deliverables**:
- [ ] Implement `get_staged_files()` using porcelain commands
- [ ] Implement `get_all_repo_files()` with NUL-delimited parsing
- [ ] Implement `find_repo_root()`
- [ ] Implement `is_git_repo()`
- [ ] Handle special characters in filenames (spaces, newlines)
- [ ] Add comprehensive error handling
- [ ] Add comprehensive docstrings

**Git Commands**:
```python
# Staged files
git diff --cached --name-only --diff-filter=ACM

# All files (NUL-delimited)
git ls-files -z

# Repo root
git rev-parse --show-toplevel
```

**Edge Cases to Handle**:
- Filenames with spaces
- Filenames with newlines
- Filenames with quotes
- Empty repositories
- Non-git directories
- Files in submodules

**Acceptance Criteria**:
- Correctly retrieves staged files
- Correctly retrieves all tracked files
- Handles special characters in filenames
- Works outside git repo (graceful error)

---

### Task 1.5: CLI Module (`cli.py`)
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Tasks 1.2, 1.3, 1.4  

**Deliverables**:
- [ ] Implement argument parsing with `argparse`
- [ ] Support positional file arguments
- [ ] Support `--all` / `-a` flag
- [ ] Support `--config` flag
- [ ] Support `--verbose` / `-v` flag
- [ ] Implement validation orchestration logic
- [ ] Implement formatted error output
- [ ] Implement exit codes (0=success, 1=violations, 2=config error, 3=runtime error)
- [ ] Add main entry point

**Argument Parsing**:
```python
parser.add_argument('files', nargs='*', help='Files to validate')
parser.add_argument('-a', '--all', action='store_true', help='Validate all repo files')
parser.add_argument('-c', '--config', default='.naming-convention-exceptions', help='Config file path')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
```

**Behavior Logic**:
```python
if args.files:
    files_to_check = args.files
elif args.all:
    files_to_check = git_utils.get_all_repo_files()
else:
    files_to_check = git_utils.get_staged_files()
```

**Acceptance Criteria**:
- Correctly handles all argument combinations
- Proper exit codes
- Clear, formatted error output
- Works with pre-commit framework

---

### Task 1.6: Integration & Manual Testing
**Priority**: Medium  
**Estimated Time**: 30 minutes  
**Dependencies**: Tasks 1.2, 1.3, 1.4, 1.5  

**Deliverables**:
- [ ] Create test git repository
- [ ] Create sample files (valid and invalid names)
- [ ] Test staged file validation
- [ ] Test `--all` flag
- [ ] Test exception handling
- [ ] Verify error output format

**Test Commands**:
```bash
# Install in development mode
uv pip install -e .

# Test staged files
naming-convention-linter

# Test full repo
naming-convention-linter --all

# Test with config
naming-convention-linter --config .naming-convention-exceptions
```

**Acceptance Criteria**:
- CLI runs without errors
- Correctly identifies violations
- Respects exceptions
- Proper exit codes

---

## Phase 2: Testing & Quality Assurance

**Duration**: Day 1 (Evening) - Day 2 (Morning)  
**Goal**: Achieve 90%+ coverage, all tests passing  

### Task 2.1: Unit Tests for Validator
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.2  

**Deliverables**:
- [ ] `test_validator.py` with comprehensive tests
- [ ] Test valid names
- [ ] Test uppercase detection
- [ ] Test invalid character detection
- [ ] Test whitespace detection
- [ ] Test diacritic detection
- [ ] Test dot in directory detection
- [ ] Test exception matching
- [ ] Test exception non-inheritability
- [ ] Test multiple violations

**Test Coverage Target**: 100% for validator module

---

### Task 2.2: Unit Tests for Config
**Priority**: High  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 1.3  

**Deliverables**:
- [ ] `test_config.py` with comprehensive tests
- [ ] Test valid YAML loading
- [ ] Test invalid YAML handling
- [ ] Test missing config file
- [ ] Test path normalization
- [ ] Test exception lookup
- [ ] Test config validation

**Test Coverage Target**: 100% for config module

---

### Task 2.3: Unit Tests for Git Utils
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.4  

**Deliverables**:
- [ ] `test_git_utils.py` with comprehensive tests
- [ ] Test `get_staged_files()` with mock Git
- [ ] Test `get_all_repo_files()` with mock Git
- [ ] Test special characters in filenames
- [ ] Test finding repo root
- [ ] Test non-git directory handling
- [ ] Test porcelain output parsing

**Test Strategy**:
- Use `unittest.mock` to mock subprocess calls
- Test edge cases (empty repos, special chars)
- Verify command generation

**Test Coverage Target**: 100% for git_utils module

---

### Task 2.4: Integration Tests for CLI
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.5  

**Deliverables**:
- [ ] `test_cli.py` with integration tests
- [ ] Test argument parsing
- [ ] Test exit codes
- [ ] Test output formatting
- [ ] Test verbose mode
- [ ] Test `--all` flag
- [ ] Test pre-commit style invocation

**Test Strategy**:
- Use `pytest` fixtures for temp directories
- Create real Git repositories in temp dirs
- Test end-to-end workflows

---

### Task 2.5: Run Full Test Suite & Coverage
**Priority**: High  
**Estimated Time**: 30 minutes  
**Dependencies**: Tasks 2.1, 2.2, 2.3, 2.4  

**Deliverables**:
- [ ] Run `pytest` with coverage
- [ ] Achieve 90%+ overall coverage
- [ ] Fix any failing tests
- [ ] Address coverage gaps

**Commands**:
```bash
pytest --cov=src/naming_convention_linter --cov-report=term-missing
pytest --cov=src/naming_convention_linter --cov-report=html
```

**Acceptance Criteria**:
- All tests passing
- 90%+ code coverage
- No coverage gaps in critical paths

---

### Task 2.6: Ruff Linting & Code Quality
**Priority**: Medium  
**Estimated Time**: 30 minutes  
**Dependencies**: Tasks 2.1, 2.2, 2.3, 2.4  

**Deliverables**:
- [ ] Run `ruff check`
- [ ] Run `ruff format`
- [ ] Fix all linting errors
- [ ] Ensure consistent code style

**Commands**:
```bash
ruff check src tests
ruff format src tests
```

**Acceptance Criteria**:
- Zero ruff warnings
- Consistent formatting across codebase

---

## Phase 3: Documentation & Hook Configuration

**Duration**: Day 2 (Afternoon)  
**Goal**: Complete documentation and pre-commit hook setup  

### Task 3.1: Create README.md
**Priority**: High  
**Estimated Time**: 1 hour  
**Dependencies**: Phase 1 & 2 complete  

**Deliverables**:
- [ ] Project description
- [ ] Installation instructions
- [ ] Usage examples
- [ ] Configuration guide
- [ ] Integration with pre-commit
- [ ] Development setup
- [ ] License information

**Sections**:
1. Overview
2. Features
3. Installation
4. Quick Start
5. Usage
   - Staged files (default)
   - Full repository scan
   - With configuration
6. Configuration
   - Exception file format
   - Examples
7. Pre-commit Integration
8. Development
9. License

---

### Task 3.2: Create .pre-commit-hooks.yaml
**Priority**: High  
**Estimated Time**: 15 minutes  
**Dependencies**: Phase 1 & 2 complete  

**Deliverables**:
- [ ] Hook definition file
- [ ] Proper entry point
- [ ] Language specification
- [ ] File matching rules

**Content**:
```yaml
- id: naming-convention-linter
  name: Naming Convention Linter
  description: Validates file and directory naming conventions
  entry: naming-convention-linter
  language: python
  files: ''
  pass_filenames: true
  require_serial: false
```

---

### Task 3.3: Update Project Documentation
**Priority**: Medium  
**Estimated Time**: 30 minutes  
**Dependencies**: Tasks 3.1, 3.2  

**Deliverables**:
- [ ] Review and update `doc/specs/`
- [ ] Add CHANGELOG.md (initial version)
- [ ] Add CONTRIBUTING.md (optional)

---

## Phase 4: Release & Integration Testing

**Duration**: Day 3 (Morning)  
**Goal**: Release-ready package  

### Task 4.1: Build Package
**Priority**: High  
**Estimated Time**: 15 minutes  
**Dependencies**: Phase 3 complete  

**Deliverables**:
- [ ] Build package with `hatchling`
- [ ] Verify package structure
- [ ] Test installation from built package

**Commands**:
```bash
python -m build
pip install dist/*.whl
```

---

### Task 4.2: Real Repository Integration Test
**Priority**: High  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 4.1  

**Deliverables**:
- [ ] Create test repository with various file names
- [ ] Set up `.pre-commit-config.yaml`
- [ ] Test pre-commit hook execution
- [ ] Verify violations are caught
- [ ] Verify exceptions work

**Test Repository Structure**:
```
test-repo/
├── good_file.py
├── BadFile.py          # Should fail
├── file with spaces.txt # Should fail
├── valid_dir/
│   └── nested_file.py
└── .naming-convention-exceptions
```

**Acceptance Criteria**:
- Works as pre-commit hook
- Catches violations
- Respects exceptions
- Proper exit codes

---

### Task 4.3: Final Review & Tagging
**Priority**: Medium  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 4.2  

**Deliverables**:
- [ ] Final code review
- [ ] Update version to 1.0.0
- [ ] Create git tag `v1.0.0`
- [ ] Push to repository

**Commands**:
```bash
git add .
git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "Initial release"
git push origin main --tags
```

---

## Development Schedule

### Day 1
| Time | Task | Duration |
|------|------|----------|
| 09:00-09:30 | Task 1.1: Project Setup | 30 min |
| 09:30-11:00 | Task 1.2: Validator Module | 90 min |
| 11:00-11:45 | Task 1.3: Config Module | 45 min |
| 11:45-12:45 | Task 1.4: Git Utils Module | 60 min |
| 12:45-13:45 | Lunch Break | 60 min |
| 13:45-14:45 | Task 1.5: CLI Module | 60 min |
| 14:45-15:15 | Task 1.6: Integration Testing | 30 min |
| 15:15-16:15 | Task 2.1: Validator Tests | 60 min |
| 16:15-17:00 | Task 2.2: Config Tests | 45 min |

### Day 2
| Time | Task | Duration |
|------|------|----------|
| 09:00-10:00 | Task 2.3: Git Utils Tests | 60 min |
| 10:00-11:00 | Task 2.4: CLI Integration Tests | 60 min |
| 11:00-11:30 | Task 2.5: Coverage & Fixes | 30 min |
| 11:30-12:00 | Task 2.6: Ruff Linting | 30 min |
| 12:00-13:00 | Lunch Break | 60 min |
| 13:00-14:00 | Task 3.1: README.md | 60 min |
| 14:00-14:15 | Task 3.2: Pre-commit Hooks | 15 min |
| 14:15-14:45 | Task 3.3: Documentation Update | 30 min |

### Day 3
| Time | Task | Duration |
|------|------|----------|
| 09:00-09:15 | Task 4.1: Build Package | 15 min |
| 09:15-09:45 | Task 4.2: Integration Test | 30 min |
| 09:45-10:15 | Task 4.3: Final Review & Tag | 30 min |
| 10:15-10:30 | Buffer / Fix Issues | 15 min |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Git command parsing issues | Low | High | Use porcelain commands, extensive testing |
| Path handling on Windows | Medium | Medium | Test on Windows, use `pathlib` |
| Special characters in filenames | Medium | High | Use NUL-delimited output, test edge cases |
| Coverage below 90% | Low | Medium | Write tests alongside implementation |
| Integration with pre-commit | Low | High | Real repository testing in Phase 4 |

---

## Development Environment Setup

**Prerequisites**:
- Python 3.9+
- uv (package manager)
- Git

**Setup Commands**:
```bash
# Clone repository
cd /home/jan/git/pre-commit-naming-convention

# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Verify setup
pytest --version
ruff --version
```

---

## Testing Checklist

**Before Each Commit**:
- [ ] All unit tests pass
- [ ] Code coverage >= 90%
- [ ] Ruff linting passes
- [ ] Manual CLI test passes

**Before Phase Completion**:
- [ ] All phase tasks complete
- [ ] Documentation updated
- [ ] Code reviewed

**Before Release**:
- [ ] Integration test in real repo
- [ ] All acceptance criteria met
- [ ] Version bumped
- [ ] Tag created

---

## Next Steps

1. **Begin Phase 1**: Start with Task 1.1 (Project Setup)
2. **TDD Approach**: Write tests before implementation
3. **Incremental Testing**: Test each module as it's built
4. **Daily Standups**: Review progress and adjust plan

**Ready to begin implementation?**
