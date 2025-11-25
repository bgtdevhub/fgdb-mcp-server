"""Tests for fgdb_toolserver.py endpoints."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

from utils.exceptions import (
    DatabaseConnectionError,
    OperationBlockedError,
    ValidationError,
    ArcPyError
)
from dtos.requestobjects import OperationResult
from utils.safety import PendingOperation


class TestSetDatabaseConnection:
    """Tests for set_database_connection endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_set_database_connection_success(self, mock_server):
        """Test successful database connection."""
        from fgdb_toolserver import set_database_connection
        
        mock_tools = Mock()
        mock_server.get_tools.return_value = mock_tools
        
        result = set_database_connection("C:\\test\\test.gdb")
        
        assert result == {"status": "ok"}
        mock_server.get_tools.assert_called_once_with("C:\\test\\test.gdb")
    
    @patch('fgdb_toolserver.server')
    def test_set_database_connection_error(self, mock_server):
        """Test database connection error."""
        from fgdb_toolserver import set_database_connection
        
        mock_server.get_tools.side_effect = DatabaseConnectionError("Connection failed")
        
        result = set_database_connection("C:\\test\\test.gdb")
        
        assert result == {"status": "error", "message": "Connection failed"}
    
    @patch('fgdb_toolserver.server')
    def test_set_database_connection_arcpy_error(self, mock_server):
        """Test ArcPy error handling."""
        from fgdb_toolserver import set_database_connection
        
        mock_server.get_tools.side_effect = ArcPyError("ArcPy not available")
        mock_server.arcpy_error = True
        
        result = set_database_connection("C:\\test\\test.gdb")
        
        assert result == {"status": "error", "message": "ArcPy not available"}


class TestListAllFeatureClasses:
    """Tests for list_all_feature_classes endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_list_all_feature_classes_success(self, mock_server):
        """Test successful listing of feature classes."""
        from fgdb_toolserver import list_all_feature_classes
        
        mock_tools = Mock()
        mock_tools.list_all_feature_classes.return_value = ["FC1", "FC2"]
        mock_server.get_tools.return_value = mock_tools
        
        result = list_all_feature_classes()
        
        assert result == ["FC1", "FC2"]
        mock_tools.list_all_feature_classes.assert_called_once()
    
    @patch('fgdb_toolserver.server')
    def test_list_all_feature_classes_error(self, mock_server):
        """Test error handling in list_all_feature_classes."""
        from fgdb_toolserver import list_all_feature_classes
        
        mock_tools = Mock()
        mock_tools.list_all_feature_classes.side_effect = Exception("Test error")
        mock_server.get_tools.return_value = mock_tools
        
        with pytest.raises(Exception, match="Test error"):
            list_all_feature_classes()


class TestDescribe:
    """Tests for describe endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_describe_success(self, mock_server):
        """Test successful dataset description."""
        from fgdb_toolserver import describe
        
        expected_result = {
            "name": "TestDataset",
            "datasetType": "FeatureClass",
            "fields": []
        }
        
        mock_tools = Mock()
        mock_tools.describe.return_value = expected_result
        mock_server.get_tools.return_value = mock_tools
        
        result = describe("TestDataset")
        
        assert result == expected_result
        mock_tools.describe.assert_called_once_with("TestDataset")
    
    @patch('fgdb_toolserver.server')
    def test_describe_error(self, mock_server):
        """Test error handling in describe."""
        from fgdb_toolserver import describe
        
        mock_tools = Mock()
        mock_tools.describe.side_effect = ValueError("Dataset not found")
        mock_server.get_tools.return_value = mock_tools
        
        with pytest.raises(ValueError, match="Dataset not found"):
            describe("NonExistentDataset")


