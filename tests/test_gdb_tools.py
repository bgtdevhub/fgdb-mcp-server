"""Tests for gdb_ops/gdb_tools.py."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from gdb_ops.gdb_tools import (
    GDBTools,
    MutatingCommand,
    SafetyCommandExecutor,
    CommandExecutorProtocol,
    create_tools_from_env
)
from gdb_ops.gdb import GDBBackendProtocol
from utils.safety import SafetyManager, RiskLevel, PendingOperation
from dtos.requestobjects import Connection, OperationResult
from tests.conftest import FakeGDBBackend


class TestMutatingCommand:
    """Tests for MutatingCommand class."""
    
    def test_mutating_command_creation(self):
        """Test creating a mutating command."""
        def execute_func():
            return "result"
        
        command = MutatingCommand(
            operation_name="test",
            endpoint="test",
            risk_level=RiskLevel.MEDIUM,
            execute=execute_func,
            parameters={"key": "value"},
            log_context={"Dataset": "Test"}
        )
        
        assert command.operation_name == "test"
        assert command.endpoint == "test"
        assert command.risk_level == RiskLevel.MEDIUM
        assert command.execute() == "result"
        assert command.parameters == {"key": "value"}
    
    def test_mutating_command_get_log_message(self):
        """Test log message generation."""
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=RiskLevel.MEDIUM,
            execute=lambda: None,
            parameters={},
            log_context={"Dataset": "TestDataset", "Rows": 5}
        )
        
        log_msg = command.get_log_message()
        assert "Operation: insert" in log_msg
        assert "Risk: medium" in log_msg
        assert "Dataset: TestDataset" in log_msg
        assert "Rows: 5" in log_msg


class TestSafetyCommandExecutor:
    """Tests for SafetyCommandExecutor class."""
    
    def test_executor_initialization(self):
        """Test executor initialization."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        assert executor.safety == safety_manager
    
    def test_execute_with_confirmed_token(self):
        """Test executing command with confirmed token."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        # Register a pending operation
        token = "test-token-123"
        safety_manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters={"dataset": "Test", "rows": 1, "fields": [], "values": []}
        )
        
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=RiskLevel.MEDIUM,
            execute=lambda: 5,
            parameters={},
            log_context={}
        )
        
        result = executor.execute(command, confirmed_token=token)
        
        assert result.success is True
        assert result.data == 5
        # Token should be consumed
        assert safety_manager.validate_token(token) is None
    
    def test_execute_with_invalid_token(self):
        """Test executing command with invalid token."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=RiskLevel.MEDIUM,
            execute=lambda: 5,
            parameters={},
            log_context={}
        )
        
        result = executor.execute(command, confirmed_token="invalid-token")
        
        assert result.success is False
        assert "Invalid or expired" in result.error
    
    def test_execute_medium_risk_requires_confirmation(self):
        """Test medium risk operation requires confirmation."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=RiskLevel.MEDIUM,
            execute=lambda: 5,
            parameters={"dataset": "Test", "rows": 1, "fields": [], "values": []},
            log_context={}
        )
        
        result = executor.execute(command)
        
        assert result.success is False
        assert result.requires_confirmation is True
        assert result.confirmation_token is not None
    
    def test_execute_high_risk_requires_confirmation(self):
        """Test high risk operation requires confirmation."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        command = MutatingCommand(
            operation_name="delete",
            endpoint="delete",
            risk_level=RiskLevel.HIGH,
            execute=lambda: 3,
            parameters={"dataset": "Test", "where": "OBJECTID = 1"},
            log_context={}
        )
        
        result = executor.execute(command)
        
        assert result.success is False
        assert result.requires_confirmation is True
        assert result.confirmation_token is not None
    
    def test_execute_low_risk_allowed(self):
        """Test low risk operation is allowed."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        command = MutatingCommand(
            operation_name="read",
            endpoint="read",
            risk_level=RiskLevel.LOW,
            execute=lambda: "data",
            parameters={},
            log_context={}
        )
        
        result = executor.execute(command)
        
        assert result.success is True
        assert result.data == "data"
    
    def test_execute_extreme_risk_blocked(self):
        """Test extreme risk operation is blocked."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        command = MutatingCommand(
            operation_name="dangerous",
            endpoint="dangerous",
            risk_level=RiskLevel.EXTREME,
            execute=lambda: None,
            parameters={},
            log_context={}
        )
        
        result = executor.execute(command)
        
        assert result.success is False
        assert result.requires_confirmation is False
        assert result.confirmation_token is None
        assert "blocked" in result.error.lower()
    
    def test_execute_command_exception(self):
        """Test executor handles command execution exceptions."""
        safety_manager = SafetyManager()
        executor = SafetyCommandExecutor(safety_manager)
        
        def failing_execute():
            raise Exception("Test error")
        
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=RiskLevel.LOW,
            execute=failing_execute,
            parameters={},
            log_context={}
        )
        
        result = executor.execute(command)
        
        assert result.success is False
        assert "Test error" in result.error


