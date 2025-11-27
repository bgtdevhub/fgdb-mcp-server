# Test Suite for FGDB MCP Server

**Version**: 0.1.0

## Overview

This test suite provides comprehensive coverage for the FGDB MCP Server, including:
- **fgdb_toolserver.py**: All MCP endpoint functions
- **gdb_ops/gdb_tools.py**: Business logic layer with safety confirmation
- **gdb_ops/gdb.py**: Backend operations and service classes
- **utils/safety.py**: SafetyManager and risk evaluation
- **utils/config.py**: Configuration parsing and management
- **utils/validation.py**: Input validation (with property-based tests)
- **dtos/requestobjects.py**: Data Transfer Objects

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and fake implementations
├── test_fgdb_toolserver.py          # Tests for MCP endpoints
├── test_gdb_tools.py                # Tests for GDBTools and command execution
├── test_gdb.py                      # Tests for backend and service classes
├── test_safety.py                   # Unit tests for SafetyManager
├── test_dtos.py                     # Unit tests for DTOs (Connection, OperationResult)
├── test_config.py                   # Unit tests for configuration parsing
├── test_validation_property.py      # Property-based tests using Hypothesis
└── test_integration_serialization.py # Integration tests for serialization
```

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
# Using pytest-cov (matches pyproject.toml configuration)
pytest --cov=fgdb_toolserver --cov=gdb_ops --cov=utils --cov-report=html --cov-report=term

# Or use coverage configuration from pyproject.toml
pytest --cov --cov-report=html --cov-report=term
```

### Run by Test Type

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Property-based tests (Hypothesis)
pytest tests/test_validation_property.py
```

### Run Specific Test File

```bash
pytest tests/test_fgdb_toolserver.py
```

### Run Specific Test Class

```bash
pytest tests/test_fgdb_toolserver.py::TestSetDatabaseConnection
```

### Run Specific Test

```bash
pytest tests/test_fgdb_toolserver.py::TestSetDatabaseConnection::test_set_database_connection_success
```

## Test Fixtures

The test suite uses several fixtures defined in `conftest.py`:

- **fake_backend**: Fake implementation of `GDBBackendProtocol`
- **fake_safety_manager**: `SafetyManager` instance for testing
- **fake_executor**: `SafetyCommandExecutor` instance
- **fake_tools**: `GDBTools` instance with fake dependencies
- **mock_server**: Mock `FGDBMCPServer` instance
- **mock_server_config**: Mock `ServerConfig` instance
- **sample_connection**: Sample `Connection` object
- **sample_operation_result_success**: Sample successful `OperationResult` object
- **sample_operation_result_confirmation**: Sample `OperationResult` requiring confirmation
- **sample_operation_result_error**: Sample failed `OperationResult` object
- **sample_pending_operation**: Sample `PendingOperation` object

## Coverage Target

The test suite aims for **≥80% coverage** for:
- `fgdb_toolserver.py`
- `gdb_ops/` (all modules)
- `utils/` (relevant modules)

## Test Strategy

1. **Unit Tests**: Isolated tests for individual components
   - `test_safety.py`: SafetyManager, RiskLevel, PendingOperation
   - `test_dtos.py`: Connection, OperationResult serialization
   - `test_config.py`: ServerConfig and environment variable parsing

2. **Property-Based Tests**: Using Hypothesis for validation
   - `test_validation_property.py`: Comprehensive property-based tests for `validate_where_clause` and `validate_limit`
   - Tests edge cases, boundary conditions, and invalid inputs automatically

3. **Integration Tests**: Component interaction testing
   - `test_integration_serialization.py`: JSON serialization of responses and DTOs
   - `test_fgdb_toolserver.py`: End-to-end endpoint testing
   - `test_gdb_tools.py`: Business logic with fake backend

4. **Mocking**: Heavy use of `unittest.mock` to isolate units
   - All ArcPy operations are mocked
   - `FakeGDBBackend` implements the protocol without ArcPy

5. **Protocol Testing**: Tests verify protocol compliance
   - Fake implementations test protocol interfaces
   - Dependency injection enables testing flexibility

## Test Markers

Tests are categorized using pytest markers:

- **`@pytest.mark.unit`**: Unit tests for individual components
- **`@pytest.mark.integration`**: Integration tests for component interactions

Run tests by marker:
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
```

## Notes

- Tests do not require ArcPy to be installed
- All ArcPy operations are mocked
- The fake backend provides realistic behavior for testing
- Safety confirmation flow is fully tested
- Property-based tests use Hypothesis for comprehensive validation testing
- All DTOs are tested for proper serialization/deserialization

