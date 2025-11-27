# Contributing to FGDB MCP Server

**Version**: 0.1.0

Thank you for your interest in contributing to the FGDB MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Areas for Contribution](#areas-for-contribution)
- [Project Structure](#project-structure)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/fgdb-mcp-server.git
   cd fgdb-mcp-server
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/bgtdevhub/fgdb-mcp-server.git
   ```

## Development Setup

### Prerequisites

- **Python**: >= 3.10
- **ArcGIS Pro**: Installed with ArcPy support (for full functionality)
- **Git**: For version control

### Setting Up the Development Environment

1. **Activate ArcGIS Pro conda environment**:
   ```powershell
   # Activate ArcGIS Pro conda environment
   & "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"
   conda activate arcgispro-py3
   ```

2. **Install the project in development mode**:
   ```bash
   pip install -e ".[test]"
   ```

3. **Verify the installation**:
   ```bash
   python -c "import arcpy; print(f'ArcPy version: {arcpy.__version__}')"
   ```

### Note on ArcPy

- ArcPy is only available in the ArcGIS Pro conda environment
- Tests use mocks and don't require ArcPy to be installed
- You can develop and test most features without ArcPy, but full functionality requires it

## Code Style Guidelines

### General Guidelines

- **Follow PEP 8**: Use the Python style guide
- **Type Hints**: Use type hints for all function parameters and return types
- **Docstrings**: Add docstrings to all public functions, classes, and modules
- **Line Length**: Keep lines to a maximum of 100 characters (soft limit)
- **Imports**: Organize imports using the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports

### Code Formatting

We use automated formatting and linting tools configured in `pyproject.toml`:

```bash
# Install dev dependencies (includes ruff, black, isort)
pip install -e ".[dev]"

# Format code with black
black .

# Sort imports with isort
isort .

# Lint code with ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code with ruff (alternative to black)
ruff format .
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any

def process_data(
    dataset: str,
    limit: Optional[int] = None,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Process dataset with optional parameters."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def list_feature_classes(connection_string: str) -> List[str]:
    """List all feature classes in the geodatabase.
    
    Args:
        connection_string: Full path to the file geodatabase
        
    Returns:
        List of feature class names
        
    Raises:
        DatabaseConnectionError: If connection fails
    """
    ...
```

### Logging

Add logging for important operations:

```python
import logging

logger = logging.getLogger(__name__)

def perform_operation():
    logger.info("Starting operation")
    try:
        # operation code
        logger.debug("Operation details")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

## Testing

### Test Requirements

- **Coverage Target**: Maintain ≥80% code coverage
- **Test Types**: Write unit tests, integration tests, and property-based tests as appropriate
- **Test Markers**: Use pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fgdb_toolserver --cov=gdb_ops --cov=utils --cov-report=html --cov-report=term

# Or use coverage configuration from pyproject.toml
pytest --cov --cov-report=html --cov-report=term

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run specific test file
pytest tests/test_gdb_tools.py
```

### Writing Tests

1. **Test Structure**: Follow the existing test patterns
2. **Fixtures**: Use fixtures from `conftest.py` when possible
3. **Mocking**: Mock ArcPy operations - tests should not require ArcPy
4. **Property-Based Tests**: Use Hypothesis for comprehensive validation testing

Example test:

```python
import pytest
from unittest.mock import Mock, patch

pytestmark = pytest.mark.unit

class TestMyFeature:
    """Tests for MyFeature."""
    
    def test_feature_behavior(self, fake_backend):
        """Test feature behavior."""
        # Test implementation
        assert result == expected
```

### Test Coverage

Before submitting a PR, ensure:
- New code has test coverage
- Coverage remains ≥80%
- All tests pass

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following the style guidelines
   - Add tests for new features
   - Update documentation as needed
   - Ensure all tests pass

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```
   
   Use clear, descriptive commit messages:
   - Start with a verb (Add, Fix, Update, Remove)
   - Keep the first line under 50 characters
   - Add more details in the body if needed

4. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Provide a detailed description of your changes
   - Reference any related issues
   - Include screenshots or examples if applicable

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows the style guidelines
- [ ] All tests pass (`pytest`)
- [ ] Test coverage is maintained (≥80%)
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with upstream/main
- [ ] No merge conflicts

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

## Areas for Contribution

We welcome contributions in the following areas:

### Features

- **New MCP Tools**: Additional tools for geodatabase operations
- **Spatial Query Enhancements**: Advanced spatial query capabilities
- **Performance Optimizations**: Query optimization and caching
- **Error Handling**: Improved error messages and recovery

### Testing

- **Unit Tests**: Additional test coverage
- **Integration Tests**: End-to-end testing scenarios
- **Property-Based Tests**: Hypothesis-based validation tests
- **Test Fixtures**: Reusable test fixtures

### Documentation

- **API Documentation**: Detailed API reference
- **Examples**: Usage examples and tutorials
- **Tutorials**: Step-by-step guides
- **Code Comments**: Inline documentation improvements

### Infrastructure

- **CI/CD**: Continuous integration improvements
- **Code Quality**: Linting and formatting tools
- **Dependencies**: Dependency updates and management

## Project Structure

```
fgdb-mcp-server/
├── fgdb_toolserver.py    # Main MCP server and tool definitions
├── fgdb_mcp_server/      # Package directory
│   └── __init__.py       # Package initialization and main entry point
├── gdb_ops/
│   ├── __init__.py
│   ├── gdb.py            # FileGDBBackend - ArcPy operations
│   └── gdb_tools.py      # GDBTools - Business logic layer
├── utils/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exception classes
│   ├── safety.py         # Safety manager for confirmation workflow
│   ├── utility.py        # Utility functions
│   └── validation.py     # Input validation utilities
├── dtos/
│   ├── __init__.py
│   └── requestobjects.py # Data transfer objects
├── tests/                # Test suite
│   ├── conftest.py       # Pytest configuration
│   ├── test_*.py         # Unit and integration tests
│   └── README.md         # Test documentation
├── pyproject.toml        # Project configuration and dependencies
├── LICENSE
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md       # This file
└── README.md
```

### Architecture

The server follows a layered architecture:

1. **MCP Layer** (`fgdb_toolserver.py`): Tool definitions and MCP protocol handling
2. **Business Logic Layer** (`gdb_tools.py`): Operation orchestration and safety checks
3. **Backend Layer** (`gdb.py`): ArcPy operations and geodatabase access
4. **Utility Layer** (`utils/`): Configuration, exceptions, and safety management

## Questions?

If you have questions or need help:

- Open an issue on GitHub
- Check existing issues and discussions
- Review the [README.md](README.md) for project overview

Thank you for contributing to FGDB MCP Server!