class TestGDBTools:
    """Tests for GDBTools class."""
    
    def test_gdb_tools_initialization(self, fake_backend, fake_safety_manager):
        """Test GDBTools initialization."""
        tools = GDBTools(
            backend=fake_backend,
            safety=fake_safety_manager
        )
        
        assert tools.backend == fake_backend
        assert tools.safety == fake_safety_manager
        assert tools.executor is not None
        assert isinstance(tools.executor, SafetyCommandExecutor)
    
    def test_list_all_feature_classes(self, fake_tools):
        """Test listing all feature classes."""
        result = fake_tools.list_all_feature_classes()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Sewerage\\SewerageLine" in result
    
    def test_describe(self, fake_tools):
        """Test describing a dataset."""
        result = fake_tools.describe("TestDataset")
        
        assert result["name"] == "TestDataset"
        assert result["datasetType"] == "FeatureClass"
        assert "fields" in result
    
    def test_describe_nonexistent_dataset(self, fake_tools):
        """Test describing a non-existent dataset."""
        with pytest.raises(ValueError, match="does not exist"):
            fake_tools.describe("NonExistentDataset")
    
    def test_count(self, fake_tools):
        """Test counting records."""
        count = fake_tools.count("TestDataset")
        
        assert count == 3
    
    def test_select(self, fake_tools):
        """Test selecting records."""
        result = fake_tools.select("TestDataset", where=None, fields=[], limit=10)
        
        assert "data" in result
        assert "hasMore" in result
        assert len(result["data"]) == 3
    
    def test_select_with_where(self, fake_tools):
        """Test selecting records with WHERE clause."""
        result = fake_tools.select("TestDataset", where="OBJECTID = 1", fields=[], limit=10)
        
        assert len(result["data"]) == 1
        assert result["data"][0]["OBJECTID"] == 1
    
    def test_select_with_fields(self, fake_tools):
        """Test selecting records with field selection."""
        result = fake_tools.select("TestDataset", where=None, fields=["Name"], limit=10)
        
        assert len(result["data"]) > 0
        assert "Name" in result["data"][0]
        assert "OBJECTID" in result["data"][0]  # OBJECTID always included
    
    def test_insert_requires_confirmation(self, fake_tools):
        """Test insert operation requires confirmation."""
        result = fake_tools.insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        
        assert result.success is False
        assert result.requires_confirmation is True
        assert result.confirmation_token is not None
    
    def test_insert_with_confirmation(self, fake_tools):
        """Test insert operation with confirmation token."""
        # First get confirmation token
        first_result = fake_tools.insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        token = first_result.confirmation_token
        
        # Confirm the operation
        result = fake_tools.insert(
            "TestDataset",
            rows=1,
            fields=["Name"],
            values=["Test"],
            confirmed_token=token
        )
        
        assert result.success is True
        assert result.data == 1
    
    def test_update_requires_confirmation(self, fake_tools):
        """Test update operation requires confirmation."""
        result = fake_tools.update("TestDataset", updates={"Name": "Updated"}, where="OBJECTID = 1")
        
        assert result.success is False
        assert result.requires_confirmation is True
    
    def test_update_with_confirmation(self, fake_tools):
        """Test update operation with confirmation token."""
        # Get confirmation token
        first_result = fake_tools.update("TestDataset", updates={"Name": "Updated"}, where="OBJECTID = 1")
        token = first_result.confirmation_token
        
        # Confirm the operation
        result = fake_tools.update(
            "TestDataset",
            updates={"Name": "Updated"},
            where="OBJECTID = 1",
            confirmed_token=token
        )
        
        assert result.success is True
        assert result.data == 1
    
    def test_delete_requires_confirmation(self, fake_tools):
        """Test delete operation requires confirmation."""
        result = fake_tools.delete("TestDataset", where="OBJECTID = 1")
        
        assert result.success is False
        assert result.requires_confirmation is True
    
    def test_delete_with_confirmation(self, fake_tools):
        """Test delete operation with confirmation token."""
        # Get confirmation token
        first_result = fake_tools.delete("TestDataset", where="OBJECTID = 1")
        token = first_result.confirmation_token
        
        # Confirm the operation
        result = fake_tools.delete(
            "TestDataset",
            where="OBJECTID = 1",
            confirmed_token=token
        )
        
        assert result.success is True
        assert result.data == 1
    
    def test_add_field_requires_confirmation(self, fake_tools):
        """Test add_field operation requires confirmation."""
        result = fake_tools.add_field("TestDataset", name="NewField", field_type="TEXT", length=50)
        
        assert result.success is False
        assert result.requires_confirmation is True
    
    def test_add_field_with_confirmation(self, fake_tools):
        """Test add_field operation with confirmation token."""
        # Get confirmation token
        first_result = fake_tools.add_field("TestDataset", name="NewField", field_type="TEXT", length=50)
        token = first_result.confirmation_token
        
        # Confirm the operation
        result = fake_tools.add_field(
            "TestDataset",
            name="NewField",
            field_type="TEXT",
            length=50,
            confirmed_token=token
        )
        
        assert result.success is True
    
    def test_delete_field_requires_confirmation(self, fake_tools):
        """Test delete_field operation requires confirmation."""
        result = fake_tools.delete_field("TestDataset", name="Name")
        
        assert result.success is False
        assert result.requires_confirmation is True
    
    def test_delete_field_with_confirmation(self, fake_tools):
        """Test delete_field operation with confirmation token."""
        # Get confirmation token
        first_result = fake_tools.delete_field("TestDataset", name="Name")
        token = first_result.confirmation_token
        
        # Confirm the operation
        result = fake_tools.delete_field(
            "TestDataset",
            name="Name",
            confirmed_token=token
        )
        
        assert result.success is True
    
    def test_custom_executor_injection(self, fake_backend, fake_safety_manager):
        """Test injecting custom executor."""
        fake_executor = Mock(spec=CommandExecutorProtocol)
        fake_executor.execute.return_value = OperationResult(success=True, data=42)
        
        tools = GDBTools(
            backend=fake_backend,
            safety=fake_safety_manager
        )
        tools.executor = fake_executor
        
        result = tools.insert("TestDataset", rows=1, fields=["Name"], values=["Test"])
        
        assert result.success is True
        assert result.data == 42
        fake_executor.execute.assert_called_once()


