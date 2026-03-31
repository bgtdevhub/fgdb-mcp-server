from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TYPE_CHECKING
import os

try:
    import arcpy  # type: ignore
    ARCPY_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    ARCPY_AVAILABLE = False

if TYPE_CHECKING:
    # Type hints only - arcpy may not be available at runtime
    from arcpy import Field  # type: ignore

from utils.validation import validate_dataset, validate_where_clause, validate_limit


@runtime_checkable
class GDBBackendProtocol(Protocol):
    """Protocol defining the interface for geodatabase backend implementations.
    
    This protocol uses structural typing (duck typing), meaning any class that
    implements all the required methods with compatible signatures automatically
    satisfies this protocol. No explicit inheritance or declaration is needed.
    
    Example:
        FileGDBBackend automatically implements this protocol because it has
        all the required methods. You can verify this with:
        
        >>> backend = FileGDBBackend("path/to/gdb")
        >>> isinstance(backend, GDBBackendProtocol)  # True (with @runtime_checkable)
    """
    
    def list_all_feature_classes(self) -> List[str]:
        """List all feature classes in the geodatabase."""
        ...
    
    def describe(self, dataset: str) -> Dict[str, Any]:
        """Get metadata and schema information for a dataset."""
        ...
    
    def select(self, dataset: str, where: Any = None, fields: Any = None, limit: int = 50000) -> Dict[str, Any]:
        """Query records from a dataset with optional filtering and field selection.
        
        Args:
            dataset: Name of the dataset to query
            where: Optional WHERE clause for filtering
            fields: Optional list of field names to return (defaults to empty list for all fields)
            limit: Maximum number of records to return (default: 50000)
        """
        ...
    
    def count(self, dataset: str, where: Optional[str] = None) -> int:
        """Count records in a dataset, optionally filtered by WHERE clause."""
        ...
    
    def insert(self, dataset: str, rows: int, fields: List[str], values: List[str]) -> int:
        """Insert records into a dataset."""
        ...
    
    def update(self, dataset: str, updates: Dict[str, Any], where: Optional[str] = None) -> int:
        """Update records in a dataset based on WHERE clause."""
        ...
    
    def delete(self, dataset: str, where: Optional[str] = None) -> int:
        """Delete records from a dataset based on WHERE clause."""
        ...
    
    def add_field(self, dataset: str, name: str, field_type: str, length: Optional[int] = None) -> None:
        """Add a field to a dataset schema."""
        ...
    
    def delete_field(self, dataset: str, name: str) -> None:
        """Delete a field from a dataset schema."""
        ...

    def list_domains(self) -> List[Dict[str, Any]]:
        """List all domains in the geodatabase with their details."""
        ...

    def list_datasets_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        """List all feature classes and tables that have at least one field using the given domain."""
        ...


# ============================================================================
# Service Protocols for Dependency Injection
# ============================================================================

@runtime_checkable
class WorkspaceManagerProtocol(Protocol):
    """Protocol for workspace management."""
    def set_workspace(self, gdb_path: str) -> None:
        """Set ArcPy workspace to the given geodatabase path."""
        ...
    def ensure_arcpy_available(self) -> None:
        """Ensure ArcPy is available, raise if not."""
        ...


@runtime_checkable
class FieldSchemaServiceProtocol(Protocol):
    """Protocol for field schema operations."""
    def get_all_fields(self, dataset: str) -> List[Any]:
        """Get all fields for a dataset."""
        ...
    def get_field_metadata(self, dataset: str) -> Dict[str, Any]:
        """Get field metadata as dictionary."""
        ...
    def get_required_fields(self, dataset: str) -> List[str]:
        """Get list of required (non-nullable) fields."""
        ...
    def is_feature_class(self, dataset: str) -> bool:
        """Check if dataset is a feature class."""
        ...
    def validate_fields(self, dataset: str, fields: List[str]) -> List[str]:
        """Validate and return valid field names."""
        ...


