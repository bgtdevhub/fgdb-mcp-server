# Test Suite for FGDB MCP Server

## Overview

This test suite provides comprehensive coverage for the FGDB MCP Server, including:
- **fgdb_toolserver.py**: All MCP endpoint functions
- **gdb_ops/gdb_tools.py**: Business logic layer with safety confirmation
- **gdb_ops/gdb.py**: Backend operations and service classes

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and fake implementations
├── test_fgdb_toolserver.py  # Tests for MCP endpoints
├── test_gdb_tools.py        # Tests for GDBTools and command execution
└── test_gdb.py              # Tests for backend and service classes
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
pytest --cov=fgdb_toolserver --cov=gdb_ops --cov=utils --cov-report=html --cov-report=term
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

## Coverage Target

The test suite aims for **≥80% coverage** for:
- `fgdb_toolserver.py`
- `gdb_ops/` (all modules)
- `utils/` (relevant modules)

## Test Strategy

1. **Mocking**: Heavy use of `unittest.mock` to isolate units
2. **Fake Backend**: `FakeGDBBackend` implements the protocol without ArcPy
3. **Protocol Testing**: Tests verify protocol compliance
4. **Integration Points**: Tests cover interaction between components

## Notes

- Tests do not require ArcPy to be installed
- All ArcPy operations are mocked
- The fake backend provides realistic behavior for testing
- Safety confirmation flow is fully tested

