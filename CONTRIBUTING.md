# Contributing to GT Logs Helper

Thank you for your interest in contributing to GT Logs Helper! This
document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- AWS CLI installed and configured
- Git for version control

### Development Setup

```bash
# Clone the repository
git clone https://github.com/markotrapani/gtlogs-helper.git
cd gtlogs-helper

# Make the script executable
chmod +x gtlogs-helper.py

# Run tests
python3 tests/test_v1_2_0.py
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid
duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, AWS CLI version)
- **Error messages** or relevant logs

### Suggesting Features

Feature requests are welcome! Please:

- Check [docs/ROADMAP.md](docs/ROADMAP.md) for planned features
- Explain the use case and expected behavior
- Consider backwards compatibility
- Discuss major changes before implementation

### Pull Requests

1. **Fork the repository** and create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Test your changes**:

   ```bash
   # Run automated tests
   python3 tests/test_suite.py

   # Test manually with various inputs
   ./gtlogs-helper.py -i
   ```

4. **Lint markdown files** (if you modified documentation):

   ```bash
   markdownlint --fix '**/*.md' --ignore node_modules --ignore venv
   markdownlint '**/*.md' --ignore node_modules --ignore venv
   ```

5. **Commit your changes** with clear commit messages:

   ```bash
   git commit -m "feat: Add support for ENG- Jira prefix"
   ```

6. **Push to your fork** and submit a pull request:

   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **type hints** for function parameters and return values
- Keep functions **focused and single-purpose**
- Add **docstrings** for all functions
- Maximum line length: **88 characters** (Black formatter default)

### Code Organization

```python
# Good: Clear function with type hints and docstring
def validate_zendesk_id(zd_id: str) -> str:
    """
    Validate and format Zendesk ticket ID.

    Args:
        zd_id: Zendesk ID in format '145980' or 'ZD-145980'

    Returns:
        Formatted ID as 'ZD-145980'

    Raises:
        ValueError: If ID is invalid
    """
    # Implementation here
    pass
```

### Markdown Style

All markdown files must pass strict linting:

- **Maximum 80 characters per line**
- Use **ATX-style headings** (`#`, `##`, `###`)
- Surround headings and lists with **blank lines**
- Always specify **language for code blocks**
- Use **reference-style links** for long URLs

Run `markdownlint '**/*.md'` before committing documentation changes.

## Testing Guidelines

### Writing Tests

- Add tests for all new features
- Update existing tests when modifying behavior
- Test both success and error cases
- Include edge cases (empty input, special characters, etc.)

### Test Structure

```python
def test_new_feature(self):
    """Test description"""
    # Arrange
    test_input = "test data"

    # Act
    result = run_command(['--flag', test_input])

    # Assert
    self.test(
        "Feature works correctly",
        expected_value in result,
        "Error details if failed"
    )
```

### Running Tests

```bash
# Run all tests
python3 tests/test_v1_2_0.py

# Tests should output:
# ✓ PASS - Test name
# ✗ FAIL - Test name (if any fail)
```

## Commit Message Format

Use conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `style:` Formatting changes
- `chore:` Maintenance tasks

Examples:

```text
feat: Add support for MOD- Jira prefix
fix: Resolve path validation issue with spaces
docs: Update README with batch upload examples
test: Add tests for duplicate file detection
```

## Documentation

Update relevant documentation when making changes:

- **[README.md](README.md)** - User-facing features
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Feature roadmap
- **[docs/TESTING.md](docs/TESTING.md)** - Testing documentation

## Development Workflow

### Adding a New Jira Prefix

Example: Add support for `ENG-` prefix

1. Update `validate_jira_id()` in `gtlogs-helper.py`
2. Add `ENG` to regex patterns
3. Update error messages
4. Update README.md examples
5. Add tests for new prefix
6. Run all tests
7. Commit with message: `feat: Add support for ENG- Jira prefix`

### Adding a New CLI Flag

Example: Add `--dry-run` flag

1. Add argument to parser in `main()`
2. Implement logic in execution flow
3. Update README.md "Command Reference" section
4. Add tests for new flag
5. Run all tests
6. Commit with message: `feat: Add --dry-run flag for preview mode`

## Release Process

For maintainers only:

1. Update version in script
2. Update ROADMAP.md with completed features
3. Update TESTING.md with test results
4. Create git tag: `git tag v1.x.x`
5. Push tag: `git push origin v1.x.x`
6. Create GitHub release with changelog

## Questions?

For questions or assistance:

- Open an issue on GitHub
- Contact: <marko.trapani@redis.com>

## License

By contributing, you agree that your contributions will be licensed
under the MIT License.
