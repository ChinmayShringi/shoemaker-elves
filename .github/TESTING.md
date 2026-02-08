# Testing Guide

This document provides instructions for running tests, linting, and type checking for the GPT Agent Orchestrator.

## Setup

Install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run tests with verbose output

```bash
pytest -v
```

### Run specific test file

```bash
pytest tests/test_config.py
```

### Run tests with coverage report

```bash
pytest --cov=src/shoemaker-elves --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run specific test class or function

```bash
pytest tests/test_transcript_parser.py::TestTranscriptParserBasics::test_parse_success_transcript
```

## Linting

Run ruff to check for style issues:

```bash
ruff check .
```

Auto-fix issues where possible:

```bash
ruff check --fix .
```

Check formatting:

```bash
ruff format --check .
```

Apply formatting:

```bash
ruff format .
```

## Type Checking

Run mypy for static type checking:

```bash
mypy src/shoemaker-elves
```

## Continuous Integration

The CI workflow runs automatically on:
- Push to `main` branch
- Pull requests to `main` branch
- Manual trigger via GitHub Actions UI

The CI performs:
1. **Test Matrix**: Runs tests on Ubuntu, macOS, and Windows with Python 3.10, 3.11, and 3.12
2. **Linting**: Runs ruff check and format verification
3. **Type Checking**: Runs mypy on the source code
4. **Package Build**: Verifies the package can be built correctly

## Test Coverage

Current coverage highlights:
- **transcript_parser.py**: 100%
- **state.py**: 92%
- **prompt_validator.py**: 90%
- **config.py**: 85%

View detailed coverage report:

```bash
pytest --cov=src/shoemaker-elves --cov-report=html
open htmlcov/index.html
```

## Writing New Tests

Tests are organized in the `tests/` directory with the following structure:

- `tests/test_*.py` - Test modules
- `tests/fixtures/` - Test data files

Test naming conventions:
- Test files: `test_<module_name>.py`
- Test classes: `Test<Feature>` (optional, for grouping)
- Test functions: `test_<specific_behavior>`

Example:

```python
def test_parse_transcript_with_errors(fixtures_dir):
    """Test parsing a transcript with errors."""
    transcript_path = fixtures_dir / "sample_transcript_with_errors.jsonl"
    result = parse_transcript(str(transcript_path))
    
    assert result["success"] is False
    assert len(result["errors"]) > 0
```

## Fixtures

Test fixtures are JSON Lines files in `tests/fixtures/`:
- `sample_transcript_success.jsonl` - Successful task execution
- `sample_transcript_with_errors.jsonl` - Task with errors
- `sample_transcript_complex.jsonl` - Multi-file operations

## Pre-commit Hooks (Optional)

You can set up pre-commit hooks to run tests automatically:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
echo "Running tests..."
pytest tests/test_config.py tests/test_state.py tests/test_transcript_parser.py -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
HOOK

chmod +x .git/hooks/pre-commit
```