class TestCount:
    """Tests for count endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_count_success(self, mock_server):
        """Test successful record counting."""
        from fgdb_toolserver import count
        
        mock_tools = Mock()
        mock_tools.count.return_value = 42
        mock_server.get_tools.return_value = mock_tools
        
        result = count("TestDataset")
        
        assert result == {"count": 42}
        mock_tools.count.assert_called_once_with("TestDataset")
    
    @patch('fgdb_toolserver.server')
    def test_count_error(self, mock_server):
        """Test error handling in count."""
        from fgdb_toolserver import count
        
        mock_tools = Mock()
        mock_tools.count.side_effect = Exception("Count error")
        mock_server.get_tools.return_value = mock_tools
        
        with pytest.raises(Exception, match="Count error"):
            count("TestDataset")


class TestSelect:
    """Tests for select endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_select_success(self, mock_server):
        """Test successful record selection."""
        from fgdb_toolserver import select
        
        mock_tools = Mock()
        mock_tools.select.return_value = {
            "data": [{"id": 1}, {"id": 2}],
            "hasMore": False
        }
        mock_server.get_tools.return_value = mock_tools
        mock_server.config.max_select_limit = 50000
        
        result = select("TestDataset", where=None, fields=None, limit=1000, page=1)
        
        assert "data" in result
        assert "has_more" in result
        assert result["has_more"] is False
        mock_tools.select.assert_called_once()
    
    @patch('fgdb_toolserver.server')
    def test_select_with_pagination(self, mock_server):
        """Test select with pagination."""
        from fgdb_toolserver import select
        
        mock_tools = Mock()
        mock_tools.select.return_value = {
            "data": [{"id": i} for i in range(10)],
            "hasMore": True
        }
        mock_server.get_tools.return_value = mock_tools
        mock_server.config.max_select_limit = 50000
        
        result = select("TestDataset", where=None, fields=None, limit=5, page=2)
        
        assert "data" in result
        assert result["has_more"] is True
    
    @patch('fgdb_toolserver.server')
    def test_select_error(self, mock_server):
        """Test error handling in select."""
        from fgdb_toolserver import select
        
        mock_tools = Mock()
        mock_tools.select.side_effect = Exception("Select error")
        mock_server.get_tools.return_value = mock_tools
        mock_server.config.max_select_limit = 50000
        
        with pytest.raises(Exception, match="Select error"):
            select("TestDataset")