class TestCreateToolsFromEnv:
    """Tests for create_tools_from_env factory function."""
    
    @patch('gdb_ops.gdb_tools.FileGDBBackend')
    @patch('gdb_ops.gdb_tools.os.path.isdir')
    def test_create_tools_from_env_success(self, mock_isdir, mock_backend_class):
        """Test successful tool creation."""
        mock_isdir.return_value = True
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        
        conn = Connection(connection_string="C:\\test\\test.gdb")
        
        tools = create_tools_from_env(conn)
        
        assert tools is not None
        assert tools.backend == mock_backend
        mock_backend_class.assert_called_once_with(gdb_path="C:\\test\\test.gdb")
    
    @patch('gdb_ops.gdb_tools.FileGDBBackend')
    @patch('gdb_ops.gdb_tools.os.path.isdir')
    def test_create_tools_from_env_with_safety_manager(self, mock_isdir, mock_backend_class):
        """Test tool creation with custom safety manager."""
        mock_isdir.return_value = True
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        
        safety_manager = SafetyManager()
        conn = Connection(connection_string="C:\\test\\test.gdb")
        
        tools = create_tools_from_env(conn, safety=safety_manager)
        
        assert tools.safety == safety_manager
    
    @patch('gdb_ops.gdb_tools.FileGDBBackend')
    @patch('gdb_ops.gdb_tools.os.path.isdir')
    def test_create_tools_from_env_with_executor(self, mock_isdir, mock_backend_class):
        """Test tool creation with custom executor."""
        mock_isdir.return_value = True
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        
        fake_executor = Mock(spec=CommandExecutorProtocol)
        conn = Connection(connection_string="C:\\test\\test.gdb")
        
        tools = create_tools_from_env(conn, executor=fake_executor)
        
        assert tools.executor == fake_executor
    
    @patch('gdb_ops.gdb_tools.os.path.isdir')
    def test_create_tools_from_env_invalid_path(self, mock_isdir):
        """Test tool creation with invalid path."""
        mock_isdir.return_value = False
        
        conn = Connection(connection_string="invalid_path")
        
        with pytest.raises(Exception, match="Invalid path"):
            create_tools_from_env(conn)
    
    @patch('gdb_ops.gdb_tools.FileGDBBackend')
    @patch('gdb_ops.gdb_tools.os.path.isdir')
    def test_create_tools_from_env_backend_error(self, mock_isdir, mock_backend_class):
        """Test tool creation when backend creation fails."""
        mock_isdir.return_value = True
        mock_backend_class.side_effect = Exception("Backend error")
        
        conn = Connection(connection_string="C:\\test\\test.gdb")
        
        with pytest.raises(RuntimeError, match="Backend error"):
            create_tools_from_env(conn)