@runtime_checkable
class ValueCoercionServiceProtocol(Protocol):
    """Protocol for value type coercion."""
    def coerce_value(self, field: Any, value: Any) -> Any:
        """Coerce a value to match field type."""
        ...
    def create_default_geometry(self) -> Any:
        """Create default geometry for feature classes."""
        ...
    def prepare_insert_values(
        self,
        fields: List[str],
        values: List[Any],
        field_metadata: Dict[str, Any],
        is_feature_class: bool,
        all_field_names: List[str]
    ) -> tuple[List[str], List[Any]]:
        """Prepare complete field list and coerced values for insert."""
        ...


@runtime_checkable
class CursorFactoryProtocol(Protocol):
    """Protocol for creating ArcPy cursors."""
    def create_search_cursor(
        self,
        dataset: str,
        fields: List[str],
        where: Optional[str] = None
    ) -> Any:
        """Create a search cursor."""
        ...
    def create_insert_cursor(
        self,
        dataset: str,
        fields: List[str]
    ) -> Any:
        """Create an insert cursor."""
        ...
    def create_update_cursor(
        self,
        dataset: str,
        fields: List[str],
        where: Optional[str] = None
    ) -> Any:
        """Create an update cursor."""
        ...


@runtime_checkable
class DataTransformerProtocol(Protocol):
    """Protocol for transforming ArcPy data."""
    def cursor_to_dicts(
        self,
        cursor: Any,
        field_names: List[str],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Convert cursor rows to list of dictionaries."""
        ...
    def fields_to_dict(self, fields: List[Any]) -> List[Dict[str, Any]]:
        """Convert field objects to dictionaries."""
        ...


# ============================================================================
# Service Implementations
# ============================================================================

class WorkspaceManager:
    """Manages ArcPy workspace setup and availability checks."""
    
    def ensure_arcpy_available(self) -> None:
        """Ensure ArcPy is available, raise if not."""
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for GDB operations in this build")
    
    def set_workspace(self, gdb_path: str) -> None:
        """Set ArcPy workspace to the given geodatabase path."""
        self.ensure_arcpy_available()
        arcpy.env.workspace = gdb_path


class FieldSchemaService:
    """Service for field schema operations."""
    
    def __init__(self, workspace_manager: WorkspaceManagerProtocol):
        self.workspace = workspace_manager
    
    def get_all_fields(self, dataset: str) -> List[Any]:
        """Get all fields for a dataset."""
        self.workspace.ensure_arcpy_available()
        return list(arcpy.ListFields(dataset) or [])
    
    def get_field_metadata(self, dataset: str) -> Dict[str, Any]:
        """Get field metadata as dictionary keyed by field name."""
        fields = self.get_all_fields(dataset)
        return {f.name: f for f in fields}
    
    def get_required_fields(self, dataset: str) -> List[str]:
        """Get list of required (non-nullable) fields, excluding OID."""
        fields = self.get_all_fields(dataset)
        return [
            f.name for f in fields
            if not getattr(f, "isNullable", True)
            and f.type != "OID"
        ]
    
    def is_feature_class(self, dataset: str) -> bool:
        """Check if dataset is a feature class."""
        self.workspace.ensure_arcpy_available()
        desc = arcpy.Describe(dataset)
        return hasattr(desc, "shapeType") and desc.shapeType is not None
    
    def validate_fields(self, dataset: str, fields: List[str]) -> List[str]:
        """Validate field names and return valid ones."""
        all_field_names = [f.name for f in self.get_all_fields(dataset)]
        valid_fields = set(fields).intersection(set(all_field_names))
        invalid = set(fields) - valid_fields
        if invalid:
            raise ValueError(
                f"Invalid fields: {invalid}. Available fields: {all_field_names}"
            )
        return list(valid_fields)


class ValueCoercionService:
    """Service for value type coercion and geometry creation."""
    
    def coerce_value(self, field: Any, value: Any) -> Any:
        """Coerce a value to match field type."""
        # Handle None/null values
        if value is None or (isinstance(value, str) and value.lower() in ["null", ""]):
            if not getattr(field, "isNullable", True):
                # Return default for required fields
                return self._get_default_value(field)
            return None
        
        # Handle geometry fields
        if field.type == "Geometry" or field.name == "Shape":
            if value is None or value == "":
                return self.create_default_geometry()
            return value
        
        # Handle numeric types
        if field.type in ["Integer", "SmallInteger", "OID"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return self._get_default_value(field)
        
        if field.type in ["Double", "Single", "Float"]:
            try:
                return float(value)
            except (ValueError, TypeError):
                return self._get_default_value(field)
        
        # Handle date types
        if field.type == "Date":
            return value  # ArcPy handles date conversion
        
        # Handle string types (default)
        return str(value)
    
    def _get_default_value(self, field: Any) -> Any:
        """Get default value for a field type."""
        if field.type in ["Integer", "SmallInteger", "OID"]:
            return 0
        elif field.type in ["Double", "Single", "Float"]:
            return 0.0
        elif field.type == "String":
            return ""
        else:
            return None
    
    def create_default_geometry(self) -> Any:
        """Create default dummy polygon geometry."""
        array = arcpy.Array([
            arcpy.Point(0.0, 0.0),
            arcpy.Point(0.001, 0.0),
            arcpy.Point(0.001, 0.001),
            arcpy.Point(0.0, 0.001),
            arcpy.Point(0.0, 0.0)  # Close polygon
        ])
        return arcpy.Polygon(array)
    
    def prepare_insert_values(
        self,
        fields: List[str],
        values: List[Any],
        field_metadata: Dict[str, Any],
        is_feature_class: bool,
        all_field_names: List[str]
    ) -> tuple[List[str], List[Any]]:
        """Prepare complete field list and coerced values for insert.
        
        Returns:
            Tuple of (complete_fields, coerced_values)
        """
        fields_dict = dict(zip(fields, values))
        complete_fields = []
        complete_values = []
        
        # Add Shape field first if feature class
        if is_feature_class and "Shape" in all_field_names:
            if "Shape" not in fields_dict:
                complete_fields.append("Shape")
                complete_values.append(None)  # Will be coerced later
            else:
                complete_fields.append("Shape")
                complete_values.append(fields_dict["Shape"])
        
        # Add user-specified fields (excluding Shape, already handled)
        for field_name in fields:
            if field_name == "Shape":
                continue
            if field_name in all_field_names:
                complete_fields.append(field_name)
                complete_values.append(fields_dict[field_name])
        
        # Add required fields that are missing
        for field_name in all_field_names:
            if field_name == "Shape":
                continue
            if field_name not in complete_fields:
                field = field_metadata.get(field_name)
                if field and not getattr(field, "isNullable", True):
                    complete_fields.append(field_name)
                    complete_values.append(self._get_default_value(field))
        
        # Coerce all values
        coerced_values = []
        for i, field_name in enumerate(complete_fields):
            field = field_metadata.get(field_name)
            if field:
                coerced_values.append(self.coerce_value(field, complete_values[i]))
            else:
                coerced_values.append(complete_values[i])
        
        return complete_fields, coerced_values


class CursorFactory:
    """Factory for creating ArcPy cursors."""
    
    def __init__(self, workspace_manager: WorkspaceManagerProtocol):
        self.workspace = workspace_manager
    
    def create_search_cursor(
        self,
        dataset: str,
        fields: List[str],
        where: Optional[str] = None
    ) -> Any:
        """Create a search cursor."""
        self.workspace.ensure_arcpy_available()
        return arcpy.da.SearchCursor(dataset, fields, where_clause=where)
    
    def create_insert_cursor(
        self,
        dataset: str,
        fields: List[str]
    ) -> Any:
        """Create an insert cursor."""
        self.workspace.ensure_arcpy_available()
        return arcpy.da.InsertCursor(dataset, fields)
    
    def create_update_cursor(
        self,
        dataset: str,
        fields: List[str],
        where: Optional[str] = None
    ) -> Any:
        """Create an update cursor."""
        self.workspace.ensure_arcpy_available()
        return arcpy.da.UpdateCursor(dataset, fields, where_clause=where)


class DataTransformer:
    """Transforms ArcPy data structures to Python dictionaries."""
    
    @staticmethod
    def cursor_to_dicts(
        cursor: Any,
        field_names: List[str],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Convert cursor rows to list of dictionaries."""
        result = []
        count = 0
        for row in cursor:
            if limit and count >= limit:
                break
            result.append(dict(zip(field_names, row)))
            count += 1
        return result
    
    @staticmethod
    def fields_to_dict(fields: List[Any]) -> List[Dict[str, Any]]:
        """Convert field objects to dictionaries."""
        return [
            {
                "name": f.name,
                "type": f.type,
                "length": getattr(f, "length", None),
                "nullable": getattr(f, "isNullable", None),
            }
            for f in fields
        ]


# ============================================================================
# Refactored FileGDBBackend (Facade)
# ============================================================================

@dataclass
class FileGDBBackend:
    """File Geodatabase backend implementation.
    
    Acts as a facade, orchestrating specialized services for different concerns.
    Uses dependency injection for all services to enable testing and flexibility.
    """
    gdb_path: str
    workspace_manager: Optional[WorkspaceManagerProtocol] = field(default=None, init=False)
    field_schema_service: Optional[FieldSchemaServiceProtocol] = field(default=None, init=False)
    value_coercion_service: Optional[ValueCoercionServiceProtocol] = field(default=None, init=False)
    cursor_factory: Optional[CursorFactoryProtocol] = field(default=None, init=False)
    data_transformer: Optional[DataTransformerProtocol] = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize default services if not provided."""
        # Check ArcPy availability (matching original __init__ behavior)
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for GDB operations in this build")
        
        # Initialize default services if not provided
        if self.workspace_manager is None:
            self.workspace_manager = WorkspaceManager()
        if self.field_schema_service is None:
            self.field_schema_service = FieldSchemaService(self.workspace_manager)
        if self.value_coercion_service is None:
            self.value_coercion_service = ValueCoercionService()
        if self.cursor_factory is None:
            self.cursor_factory = CursorFactory(self.workspace_manager)
        if self.data_transformer is None:
            self.data_transformer = DataTransformer()
    
    def _set_workspace(self) -> None:
        """Set workspace for current operation."""
        self.workspace_manager.set_workspace(self.gdb_path)
    
    def list_all_feature_classes(self) -> List[str]:
        """List all feature classes in the geodatabase (FGDB or SDE)."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        walk = arcpy.da.Walk(self.gdb_path, datatype="FeatureClass")
        fc_list = [
            os.path.join(root, feature_class)
            for root, data_sets, feature_classes in walk
            for feature_class in feature_classes
        ]
        # Workspace-agnostic: relative path from workspace root (works for .gdb and .sde)
        _seps = "\\/"  # support both Windows and Unix, and mocked os
        workspace_root = self.gdb_path.rstrip(_seps)
        result = []
        for full_path in fc_list or []:
            if full_path.startswith(workspace_root):
                rel = full_path[len(workspace_root) :].lstrip(_seps)
                if rel:
                    result.append(rel)
            else:
                result.append(full_path)
        return result

    def list_domains(self) -> List[Dict[str, Any]]:
        """List all domains in the geodatabase with name, type, and values or range."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        domains = arcpy.da.ListDomains(self.gdb_path)
        result = []
        for domain in domains or []:
            d: Dict[str, Any] = {
                "name": domain.name,
                "domainType": domain.domainType,
            }
            if domain.domainType == "CodedValue":
                d["codedValues"] = [
                    {"value": val, "description": desc}
                    for val, desc in (domain.codedValues or {}).items()
                ]
            elif domain.domainType == "Range":
                r = domain.range or [None, None]
                d["range"] = {"min": r[0], "max": r[1]}
            result.append(d)
        return result

    def list_datasets_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        """List all feature classes and tables (including inside feature datasets) that have at least one field using the given domain."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        result: List[Dict[str, Any]] = []
        candidates = list(arcpy.ListFeatureClasses() or []) + list(arcpy.ListTables() or [])
        for ds_path in candidates:
            fields = list(arcpy.ListFields(ds_path) or [])
            matching = [f.name for f in fields if getattr(f, "domain", None) == domain_name]
            if matching:
                result.append({"dataset": ds_path, "fields": matching})
        for ds in arcpy.ListDatasets("", "Feature") or []:
            for fc in arcpy.ListFeatureClasses("", "", ds) or []:
                path = os.path.join(ds, fc)
                fields = list(arcpy.ListFields(path) or [])
                matching = [f.name for f in fields if getattr(f, "domain", None) == domain_name]
                if matching:
                    result.append({"dataset": path, "fields": matching})
        return result

    def describe(self, dataset: str) -> Dict[str, Any]:
        """Get metadata and schema information for a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        
        desc = arcpy.Describe(dataset)
        fields = self.field_schema_service.get_all_fields(dataset)
        
        return {
            "name": getattr(desc, "name", dataset),
            "datasetType": getattr(desc, "datasetType", None),
            "shapeType": getattr(desc, "shapeType", None),
            "spatialReference": getattr(
                getattr(desc, "spatialReference", None), "name", None
            ),
            "fields": self.data_transformer.fields_to_dict(fields),
        }
    
    def select(
        self,
        dataset: str,
        where: Optional[str] = None,
        fields: List[str] = [],
        limit: int = 50000
    ) -> Dict[str, Any]:
        """Query records from a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        validate_where_clause(where)
        validate_limit(limit)
        
        total_count = self.count(dataset)
        if total_count < limit:
            limit = total_count
        
        # Get field list
        all_fields = [f.name for f in self.field_schema_service.get_all_fields(dataset)]
        if fields:
            fields_list = self.field_schema_service.validate_fields(dataset, fields)
        else:
            fields_list = all_fields
        
        # Execute query
        with self.cursor_factory.create_search_cursor(
            dataset, fields_list, where
        ) as cursor:
            result = self.data_transformer.cursor_to_dicts(cursor, fields_list, limit)
        
        has_more = total_count > len(result)
        return {"data": result, "hasMore": has_more}
    
    def count(self, dataset: str, where: Optional[str] = None) -> int:
        """Count records in a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        validate_where_clause(where)
        return int(arcpy.management.GetCount(dataset)[0])
    
    def insert(
        self,
        dataset: str,
        rows: int,
        fields: List[str],
        values: List[str]
    ) -> int:
        """Insert records into a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        
        # Get field metadata
        all_fields = self.field_schema_service.get_all_fields(dataset)
        all_field_names = [f.name for f in all_fields if f.type != "OID"]
        field_metadata = self.field_schema_service.get_field_metadata(dataset)
        is_feature_class = self.field_schema_service.is_feature_class(dataset)
        
        # Prepare values
        complete_fields, coerced_values = self.value_coercion_service.prepare_insert_values(
            fields, values, field_metadata, is_feature_class, all_field_names
        )
        
        # Execute insert
        if set(complete_fields).intersection(set(all_field_names)):
            with self.cursor_factory.create_insert_cursor(dataset, complete_fields) as cursor:
                count = 0
                while rows > count:
                    cursor.insertRow(coerced_values)
                    count += 1
            return count
        return 0
    
    def update(
        self,
        dataset: str,
        updates: Dict[str, Any],
        where: Optional[str] = None
    ) -> int:
        """Update records in a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        validate_where_clause(where)
        
        fields = list(updates.keys())
        oid_field = arcpy.Describe(dataset).OIDFieldName
        
        with self.cursor_factory.create_update_cursor(
            dataset, fields + [oid_field], where
        ) as cursor:
            count = 0
            for row in cursor:
                for i, f in enumerate(fields):
                    row[i] = updates[f]
                cursor.updateRow(row)
                count += 1
        return count
    
    def delete(self, dataset: str, where: Optional[str] = None) -> int:
        """Delete records from a dataset."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        validate_where_clause(where)
        
        oid_field = arcpy.Describe(dataset).OIDFieldName
        with self.cursor_factory.create_update_cursor(
            dataset, [oid_field], where
        ) as cursor:
            count = 0
            for _ in cursor:
                cursor.deleteRow()
                count += 1
        return count
    
    def add_field(
        self,
        dataset: str,
        name: str,
        field_type: str,
        length: Optional[int] = None
    ) -> None:
        """Add a field to a dataset schema."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        arcpy.management.AddField(dataset, name, field_type, field_length=length)
    
    def delete_field(self, dataset: str, name: str) -> None:
        """Delete a field from a dataset schema."""
        self.workspace_manager.ensure_arcpy_available()
        self._set_workspace()
        validate_dataset(dataset, self.gdb_path)
        arcpy.management.DeleteField(dataset, name)
