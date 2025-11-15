import logging
from typing import Annotated, Any, Dict, List, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from dtos.requestobjects import Connection
from gdb_ops.gdb_tools import create_tools_from_env, GDBTools
from utils.safety import SafetyManager
from utils.exceptions import (
    DatabaseConnectionError,
    OperationBlockedError,
    ValidationError,
    ArcPyError
)
from utils.config import get_config, ServerConfig

# Load configuration and setup logging
config = get_config()
config.setup_logging()

try:
    import arcpy  # type: ignore
    ARCPY_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    ARCPY_AVAILABLE = False
    logging.error("arcpy un-available")


class FGDBMCPServer:
    """Server class that manages all state and operations."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or get_config()
        self.safety = SafetyManager()
        self._tools: Optional[GDBTools] = None
        self._current_connection: Optional[str] = None
        self.arcpy_error = False
    
    def get_tools(self, connection_string: Optional[str] = None) -> GDBTools:
        """Get or initialize tools for the given connection string."""
        # If connection_string is provided and different, reinitialize
        if connection_string is not None and self._current_connection != connection_string:
            self._current_connection = connection_string
            self._tools = None  # Force reinitialization
        
        if self._tools is None:
            if self._current_connection is None:
                raise DatabaseConnectionError("No database connection established. Call set_database_connection first.")
            
            logging.info(f"Initializing tools for database: {self._current_connection}")
            try:
                conn = Connection()
                conn.connection_string = self._current_connection
                self._tools = create_tools_from_env(conn, self.safety)
                logging.info("Tools initialized successfully")
            except ArcPyError:
                self.arcpy_error = True
                raise
            except Exception as ex:
                logging.error(f"Database connection error: {ex}")
                self.arcpy_error = True
                raise DatabaseConnectionError(f"Failed to establish database connection: {ex}") from ex
        else:
            logging.debug("Using existing tools instance")
        
        if self._tools is None:
            logging.error("Tools not initialized. Database connection may have failed.")
            raise DatabaseConnectionError("Tools not initialized. Database connection may have failed.")
        
        return self._tools


# Create server instance with configuration
server = FGDBMCPServer(config)
mcp = FastMCP("fgdb-mcp-server")


# Module-level functions that FastMCP can call - they access the server instance
@mcp.tool(description="Establishes a connection to the given FGDB path. Requires a full absolute path.")
def set_database_connection(
    gdb_path: Annotated[str, Field(description="Full absolute path to the file geodatabase", examples=["C:\\data\\mygeodatabase.gdb"])]
) -> Dict[str, str]:
    logging.info(f"Setting database connection string to: {gdb_path}")
    try:
        tools = server.get_tools(gdb_path)
        if tools:
            logging.info(f"Database connection established successfully: {gdb_path}")
            return {"status": "ok"}
    except DatabaseConnectionError as ex:
        logging.error(f"Failed to establish database connection: {ex}")
        if server.arcpy_error:
            logging.error("arcpy error")
        return {"status": "error", "message": str(ex)}
    except Exception as ex:
        logging.error(f"Unexpected error establishing connection: {ex}")
        return {"status": "error", "message": str(ex)}


@mcp.tool(description="Lists all feature classes available in the connected file geodatabase.")
def list_all_feature_classes() -> List[str]:
    logging.info("Listing all feature classes")
    try:
        result = server.get_tools().list_all_feature_classes()
        logging.info(f"Found {len(result)} feature classes")
        return result
    except Exception as ex:
        logging.error(f"Error listing feature classes: {ex}")
        raise


@mcp.tool(description="Returns metadata and schema information for a specified dataset (feature class or table).")
def describe(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to describe")]
) -> Dict[str, Any]:
    logging.info(f"Describing dataset: {dataset}")
    try:
        result = server.get_tools().describe(dataset)
        logging.info(f"Successfully described dataset: {dataset}")
        return result
    except Exception as ex:
        logging.error(f"Error describing dataset {dataset}: {ex}")
        raise


@mcp.tool(description="Returns the total number of records in a specified dataset.")
def count(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to count records from")]
) -> Dict[str, int]:
    logging.info(f"Counting records in dataset: {dataset}")
    try:
        count_result = server.get_tools().count(dataset)
        logging.info(f"Dataset {dataset} has {count_result} records")
        return {"count": count_result}
    except Exception as ex:
        logging.error(f"Error counting records in dataset {dataset}: {ex}")
        raise


@mcp.tool(description="Queries records from a dataset with optional filtering, field selection, and pagination support.")
def select(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to query")],
    where: Annotated[Optional[str], Field(default=None, description="SQL WHERE clause to filter records (e.g., 'OBJECTID > 100')")] = None,
    fields: Annotated[Optional[List[str]], Field(default=None, description="List of field names to return. If empty or None, returns all fields")] = None,
    limit: Annotated[int, Field(default=1000, description="Maximum number of records to return per page", ge=1)] = 1000,
    page: Annotated[int, Field(default=1, description="Page number for pagination (1-based)", ge=1)] = 1
):
    logging.info(f"Selecting from dataset: {dataset}, where: {where}, fields: {fields}, limit: {limit}, page: {page}")
    try:
        if fields is None:
            fields = []
        limit = limit if limit else server.config.max_select_limit
        start = (page - 1) * limit if page else 0
        end = start + limit
        if start > 0:
            limit = end
        result = server.get_tools().select(dataset, where, fields, limit)
        data_count = len(result["data"][start:end])
        logging.info(f"Selected {data_count} records from dataset {dataset} (has_more: {result['hasMore']})")
        return {
            "data": result["data"][start:end],
            "limit": limit,
            "has_more": result["hasMore"]
        }
    except Exception as ex:
        logging.error(f"Error selecting from dataset {dataset}: {ex}")
        raise


@mcp.tool(description="Deletes records from a dataset based on a WHERE clause. May require confirmation for high-risk operations.")
def delete(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to delete records from")],
    where: Annotated[str, Field(description="SQL WHERE clause to specify which records to delete (e.g., 'OBJECTID = 1')")]
) -> Dict[str, Any]:
    logging.info(f"Delete operation requested for dataset: {dataset}, where: {where}")
    result = server.get_tools().delete(dataset, where)
    
    if result.requires_confirmation:
        logging.warning(f"Delete operation requires confirmation for dataset: {dataset}, token: {result.confirmation_token}")
        return {
            "status": "confirmation_required",
            "confirmation_token": result.confirmation_token,
            "endpoint": "delete",
            "message": "This is a high-risk operation. Please confirm using the confirm_operation endpoint."
        }
    
    if not result.success:
        logging.error(f"Delete operation failed for dataset {dataset}: {result.error}")
        raise OperationBlockedError(result.error or "Operation blocked")
    
    logging.info(f"Successfully deleted {result.data} records from dataset: {dataset}")
    return {"status": "ok", "deleted": result.data}


@mcp.tool(description="Inserts new records into a dataset. May require confirmation for medium-risk operations.")
def insert(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to insert records into")],
    rows: Annotated[int, Field(description="Number of rows to insert", ge=1)],
    fields: Annotated[List[str], Field(description="List of field names corresponding to the values to insert")],
    values: Annotated[List[str], Field(description="List of values to insert. Values should match the order and count of fields")]
) -> Dict[str, Any]:
    if rows is None:
        logging.error("Insert operation failed: rows parameter is required")
        raise ValidationError("rows parameter is required")
    rows = int(rows) if not isinstance(rows, int) else rows
    logging.info(f"Insert operation requested for dataset: {dataset}, rows: {rows}, fields: {fields}")
    result = server.get_tools().insert(dataset, rows, fields, values)
    
    if result.requires_confirmation:
        logging.warning(f"Insert operation requires confirmation for dataset: {dataset}, token: {result.confirmation_token}")
        return {
            "status": "confirmation_required",
            "confirmation_token": result.confirmation_token,
            "endpoint": "insert",
            "message": "This operation requires confirmation. Please confirm using the confirm_operation endpoint."
        }
    
    if not result.success:
        logging.error(f"Insert operation failed for dataset {dataset}: {result.error}")
        raise OperationBlockedError(result.error or "Operation blocked")
    
    logging.info(f"Successfully inserted {result.data} rows into dataset: {dataset}")
    return {"status": "ok", "inserted": result.data}


@mcp.tool(description="Updates existing records in a dataset based on WHERE clause. May require confirmation for medium-risk operations.")
def update(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to update records in")],
    where: Annotated[str, Field(description="SQL WHERE clause to specify which records to update (e.g., 'OBJECTID = 1')")],
    updates: Annotated[Dict[str, Any], Field(description="Dictionary of field names and their new values to update")]
) -> Dict[str, Any]:
    if updates is None:
        logging.error("Update operation failed: updates parameter is required")
        raise ValidationError("updates parameter is required")
    
    logging.info(f"Update operation requested for dataset: {dataset}, where: {where}, updates: {updates}")
    result = server.get_tools().update(dataset, updates, where)
    
    if result.requires_confirmation:
        logging.warning(f"Update operation requires confirmation for dataset: {dataset}, token: {result.confirmation_token}")
        return {
            "status": "confirmation_required",
            "confirmation_token": result.confirmation_token,
            "endpoint": "update",
            "message": "This operation requires confirmation. Please confirm using the confirm_operation endpoint."
        }
    
    if not result.success:
        logging.error(f"Update operation failed for dataset {dataset}: {result.error}")
        raise OperationBlockedError(result.error or "Operation blocked")
    
    logging.info(f"Successfully updated {result.data} records in dataset: {dataset}")
    return {"status": "ok", "updated": result.data}


@mcp.tool(description="Adds a new field to a dataset schema. May require confirmation for medium-risk operations.")
def add_field(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to add the field to")],
    name: Annotated[str, Field(description="Name of the new field to add")],
    field_type: Annotated[str, Field(description="Data type of the field (e.g., 'TEXT','SHORT', 'INTEGER', 'DOUBLE', 'DATE')")],
    length: Annotated[Optional[int], Field(default=None, description="Length for text fields (required for TEXT fields)", ge=1)] = None
) -> Dict[str, Any]:
    if name is None or field_type is None:
        logging.error("Add field operation failed: name and field_type are required")
        raise ValidationError("name and field_type are required")
    
    logging.info(f"Add field operation requested for dataset: {dataset}, field: {name}, type: {field_type}, length: {length}")
    result = server.get_tools().add_field(dataset, name, field_type, length)
    
    if result.requires_confirmation:
        logging.warning(f"Add field operation requires confirmation for dataset: {dataset}, token: {result.confirmation_token}")
        return {
            "status": "confirmation_required",
            "confirmation_token": result.confirmation_token,
            "endpoint": "add_field",
            "message": "This operation requires confirmation. Please confirm using the confirm_operation endpoint."
        }
    
    if not result.success:
        logging.error(f"Add field operation failed for dataset {dataset}, field {name}: {result.error}")
        raise OperationBlockedError(result.error or "Operation blocked")
    
    logging.info(f"Successfully added field {name} to dataset: {dataset}")
    return {"status": "ok"}


@mcp.tool(description="Deletes a field from a dataset schema. May require confirmation for high-risk operations.")
def delete_field(
    dataset: Annotated[str, Field(description="Name of the dataset (feature class or table) to delete the field from")],
    name: Annotated[str, Field(description="Name of the field to delete")]
) -> Dict[str, Any]:
    if name is None:
        logging.error("Delete field operation failed: name parameter is required")
        raise ValidationError("name parameter is required")
    
    logging.info(f"Delete field operation requested for dataset: {dataset}, field: {name}")
    result = server.get_tools().delete_field(dataset, name)
    
    if result.requires_confirmation:
        logging.warning(f"Delete field operation requires confirmation for dataset: {dataset}, token: {result.confirmation_token}")
        return {
            "status": "confirmation_required",
            "confirmation_token": result.confirmation_token,
            "endpoint": "delete_field",
            "message": "This is a high-risk operation. Please confirm using the confirm_operation endpoint."
        }
    
    if not result.success:
        logging.error(f"Delete field operation failed for dataset {dataset}, field {name}: {result.error}")
        raise OperationBlockedError(result.error or "Operation blocked")
    
    logging.info(f"Successfully deleted field {name} from dataset: {dataset}")
    return {"status": "ok"}


@mcp.tool(description="Confirms and executes a pending high-risk or medium-risk operation using a confirmation token received from the initial operation request.")
def confirm_operation(
    token: Annotated[str, Field(description="The confirmation token received from the initial operation request")],
    endpoint: Annotated[str, Field(description="The endpoint that was originally called (e.g., 'delete', 'insert', 'update')")],
    request: Annotated[Dict[str, Any], Field(description="The original request parameters as a dictionary")]
) -> Dict[str, Any]:
    logging.info(f"Confirm operation requested for endpoint: {endpoint}, token: {token}")
    tools = server.get_tools()
    
    # Validate token exists (without consuming it)
    pending = server.safety.validate_token(token)
    if pending is None:
        logging.warning(f"Invalid or expired confirmation token: {token}")
        return {"status": "error", "detail": "Invalid or expired confirmation token"}
    
    # Verify the endpoint matches
    if pending.endpoint != endpoint:
        logging.warning(f"Endpoint mismatch for token {token}. Expected {pending.endpoint}, got {endpoint}")
        return { 
            "status": "error",
            "detail": f"Endpoint mismatch. Expected {pending.endpoint}, got {endpoint}"
        }
    
    # Execute the operation based on endpoint (token will be consumed in the method)
    if endpoint == "delete":
        logging.info(f"Executing confirmed delete operation for dataset: {pending.parameters.get('dataset')}")
        result = tools.delete(
            dataset=pending.parameters["dataset"],
            where=pending.parameters.get("where"),
            confirmed_token=token
        )
        if not result.success:
            logging.error(f"Confirmed delete operation failed: {result.error}")
            return {"status": "error", "detail": result.error or "Operation failed"}
        logging.info(f"Confirmed delete operation successful: {result.data} records deleted")
        return {"status": "ok", "deleted": result.data}
    
    elif endpoint == "insert":
        logging.info(f"Executing confirmed insert operation for dataset: {pending.parameters.get('dataset')}")
        result = tools.insert(
            dataset=pending.parameters["dataset"],
            rows=pending.parameters["rows"],
            fields=pending.parameters.get("fields", []),
            values=pending.parameters.get("values", []),
            confirmed_token=token
        )
        if not result.success:
            logging.error(f"Confirmed insert operation failed: {result.error}")
            return {"status": "error", "detail": result.error or "Operation failed"}
        logging.info(f"Confirmed insert operation successful: {result.data} rows inserted")
        return {"status": "ok", "inserted": result.data}
    
    elif endpoint == "update":
        logging.info(f"Executing confirmed update operation for dataset: {pending.parameters.get('dataset')}")
        result = tools.update(
            dataset=pending.parameters["dataset"],
            updates=pending.parameters["updates"],
            where=pending.parameters.get("where"),
            confirmed_token=token
        )
        if not result.success:
            logging.error(f"Confirmed update operation failed: {result.error}")
            return {"status": "error", "detail": result.error or "Operation failed"}
        logging.info(f"Confirmed update operation successful: {result.data} records updated")
        return {"status": "ok", "updated": result.data}
    
    elif endpoint == "delete_field":
        logging.info(f"Executing confirmed delete_field operation for dataset: {pending.parameters.get('dataset')}, field: {pending.parameters.get('name')}")
        result = tools.delete_field(
            dataset=pending.parameters["dataset"],
            name=pending.parameters["name"],
            confirmed_token=token
        )
        if not result.success:
            logging.error(f"Confirmed delete_field operation failed: {result.error}")
            return {"status": "error", "detail": result.error or "Operation failed"}
        logging.info(f"Confirmed delete_field operation successful")
        return {"status": "ok"}
    
    elif endpoint == "add_field":
        logging.info(f"Executing confirmed add_field operation for dataset: {pending.parameters.get('dataset')}, field: {pending.parameters.get('name')}")
        result = tools.add_field(
            dataset=pending.parameters["dataset"],
            name=pending.parameters["name"],
            field_type=pending.parameters["field_type"],
            length=pending.parameters.get("length"),
            confirmed_token=token
        )
        if not result.success:
            logging.error(f"Confirmed add_field operation failed: {result.error}")
            return {"status": "error", "detail": result.error or "Operation failed"}
        logging.info(f"Confirmed add_field operation successful")
        return {"status": "ok"}
    
    else:
        logging.error(f"Unsupported endpoint for confirmation: {endpoint}")
        return {"status": "error", "detail": f"Unsupported endpoint: {endpoint}"}


def main():
    """Main entry point."""
    logging.info("Starting FGDB MCP Server")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
