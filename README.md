# FGDB MCP Server

A Model Context Protocol (MCP) server for interacting with Esri File Geodatabases (FGDB) through ArcPy. This server provides a comprehensive set of tools for querying, modifying, and managing geodatabase datasets via the MCP protocol.

**Version**: 0.1.0

See the [MCP Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information about the Model Context Protocol.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [MCP Client Configuration](#mcp-client-configuration)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- **Connection Management**: Establish and manage connections to File Geodatabases
- **Data Querying**: Query feature classes and tables with filtering, field selection, and pagination
- **Data Modification**: Insert, update, and delete records with safety confirmation workflows
- **Schema Management**: Add and delete fields from datasets
- **Metadata Operations**: List feature classes, describe datasets, and count records
- **Safety System**: Built-in confirmation workflow for high-risk operations
- **Comprehensive Logging**: Configurable logging with rotation support
- **Error Handling**: Standardized exception handling with custom error types

## Requirements

### System Requirements
- **Python**: >= 3.10
- **ArcGIS Pro**: Installed with ArcPy support (ArcPy is not installable via pip)
- **Operating System**: Windows (ArcPy is primarily available on Windows)

### Python Dependencies
- `mcp[cli] >= 1.21.0` - Model Context Protocol server framework
- `pydantic >= 2.0.0` - Data validation (installed as dependency of mcp)

### ArcPy Requirements
ArcPy is provided by ArcGIS Pro and is only available in the ArcGIS Pro conda environment. It cannot be installed via pip. See the [Installation](#installation) section for setup instructions.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fgdb-mcp-server
   ```

2. **Set up ArcPy environment**:
   
   Use the ArcGIS Pro conda environment directly:
   
   ```powershell
   # Activate ArcGIS Pro conda environment
   & "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"
   conda activate arcgispro-py3
   
   # Install your project dependencies
   # Note: Run your terminal with Administrator privileges
   pip install -e .
   ```

3. **Verify ArcPy availability**:
   ```python
   try:
       import arcpy
       print(f"ArcPy version: {arcpy.__version__}")
       print("ArcPy is available!")
   except ImportError:
       print("ArcPy is not available")
   ```

### Notes

- ArcPy is only available when ArcGIS Pro is installed
- The default ArcGIS Pro Python path is typically: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\`
- The code already handles ArcPy unavailability gracefully with try/except blocks

## MCP Client Configuration

To use this server with an MCP client, add the following configuration to your MCP client's configuration file (typically `mcp.json`):

```json
{
  "mcpServers": {
    "fgdb-mcp-server": {
      "type": "stdio",
      "command": "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe",
      "args": [
        "C:\\{path to}\\fgdb-mcp-server\\fgdb_toolserver.py"
      ]
    }
  }
}
```

### Configuration Notes

- **`command`**: Update this path to match your ArcGIS Pro Python executable location
- **`args`**: Update the path to point to your `fgdb_toolserver.py` file location (use full absolute path)
- **Windows paths**: Use double backslashes (`\\`) or forward slashes (`/`) in JSON paths

**Example with custom path:**
```json
{
  "mcpServers": {
    "fgdb-mcp-server": {
      "type": "stdio",
      "command": "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe",
      "args": [
        "C:\\your\\custom\\path\\to\\fgdb_toolserver.py"
      ]
    }
  }
}
```

## Usage

### Running the Server

The server runs as an MCP server using stdio transport, which allows it to be used with MCP-compatible clients.

### Example Workflow

1. **Connect to a geodatabase**:
   ```
   set_database_connection(gdb_path="C:\\data\\mygeodatabase.gdb")
   ```

2. **List available feature classes**:
   ```
   list_all_feature_classes()
   ```

3. **Query data**:
   ```
   select(dataset="MyFeatureClass", where="OBJECTID > 100", limit=100, page=1)
   ```

4. **Modify data** (with confirmation):
   ```
   # First attempt - returns confirmation token
   insert(dataset="MyFeatureClass", rows=1, fields=["Name"], values=["Test"])
   
   # Confirm the operation
   confirm_operation(token="...", endpoint="insert", request={...})
   ```

## Configuration

The server can be configured using environment variables:

### Environment Variables

#### Database Settings
- **`FGDB_MAX_SELECT_LIMIT`**: Maximum number of records to return in a single select query (default: `50000`)

#### Logging Settings
- **`FGDB_LOG_FILE`**: Path to the log file (default: `fgdb_server.log`)
- **`FGDB_LOG_LEVEL`**: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)
- **`FGDB_LOG_MAX_BYTES`**: Maximum log file size in bytes before rotation (default: `10485760` = 10MB)
- **`FGDB_LOG_BACKUP_COUNT`**: Number of backup log files to keep (default: `5`)

#### API Versioning
- **`FGDB_API_VERSION`**: Current API version (default: `v1`)
- **`FGDB_SUPPORTED_VERSIONS`**: Comma-separated list of supported API versions (default: `v1`)

#### Feature Flags
- **`FGDB_FEATURE_EXPERIMENTAL`**: Enable experimental features (default: `false`)

**Note**: Mutating operations (insert, update, delete, add_field, delete_field) do not use feature flags. They are controlled by the safety confirmation system, which requires explicit user confirmation for each operation.

### Example Configuration

```powershell
# Database settings
$env:FGDB_MAX_SELECT_LIMIT = "20000"

# Logging settings
$env:FGDB_LOG_LEVEL = "DEBUG"
$env:FGDB_LOG_FILE = "logs/fgdb_server.log"

# API versioning
$env:FGDB_API_VERSION = "v1"
$env:FGDB_SUPPORTED_VERSIONS = "v1"

# Feature flags - experimental features (optional)
$env:FGDB_FEATURE_EXPERIMENTAL = "false"
```

## Version Information

### Product Version
- **Current Release**: 0.1.0

### API Versioning

This server currently supports **API Version 1 (v1)**. All endpoints are part of the v1 API.

**Note**: Product version (0.1.0) and API version (v1) are independent:
- **Product version** tracks the software release (semantic versioning: major.minor.patch)
- **API version** tracks the API contract (v1, v2, etc.) and changes when breaking API changes occur

### API Version Information
- **Current API Version**: v1
- **Supported API Versions**: v1
- **Deprecation Policy**: Endpoints will be marked as deprecated at least one version before removal

### Version Configuration

The API version can be configured via environment variables:

```bash
# Set the default API version (default: v1)
$env:FGDB_API_VERSION = "v1"

# Specify supported API versions (comma-separated, default: v1)
$env:FGDB_SUPPORTED_VERSIONS = "v1"
```

## Feature Flags

The server supports feature flags for experimental features. Mutating operations (insert, update, delete, add_field, delete_field) do not use feature flags - they are controlled by the **safety confirmation system**, which requires explicit user confirmation for each operation.

### Available Feature Flags

| Feature | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Experimental | `FGDB_FEATURE_EXPERIMENTAL` | `false` | Enable experimental features |

### Why No Feature Flags for Mutating Operations?

Mutating operations are protected by the **safety confirmation system**:
- All mutating operations require explicit user confirmation via tokens
- The agent cannot bypass the confirmation requirement
- User confirmation is the authorization mechanism
- Feature flags would be redundant since confirmation already provides the necessary control

### Configuring Feature Flags

Feature flags can be set via environment variables:

```bash
# Enable experimental features (if any)
$env:FGDB_FEATURE_EXPERIMENTAL = "true"
```

## API Reference

The server provides 11 MCP tools for geodatabase operations:

### API Version 1 (v1) - Current

All endpoints below are part of the v1 API:

### Connection & Discovery

- **`set_database_connection`** (v1): Establishes a connection to a File Geodatabase using an absolute path
- **`list_all_feature_classes`** (v1): Lists all feature classes available in the connected geodatabase
- **`describe`** (v1): Returns metadata and schema information for a specified dataset (feature class or table)
- **`count`** (v1): Returns the total number of records in a specified dataset

### Data Querying

- **`select`** (v1): Queries records from a dataset with optional filtering, field selection, and pagination support
  - Supports SQL WHERE clauses
  - Field selection (returns all fields if not specified)
  - Pagination with configurable page size
  - Maximum limit protection (configurable, default: 50,000 records)

### Data Modification

- **`insert`** (v1): Inserts new records into a dataset (requires confirmation for medium-risk operations)
- **`update`** (v1): Updates existing records based on WHERE clause (requires confirmation for medium-risk operations)
- **`delete`** (v1): Deletes records from a dataset based on WHERE clause (requires confirmation for high-risk operations)

### Schema Management

- **`add_field`** (v1): Adds a new field to a dataset schema (requires confirmation for medium-risk operations)
- **`delete_field`** (v1): Deletes a field from a dataset schema (requires confirmation for high-risk operations)

### Safety & Confirmation

- **`confirm_operation`** (v1): Confirms and executes pending high-risk or medium-risk operations using a confirmation token

### Safety System

The server implements a safety system that requires confirmation for medium and high-risk operations:

- **Low Risk**: Operations proceed immediately (e.g., read operations)
- **Medium Risk**: Requires confirmation (e.g., insert, update, add_field)
- **High Risk**: Requires confirmation (e.g., delete, delete_field)
- **Extreme Risk**: Blocked entirely

When a confirmation is required, the operation returns a confirmation token that must be used with the `confirm_operation` tool to execute the operation.

### Error Handling

The server uses standardized exception handling:

- **`DatabaseConnectionError`**: Database connection issues
- **`OperationBlockedError`**: Operations blocked by safety checks
- **`ValidationError`**: Input validation failures
- **`ArcPyError`**: ArcPy-related errors
- **`ConfigurationError`**: Configuration errors

All errors are logged and returned with descriptive messages.

### Logging

The server provides comprehensive logging:

- **File Logging**: All operations are logged to `fgdb_server.log` (configurable)
- **Log Rotation**: Automatic log rotation when file size exceeds the configured limit
- **Console Logging**: Optional console output for development
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)

Logs include:
- Operation requests and parameters
- Success/failure status
- Error details
- Confirmation token generation
- Database connection events

## Contributing

We welcome contributions from the open source community! This project is designed to be extensible and maintainable.

### How to Contribute

1. **Fork the repository** and create a feature branch
2. **Follow the code style**:
   - Use type hints
   - Add docstrings to functions and classes
   - Follow PEP 8 style guidelines
   - Add logging for important operations
3. **Write tests** for new features (when test framework is added)
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description of changes

### Areas for Contribution

- **Additional Tools**: New MCP tools for geodatabase operations
- **Testing**: Unit tests, integration tests, and test fixtures
- **Documentation**: Examples, tutorials, and API documentation
- **Performance**: Query optimization and caching
- **Features**: 
  - Spatial query enhancements

### Code Structure

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
├── CONTRIBUTING.md
└── README.md
```

### Architecture

The server follows a layered architecture:

1. **MCP Layer** (`fgdb_toolserver.py`): Tool definitions and MCP protocol handling
2. **Business Logic Layer** (`gdb_tools.py`): Operation orchestration and safety checks
3. **Backend Layer** (`gdb.py`): ArcPy operations and geodatabase access
4. **Utility Layer** (`utils/`): Configuration, exceptions, and safety management

This separation of concerns makes the codebase maintainable and testable.

### Reporting Issues

Please report bugs, request features, or ask questions by opening an issue on GitHub. Include:
- Description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (Python version, ArcGIS Pro version, OS)

## License

This project is licensed under the MIT License.

Copyright (c) 2025 Boustead Geospatial Technologies

See the [LICENSE](LICENSE) file for the full license text.

## Support

For questions, issues, or contributions, please use the GitHub issue tracker.