class TestInsert:
    """Tests for insert endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_insert_requires_confirmation(self, mock_server):
        """Test insert operation requiring confirmation."""
        from fgdb_toolserver import insert
        
        mock_tools = Mock()
        mock_tools.insert.return_value = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        
        assert result["status"] == "confirmation_required"
        assert result["confirmation_token"] == "test-token-123"
        assert result["endpoint"] == "insert"
    
    @patch('fgdb_toolserver.server')
    def test_insert_success(self, mock_server):
        """Test successful insert operation."""
        from fgdb_toolserver import insert
        
        mock_tools = Mock()
        mock_tools.insert.return_value = OperationResult(
            success=True,
            data=5
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        
        assert result["status"] == "ok"
        assert result["inserted"] == 5
    
    @patch('fgdb_toolserver.server')
    def test_insert_error(self, mock_server):
        """Test insert operation error."""
        from fgdb_toolserver import insert
        
        mock_tools = Mock()
        mock_tools.insert.return_value = OperationResult(
            success=False,
            error="Operation blocked"
        )
        mock_server.get_tools.return_value = mock_tools
        
        with pytest.raises(OperationBlockedError):
            insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
    
    @patch('fgdb_toolserver.server')
    def test_insert_validation_error(self, mock_server):
        """Test insert with missing rows parameter."""
        from fgdb_toolserver import insert
        
        with pytest.raises(ValidationError, match="rows parameter is required"):
            insert("TestDataset", rows=None, fields=["Name"], values=["Test"])


class TestUpdate:
    """Tests for update endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_update_requires_confirmation(self, mock_server):
        """Test update operation requiring confirmation."""
        from fgdb_toolserver import update
        
        mock_tools = Mock()
        mock_tools.update.return_value = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = update("TestDataset", where="OBJECTID = 1", updates={"Name": "Updated"})
        
        assert result["status"] == "confirmation_required"
        assert result["confirmation_token"] == "test-token-123"
    
    @patch('fgdb_toolserver.server')
    def test_update_success(self, mock_server):
        """Test successful update operation."""
        from fgdb_toolserver import update
        
        mock_tools = Mock()
        mock_tools.update.return_value = OperationResult(
            success=True,
            data=3
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = update("TestDataset", where="OBJECTID = 1", updates={"Name": "Updated"})
        
        assert result["status"] == "ok"
        assert result["updated"] == 3
    
    @patch('fgdb_toolserver.server')
    def test_update_validation_error(self, mock_server):
        """Test update with missing updates parameter."""
        from fgdb_toolserver import update
        
        with pytest.raises(ValidationError, match="updates parameter is required"):
            update("TestDataset", where="OBJECTID = 1", updates=None)


class TestDelete:
    """Tests for delete endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_delete_requires_confirmation(self, mock_server):
        """Test delete operation requiring confirmation."""
        from fgdb_toolserver import delete
        
        mock_tools = Mock()
        mock_tools.delete.return_value = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = delete("TestDataset", where="OBJECTID = 1")
        
        assert result["status"] == "confirmation_required"
        assert result["confirmation_token"] == "test-token-123"
        assert "high-risk" in result["message"].lower()
    
    @patch('fgdb_toolserver.server')
    def test_delete_success(self, mock_server):
        """Test successful delete operation."""
        from fgdb_toolserver import delete
        
        mock_tools = Mock()
        mock_tools.delete.return_value = OperationResult(
            success=True,
            data=2
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = delete("TestDataset", where="OBJECTID = 1")
        
        assert result["status"] == "ok"
        assert result["deleted"] == 2


class TestAddField:
    """Tests for add_field endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_add_field_requires_confirmation(self, mock_server):
        """Test add_field operation requiring confirmation."""
        from fgdb_toolserver import add_field
        
        mock_tools = Mock()
        mock_tools.add_field.return_value = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = add_field("TestDataset", name="NewField", field_type="TEXT", length=50)
        
        assert result["status"] == "confirmation_required"
        assert result["confirmation_token"] == "test-token-123"
    
    @patch('fgdb_toolserver.server')
    def test_add_field_success(self, mock_server):
        """Test successful add_field operation."""
        from fgdb_toolserver import add_field
        
        mock_tools = Mock()
        mock_tools.add_field.return_value = OperationResult(success=True)
        mock_server.get_tools.return_value = mock_tools
        
        result = add_field("TestDataset", name="NewField", field_type="TEXT", length=50)
        
        assert result["status"] == "ok"
    
    @patch('fgdb_toolserver.server')
    def test_add_field_validation_error(self, mock_server):
        """Test add_field with missing parameters."""
        from fgdb_toolserver import add_field
        
        with pytest.raises(ValidationError, match="name and field_type are required"):
            add_field("TestDataset", name=None, field_type="TEXT")


class TestDeleteField:
    """Tests for delete_field endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_delete_field_requires_confirmation(self, mock_server):
        """Test delete_field operation requiring confirmation."""
        from fgdb_toolserver import delete_field
        
        mock_tools = Mock()
        mock_tools.delete_field.return_value = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        mock_server.get_tools.return_value = mock_tools
        
        result = delete_field("TestDataset", name="OldField")
        
        assert result["status"] == "confirmation_required"
        assert result["confirmation_token"] == "test-token-123"
        assert "high-risk" in result["message"].lower()
    
    @patch('fgdb_toolserver.server')
    def test_delete_field_success(self, mock_server):
        """Test successful delete_field operation."""
        from fgdb_toolserver import delete_field
        
        mock_tools = Mock()
        mock_tools.delete_field.return_value = OperationResult(success=True)
        mock_server.get_tools.return_value = mock_tools
        
        result = delete_field("TestDataset", name="OldField")
        
        assert result["status"] == "ok"
    
    @patch('fgdb_toolserver.server')
    def test_delete_field_validation_error(self, mock_server):
        """Test delete_field with missing name parameter."""
        from fgdb_toolserver import delete_field
        
        with pytest.raises(ValidationError, match="name parameter is required"):
            delete_field("TestDataset", name=None)


class TestConfirmOperation:
    """Tests for confirm_operation endpoint."""
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_invalid_token(self, mock_server):
        """Test confirm_operation with invalid token."""
        from fgdb_toolserver import confirm_operation
        
        mock_server.get_tools.return_value = Mock()
        mock_server.safety.validate_token.return_value = None
        
        result = confirm_operation(
            token="invalid-token",
            endpoint="insert",
            request={}
        )
        
        assert result["status"] == "error"
        assert "Invalid or expired" in result["detail"]
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_endpoint_mismatch(self, mock_server):
        """Test confirm_operation with endpoint mismatch."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="insert",
            endpoint="insert",
            parameters={"dataset": "TestDataset", "rows": 1, "fields": [], "values": []},
            token="test-token"
        )
        
        mock_server.get_tools.return_value = Mock()
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="update",  # Mismatch
            request={}
        )
        
        assert result["status"] == "error"
        assert "Endpoint mismatch" in result["detail"]
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_insert_success(self, mock_server):
        """Test successful confirmed insert operation."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="insert",
            endpoint="insert",
            parameters={
                "dataset": "TestDataset",
                "rows": 1,
                "fields": ["Name"],
                "values": ["Test"]
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.insert.return_value = OperationResult(success=True, data=1)
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="insert",
            request={}
        )
        
        assert result["status"] == "ok"
        assert result["inserted"] == 1
        mock_tools.insert.assert_called_once()
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_update_success(self, mock_server):
        """Test successful confirmed update operation."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="update",
            endpoint="update",
            parameters={
                "dataset": "TestDataset",
                "updates": {"Name": "Updated"},
                "where": "OBJECTID = 1"
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.update.return_value = OperationResult(success=True, data=1)
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="update",
            request={}
        )
        
        assert result["status"] == "ok"
        assert result["updated"] == 1
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_delete_success(self, mock_server):
        """Test successful confirmed delete operation."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="delete",
            endpoint="delete",
            parameters={
                "dataset": "TestDataset",
                "where": "OBJECTID = 1"
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.delete.return_value = OperationResult(success=True, data=1)
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="delete",
            request={}
        )
        
        assert result["status"] == "ok"
        assert result["deleted"] == 1
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_add_field_success(self, mock_server):
        """Test successful confirmed add_field operation."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="add_field",
            endpoint="add_field",
            parameters={
                "dataset": "TestDataset",
                "name": "NewField",
                "field_type": "TEXT",
                "length": 50
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.add_field.return_value = OperationResult(success=True)
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="add_field",
            request={}
        )
        
        assert result["status"] == "ok"
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_delete_field_success(self, mock_server):
        """Test successful confirmed delete_field operation."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="delete_field",
            endpoint="delete_field",
            parameters={
                "dataset": "TestDataset",
                "name": "OldField"
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.delete_field.return_value = OperationResult(success=True)
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="delete_field",
            request={}
        )
        
        assert result["status"] == "ok"
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_unsupported_endpoint(self, mock_server):
        """Test confirm_operation with unsupported endpoint."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="unknown",
            endpoint="unknown",
            parameters={},
            token="test-token"
        )
        
        mock_server.get_tools.return_value = Mock()
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="unknown",
            request={}
        )
        
        assert result["status"] == "error"
        assert "Unsupported endpoint" in result["detail"]
    
    @patch('fgdb_toolserver.server')
    def test_confirm_operation_failed_execution(self, mock_server):
        """Test confirm_operation when execution fails."""
        from fgdb_toolserver import confirm_operation
        
        pending = PendingOperation(
            operation="insert",
            endpoint="insert",
            parameters={
                "dataset": "TestDataset",
                "rows": 1,
                "fields": ["Name"],
                "values": ["Test"]
            },
            token="test-token"
        )
        
        mock_tools = Mock()
        mock_tools.insert.return_value = OperationResult(
            success=False,
            error="Execution failed"
        )
        mock_server.get_tools.return_value = mock_tools
        mock_server.safety.validate_token.return_value = pending
        
        result = confirm_operation(
            token="test-token",
            endpoint="insert",
            request={}
        )
        
        assert result["status"] == "error"
        assert "Execution failed" in result["detail"]


