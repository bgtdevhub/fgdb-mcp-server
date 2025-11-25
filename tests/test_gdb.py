"""Tests for gdb_ops/gdb.py backend and services."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from gdb_ops.gdb import (
    FileGDBBackend,
    WorkspaceManager,
    FieldSchemaService,
    ValueCoercionService,
    CursorFactory,
    DataTransformer,
    WorkspaceManagerProtocol,
    FieldSchemaServiceProtocol,
    ValueCoercionServiceProtocol,
    CursorFactoryProtocol,
    DataTransformerProtocol
)
from tests.conftest import FakeGDBBackend


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_set_workspace(self, mock_arcpy):
        """Test setting workspace."""
        manager = WorkspaceManager()
        manager.set_workspace("C:\\test\\test.gdb")
        
        assert mock_arcpy.env.workspace == "C:\\test\\test.gdb"
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', False)
    def test_ensure_arcpy_available_raises_error(self):
        """Test ensure_arcpy_available raises error when ArcPy unavailable."""
        manager = WorkspaceManager()
        
        with pytest.raises(RuntimeError, match="ArcPy is required"):
            manager.ensure_arcpy_available()
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', False)
    def test_set_workspace_raises_error_when_arcpy_unavailable(self):
        """Test set_workspace raises error when ArcPy unavailable."""
        manager = WorkspaceManager()
        
        with pytest.raises(RuntimeError, match="ArcPy is required"):
            manager.set_workspace("C:\\test\\test.gdb")


class TestFieldSchemaService:
    """Tests for FieldSchemaService class."""
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_get_all_fields(self, mock_arcpy):
        """Test getting all fields."""
        mock_field1 = Mock()
        mock_field1.name = "Field1"
        mock_field2 = Mock()
        mock_field2.name = "Field2"
        mock_arcpy.ListFields.return_value = [mock_field1, mock_field2]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        service = FieldSchemaService(workspace_manager)
        fields = service.get_all_fields("TestDataset")
        
        assert len(fields) == 2
        assert fields[0].name == "Field1"
        assert fields[1].name == "Field2"
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_get_field_metadata(self, mock_arcpy):
        """Test getting field metadata."""
        mock_field = Mock()
        mock_field.name = "TestField"
        mock_arcpy.ListFields.return_value = [mock_field]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        service = FieldSchemaService(workspace_manager)
        metadata = service.get_field_metadata("TestDataset")
        
        assert "TestField" in metadata
        assert metadata["TestField"] == mock_field
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_is_feature_class(self, mock_arcpy):
        """Test checking if dataset is a feature class."""
        mock_desc = Mock()
        mock_desc.shapeType = "Polyline"
        mock_arcpy.Describe.return_value = mock_desc
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        service = FieldSchemaService(workspace_manager)
        is_fc = service.is_feature_class("TestDataset")
        
        assert is_fc is True
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_validate_fields(self, mock_arcpy):
        """Test field validation."""
        mock_field1 = Mock()
        mock_field1.name = "Field1"
        mock_field2 = Mock()
        mock_field2.name = "Field2"
        mock_arcpy.ListFields.return_value = [mock_field1, mock_field2]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        service = FieldSchemaService(workspace_manager)
        valid_fields = service.validate_fields("TestDataset", ["Field1", "Field2"])
        
        assert valid_fields == ["Field1", "Field2"]
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_validate_fields_invalid(self, mock_arcpy):
        """Test field validation with invalid fields."""
        mock_field = Mock()
        mock_field.name = "Field1"
        mock_arcpy.ListFields.return_value = [mock_field]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        service = FieldSchemaService(workspace_manager)
        
        with pytest.raises(ValueError, match="Invalid fields"):
            service.validate_fields("TestDataset", ["Field1", "InvalidField"])


class TestValueCoercionService:
    """Tests for ValueCoercionService class."""
    
    def test_coerce_value_integer(self):
        """Test coercing value to integer."""
        service = ValueCoercionService()
        
        mock_field = Mock()
        mock_field.type = "Integer"
        mock_field.isNullable = True
        
        result = service.coerce_value(mock_field, "42")
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_coerce_value_double(self):
        """Test coercing value to double."""
        service = ValueCoercionService()
        
        mock_field = Mock()
        mock_field.type = "Double"
        mock_field.isNullable = True
        
        result = service.coerce_value(mock_field, "3.14")
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_coerce_value_string(self):
        """Test coercing value to string."""
        service = ValueCoercionService()
        
        mock_field = Mock()
        mock_field.type = "String"
        mock_field.isNullable = True
        
        result = service.coerce_value(mock_field, 123)
        
        assert result == "123"
        assert isinstance(result, str)
    
    def test_coerce_value_null(self):
        """Test coercing null value."""
        service = ValueCoercionService()
        
        mock_field = Mock()
        mock_field.type = "String"
        mock_field.isNullable = True
        
        result = service.coerce_value(mock_field, None)
        
        assert result is None
    
    def test_coerce_value_required_field_default(self):
        """Test coercing null value for required field."""
        service = ValueCoercionService()
        
        mock_field = Mock()
        mock_field.type = "Integer"
        mock_field.isNullable = False
        
        result = service.coerce_value(mock_field, None)
        
        assert result == 0  # Default for required integer field
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_create_default_geometry(self, mock_arcpy):
        """Test creating default geometry."""
        service = ValueCoercionService()
        
        geometry = service.create_default_geometry()
        
        assert geometry is not None
        # Verify arcpy.Array and arcpy.Polygon were called
        assert mock_arcpy.Array.called
        assert mock_arcpy.Polygon.called
    
    def test_prepare_insert_values(self):
        """Test preparing insert values."""
        service = ValueCoercionService()
        
        mock_field1 = Mock()
        mock_field1.name = "Name"
        mock_field1.type = "String"
        mock_field1.isNullable = True
        
        mock_field2 = Mock()
        mock_field2.name = "ID"
        mock_field2.type = "Integer"
        mock_field2.isNullable = False
        
        field_metadata = {
            "Name": mock_field1,
            "ID": mock_field2
        }
        
        fields = ["Name"]
        values = ["Test"]
        all_field_names = ["Name", "ID"]
        
        complete_fields, coerced_values = service.prepare_insert_values(
            fields, values, field_metadata, False, all_field_names
        )
        
        assert "Name" in complete_fields
        assert "ID" in complete_fields  # Required field added
        assert len(complete_fields) == len(coerced_values)


class TestCursorFactory:
    """Tests for CursorFactory class."""
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_create_search_cursor(self, mock_arcpy):
        """Test creating search cursor."""
        mock_cursor = Mock()
        mock_arcpy.da.SearchCursor.return_value = mock_cursor
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        factory = CursorFactory(workspace_manager)
        cursor = factory.create_search_cursor("TestDataset", ["Field1"], "OBJECTID > 1")
        
        assert cursor == mock_cursor
        mock_arcpy.da.SearchCursor.assert_called_once_with(
            "TestDataset", ["Field1"], where_clause="OBJECTID > 1"
        )
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_create_insert_cursor(self, mock_arcpy):
        """Test creating insert cursor."""
        mock_cursor = Mock()
        mock_arcpy.da.InsertCursor.return_value = mock_cursor
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        factory = CursorFactory(workspace_manager)
        cursor = factory.create_insert_cursor("TestDataset", ["Field1"])
        
        assert cursor == mock_cursor
        mock_arcpy.da.InsertCursor.assert_called_once_with("TestDataset", ["Field1"])
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    def test_create_update_cursor(self, mock_arcpy):
        """Test creating update cursor."""
        mock_cursor = Mock()
        mock_arcpy.da.UpdateCursor.return_value = mock_cursor
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        
        factory = CursorFactory(workspace_manager)
        cursor = factory.create_update_cursor("TestDataset", ["Field1"], "OBJECTID = 1")
        
        assert cursor == mock_cursor
        mock_arcpy.da.UpdateCursor.assert_called_once_with(
            "TestDataset", ["Field1"], where_clause="OBJECTID = 1"
        )


class TestDataTransformer:
    """Tests for DataTransformer class."""
    
    def test_cursor_to_dicts(self):
        """Test converting cursor to dictionaries."""
        mock_cursor = [
            (1, "Value1"),
            (2, "Value2"),
        ]
        field_names = ["ID", "Name"]
        
        result = DataTransformer.cursor_to_dicts(mock_cursor, field_names)
        
        assert len(result) == 2
        assert result[0] == {"ID": 1, "Name": "Value1"}
        assert result[1] == {"ID": 2, "Name": "Value2"}
    
    def test_cursor_to_dicts_with_limit(self):
        """Test converting cursor with limit."""
        mock_cursor = [
            (1, "Value1"),
            (2, "Value2"),
            (3, "Value3"),
        ]
        field_names = ["ID", "Name"]
        
        result = DataTransformer.cursor_to_dicts(mock_cursor, field_names, limit=2)
        
        assert len(result) == 2
    
    def test_fields_to_dict(self):
        """Test converting fields to dictionaries."""
        mock_field1 = Mock()
        mock_field1.name = "Field1"
        mock_field1.type = "String"
        mock_field1.length = 50
        mock_field1.isNullable = True
        
        mock_field2 = Mock()
        mock_field2.name = "Field2"
        mock_field2.type = "Integer"
        mock_field2.length = None
        mock_field2.isNullable = False
        
        fields = [mock_field1, mock_field2]
        result = DataTransformer.fields_to_dict(fields)
        
        assert len(result) == 2
        assert result[0]["name"] == "Field1"
        assert result[0]["type"] == "String"
        assert result[1]["name"] == "Field2"
        assert result[1]["type"] == "Integer"


class TestFileGDBBackend:
    """Tests for FileGDBBackend class."""
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.os')
    def test_list_all_feature_classes(self, mock_os, mock_arcpy):
        """Test listing all feature classes."""
        # Mock os.path.join to return paths that include .gdb
        def mock_join(*args):
            return "\\".join(args)
        mock_os.path.join.side_effect = mock_join
        
        # Mock arcpy.da.Walk to return paths that will include .gdb when joined
        # The root should be the gdb path, and feature classes will be joined to it
        mock_arcpy.da.Walk.return_value = [
            ("C:\\test\\test.gdb", [], ["FC1", "FC2"])
        ]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        
        result = backend.list_all_feature_classes()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert "FC1" in result
        assert "FC2" in result
        workspace_manager.set_workspace.assert_called()
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    def test_describe(self, mock_validate, mock_arcpy):
        """Test describing a dataset."""
        mock_desc = Mock()
        mock_desc.name = "TestDataset"
        mock_desc.datasetType = "FeatureClass"
        mock_desc.shapeType = "Polyline"
        mock_desc.spatialReference = Mock()
        mock_desc.spatialReference.name = "SVY21"
        mock_arcpy.Describe.return_value = mock_desc
        
        mock_field = Mock()
        mock_field.name = "Field1"
        mock_field.type = "String"
        mock_field.length = 50
        mock_field.isNullable = True
        mock_arcpy.ListFields.return_value = [mock_field]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        field_schema_service = Mock(spec=FieldSchemaServiceProtocol)
        field_schema_service.get_all_fields.return_value = [mock_field]
        
        data_transformer = Mock(spec=DataTransformerProtocol)
        data_transformer.fields_to_dict.return_value = [
            {"name": "Field1", "type": "String", "length": 50, "nullable": True}
        ]
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        backend.field_schema_service = field_schema_service
        backend.data_transformer = data_transformer
        
        result = backend.describe("TestDataset")
        
        assert result["name"] == "TestDataset"
        assert result["datasetType"] == "FeatureClass"
        assert "fields" in result
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    @patch('gdb_ops.gdb.validate_where_clause')
    def test_count(self, mock_validate_where, mock_validate_dataset, mock_arcpy):
        """Test counting records."""
        mock_arcpy.management.GetCount.return_value = [42]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        
        result = backend.count("TestDataset")
        
        assert result == 42
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    @patch('gdb_ops.gdb.validate_where_clause')
    @patch('gdb_ops.gdb.validate_limit')
    def test_select(self, mock_validate_limit, mock_validate_where, mock_validate_dataset, mock_arcpy):
        """Test selecting records."""
        mock_cursor = [
            (1, "Value1"),
            (2, "Value2"),
        ]
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        field_schema_service = Mock(spec=FieldSchemaServiceProtocol)
        field_schema_service.get_all_fields.return_value = []
        field_schema_service.validate_fields.return_value = ["ID", "Name"]
        
        cursor_factory = Mock(spec=CursorFactoryProtocol)
        cursor_factory.create_search_cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        cursor_factory.create_search_cursor.return_value.__exit__ = Mock(return_value=None)
        
        data_transformer = Mock(spec=DataTransformerProtocol)
        data_transformer.cursor_to_dicts.return_value = [
            {"ID": 1, "Name": "Value1"},
            {"ID": 2, "Name": "Value2"},
        ]
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        backend.field_schema_service = field_schema_service
        backend.cursor_factory = cursor_factory
        backend.data_transformer = data_transformer
        
        result = backend.select("TestDataset", where=None, fields=["ID", "Name"], limit=10)
        
        assert "data" in result
        assert "hasMore" in result
        assert len(result["data"]) == 2
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    def test_insert(self, mock_validate, mock_arcpy):
        """Test inserting records."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.insertRow = Mock()
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        field_schema_service = Mock(spec=FieldSchemaServiceProtocol)
        mock_field = Mock()
        mock_field.name = "Name"
        mock_field.type = "String"
        field_schema_service.get_all_fields.return_value = [mock_field]
        field_schema_service.get_field_metadata.return_value = {"Name": mock_field}
        field_schema_service.is_feature_class.return_value = False
        
        value_coercion_service = Mock(spec=ValueCoercionServiceProtocol)
        value_coercion_service.prepare_insert_values.return_value = (
            ["Name"], ["Test"]
        )
        
        cursor_factory = Mock(spec=CursorFactoryProtocol)
        cursor_factory.create_insert_cursor.return_value = mock_cursor
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        backend.field_schema_service = field_schema_service
        backend.value_coercion_service = value_coercion_service
        backend.cursor_factory = cursor_factory
        
        result = backend.insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        
        assert result == 1
        mock_cursor.insertRow.assert_called_once()
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    @patch('gdb_ops.gdb.validate_where_clause')
    def test_update(self, mock_validate_where, mock_validate_dataset, mock_arcpy):
        """Test updating records."""
        # ArcPy update cursors return lists (mutable), not tuples
        mock_row = [None, 1]  # [Name value, OBJECTID]
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.__iter__ = Mock(return_value=iter([mock_row]))
        mock_cursor.updateRow = Mock()
        
        mock_desc = Mock()
        mock_desc.OIDFieldName = "OBJECTID"
        mock_arcpy.Describe.return_value = mock_desc
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        cursor_factory = Mock(spec=CursorFactoryProtocol)
        cursor_factory.create_update_cursor.return_value = mock_cursor
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        backend.cursor_factory = cursor_factory
        
        result = backend.update("TestDataset", updates={"Name": "Updated"}, where="OBJECTID = 1")
        
        assert result == 1
        assert mock_row[0] == "Updated"  # Verify the row was modified
        mock_cursor.updateRow.assert_called_once_with(mock_row)
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    @patch('gdb_ops.gdb.validate_where_clause')
    def test_delete(self, mock_validate_where, mock_validate_dataset, mock_arcpy):
        """Test deleting records."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.__iter__ = Mock(return_value=iter([(1,)]))
        mock_cursor.deleteRow = Mock()
        
        mock_desc = Mock()
        mock_desc.OIDFieldName = "OBJECTID"
        mock_arcpy.Describe.return_value = mock_desc
        
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        cursor_factory = Mock(spec=CursorFactoryProtocol)
        cursor_factory.create_update_cursor.return_value = mock_cursor
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        backend.cursor_factory = cursor_factory
        
        result = backend.delete("TestDataset", where="OBJECTID = 1")
        
        assert result == 1
        mock_cursor.deleteRow.assert_called_once()
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    def test_add_field(self, mock_validate, mock_arcpy):
        """Test adding a field."""
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        
        backend.add_field("TestDataset", "NewField", "TEXT", length=50)
        
        mock_arcpy.management.AddField.assert_called_once_with(
            "TestDataset", "NewField", "TEXT", field_length=50
        )
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', True)
    @patch('gdb_ops.gdb.arcpy')
    @patch('gdb_ops.gdb.validate_dataset')
    def test_delete_field(self, mock_validate, mock_arcpy):
        """Test deleting a field."""
        workspace_manager = Mock(spec=WorkspaceManagerProtocol)
        workspace_manager.ensure_arcpy_available = Mock()
        workspace_manager.set_workspace = Mock()
        
        backend = FileGDBBackend(gdb_path="C:\\test\\test.gdb")
        backend.workspace_manager = workspace_manager
        
        backend.delete_field("TestDataset", "OldField")
        
        mock_arcpy.management.DeleteField.assert_called_once_with("TestDataset", "OldField")
    
    @patch('gdb_ops.gdb.ARCPY_AVAILABLE', False)
    def test_backend_initialization_arcpy_unavailable(self):
        """Test backend initialization when ArcPy unavailable."""
        with pytest.raises(RuntimeError, match="ArcPy is required"):
            FileGDBBackend(gdb_path="C:\\test\\test.gdb")

