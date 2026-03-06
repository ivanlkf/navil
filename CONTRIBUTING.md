# Contributing to Navil

Thank you for your interest in contributing to Navil! This document explains how to get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/ivanlkf/navil.git
cd navil

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

We use [mypy](https://mypy-lang.org/) for type checking:

```bash
mypy navil
```

## Testing

Run the full test suite with:

```bash
pytest
```

For coverage:

```bash
pytest --cov=navil --cov-report=html
```

All new code should include tests. We target 80%+ coverage.

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` -- A new feature
- `fix:` -- A bug fix
- `docs:` -- Documentation changes
- `test:` -- Adding or updating tests
- `ci:` -- CI/CD changes
- `chore:` -- Maintenance tasks
- `refactor:` -- Code changes that neither fix bugs nor add features

Examples:

```
feat: add SBOM generation for MCP server dependencies
fix: handle missing authentication field in scanner
docs: update quick start with credential rotation example
test: add policy engine rate-limiting edge cases
```

## Pull Requests

1. Fork the repository and create a branch from `main`
2. Make your changes and add tests
3. Ensure all checks pass (`ruff check .`, `mypy navil`, `pytest`)
4. Submit a pull request with a clear description

## Reporting Issues

Open an issue at [github.com/ivanlkf/navil/issues](https://github.com/ivanlkf/navil/issues) with:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