class TestFGDBMCPServer:
    """Tests for FGDBMCPServer class."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        from fgdb_toolserver import FGDBMCPServer
        from utils.config import ServerConfig
        
        config = ServerConfig()
        server = FGDBMCPServer(config=config)
        
        assert server.config == config
        assert server.safety is not None
        assert server._tools is None
        assert server._current_connection is None
        assert server.arcpy_error is False
    
    @patch('fgdb_toolserver.create_tools_from_env')
    def test_get_tools_success(self, mock_create_tools):
        """Test successful tool initialization."""
        from fgdb_toolserver import FGDBMCPServer
        from utils.config import ServerConfig
        
        mock_tools = Mock()
        mock_create_tools.return_value = mock_tools
        
        server = FGDBMCPServer(config=ServerConfig())
        tools = server.get_tools("C:\\test\\test.gdb")
        
        assert tools == mock_tools
        assert server._current_connection == "C:\\test\\test.gdb"
        mock_create_tools.assert_called_once()
    
    def test_get_tools_no_connection(self):
        """Test get_tools without connection."""
        from fgdb_toolserver import FGDBMCPServer
        from utils.config import ServerConfig
        
        server = FGDBMCPServer(config=ServerConfig())
        
        with pytest.raises(DatabaseConnectionError):
            server.get_tools()
    
    @patch('fgdb_toolserver.create_tools_from_env')
    def test_get_tools_reuses_existing(self, mock_create_tools):
        """Test get_tools reuses existing tools instance."""
        from fgdb_toolserver import FGDBMCPServer
        from utils.config import ServerConfig
        
        mock_tools = Mock()
        mock_create_tools.return_value = mock_tools
        
        server = FGDBMCPServer(config=ServerConfig())
        server._current_connection = "C:\\test\\test.gdb"
        server._tools = mock_tools
        
        tools = server.get_tools()
        
        assert tools == mock_tools
        mock_create_tools.assert_not_called()
    
    @patch('fgdb_toolserver.create_tools_from_env')
    def test_get_tools_reinitializes_on_new_connection(self, mock_create_tools):
        """Test get_tools reinitializes on new connection."""
        from fgdb_toolserver import FGDBMCPServer
        from utils.config import ServerConfig
        
        mock_tools1 = Mock()
        mock_tools2 = Mock()
        mock_create_tools.side_effect = [mock_tools1, mock_tools2]
        
        server = FGDBMCPServer(config=ServerConfig())
        
        # First call - establish first connection
        tools1 = server.get_tools("C:\\test\\test1.gdb")
        
        assert tools1 == mock_tools1
        assert server._current_connection == "C:\\test\\test1.gdb"
        assert mock_create_tools.call_count == 1
        
        # Second call - switch to new connection (should reinitialize)
        tools2 = server.get_tools("C:\\test\\test2.gdb")
        
        assert tools2 == mock_tools2
        assert server._current_connection == "C:\\test\\test2.gdb"
        assert mock_create_tools.call_count == 2

