# Contributing to CmdChat

Thank you for your interest in contributing to CmdChat! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip and virtualenv

### Local Development

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/yourusername/cmd-chat.git
   cd cmd-chat
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**

   ```bash
   pip install -e '.[dev]'
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cmdchat --cov-report=html

# Run specific test file
pytest tests/test_crypto.py

# Run in parallel
pytest -n auto
```

### Code Formatting

We use **Black** for code formatting and **Ruff** for linting.

```bash
# Format code
black cmdchat tests

# Lint code
ruff check cmdchat tests

# Auto-fix linting issues
ruff check --fix cmdchat tests
```

### Type Checking

```bash
# Run mypy
mypy cmdchat
```

### Security Scanning

```bash
# Run Bandit
bandit -r cmdchat

# Check dependencies
safety check
```

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks
- `perf:` Performance improvements

**Example:**

```bash
git commit -m "feat: add support for custom encryption algorithms"
git commit -m "fix: resolve race condition in heartbeat loop"
git commit -m "docs: update installation instructions"
```

## Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run the test suite**

   ```bash
   pytest
   black cmdchat tests
   ruff check cmdchat tests
   mypy cmdchat
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass

## Code Quality Standards

### Code Coverage

- Aim for **95%+ code coverage**
- All new features must include tests
- Edge cases should be tested

### Code Style

- Follow **PEP 8** guidelines
- Maximum line length: **100 characters**
- Use type hints for all function signatures
- Write clear, descriptive docstrings

### Testing Guidelines

- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Test edge cases and error conditions

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Include examples for complex functionality

## Project Structure

```
cmd-chat/
├── cmdchat/              # Main package
│   ├── server/           # Server modules
│   ├── client/           # Client modules
│   ├── lib/              # Shared libraries
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── .github/              # GitHub Actions workflows
├── .devcontainer/        # Dev container configuration
└── docs/                 # Documentation
```

## Reporting Issues

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

## Feature Requests

For feature requests:

- Describe the problem you're trying to solve
- Explain your proposed solution
- Discuss alternatives you've considered
- Indicate if you're willing to implement it

## Questions?

- Open a discussion on GitHub
- Check existing issues and pull requests
- Review the documentation

Thank you for contributing to CmdChat! 🎉
