"""Unit tests for Data Transfer Objects (DTOs)."""
import pytest
from typing import Any, Dict
import json

from dtos.requestobjects import Connection, OperationResult

pytestmark = pytest.mark.unit


class TestConnection:
    """Tests for Connection class."""
    
    def test_connection_initialization(self):
        """Test Connection initialization."""
        conn = Connection()
        assert conn.connection_string is None
    
    def test_connection_string_assignment(self):
        """Test assigning connection string."""
        conn = Connection()
        conn.connection_string = "C:\\test\\test.gdb"
        assert conn.connection_string == "C:\\test\\test.gdb"
    
    def test_connection_string_update(self):
        """Test updating connection string."""
        conn = Connection()
        conn.connection_string = "C:\\test\\test1.gdb"
        assert conn.connection_string == "C:\\test\\test1.gdb"
        
        conn.connection_string = "C:\\test\\test2.gdb"
        assert conn.connection_string == "C:\\test\\test2.gdb"
    
    def test_connection_string_none(self):
        """Test setting connection string to None."""
        conn = Connection()
        conn.connection_string = "C:\\test\\test.gdb"
        conn.connection_string = None
        assert conn.connection_string is None


class TestOperationResult:
    """Tests for OperationResult DTO."""
    
    def test_operation_result_creation_success(self):
        """Test creating a successful operation result."""
        result = OperationResult(success=True, data=42)
        
        assert result.success is True
        assert result.data == 42
        assert result.requires_confirmation is False
        assert result.confirmation_token is None
        assert result.error is None
    
    def test_operation_result_creation_failure(self):
        """Test creating a failed operation result."""
        result = OperationResult(success=False, error="Test error")
        
        assert result.success is False
        assert result.error == "Test error"
        assert result.data is None
        assert result.requires_confirmation is False
        assert result.confirmation_token is None
    
    def test_operation_result_requires_confirmation(self):
        """Test creating an operation result requiring confirmation."""
        result = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="test-token-123"
        )
        
        assert result.success is False
        assert result.requires_confirmation is True
        assert result.confirmation_token == "test-token-123"
        assert result.error is None
    
    def test_operation_result_default_values(self):
        """Test OperationResult default values."""
        result = OperationResult(success=True)
        
        assert result.success is True
        assert result.data is None
        assert result.requires_confirmation is False
        assert result.confirmation_token is None
        assert result.error is None
    
    def test_operation_result_with_data(self):
        """Test OperationResult with various data types."""
        # Integer data
        result1 = OperationResult(success=True, data=42)
        assert result1.data == 42
        
        # String data
        result2 = OperationResult(success=True, data="test")
        assert result2.data == "test"
        
        # List data
        result3 = OperationResult(success=True, data=[1, 2, 3])
        assert result3.data == [1, 2, 3]
        
        # Dict data
        result4 = OperationResult(success=True, data={"key": "value"})
        assert result4.data == {"key": "value"}
    
    def test_operation_result_serialization(self):
        """Test OperationResult JSON serialization."""
        result = OperationResult(
            success=True,
            data={"count": 5},
            requires_confirmation=False
        )
        
        # Pydantic models are JSON serializable
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        
        # Parse back
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["data"] == {"count": 5}
        assert parsed["requires_confirmation"] is False
    
    def test_operation_result_model_dump(self):
        """Test OperationResult model_dump method."""
        result = OperationResult(
            success=False,
            error="Test error",
            requires_confirmation=True,
            confirmation_token="token-123"
        )
        
        dumped = result.model_dump()
        assert dumped == {
            "success": False,
            "data": None,
            "requires_confirmation": True,
            "confirmation_token": "token-123",
            "error": "Test error"
        }
    
    def test_operation_result_model_dump_exclude_none(self):
        """Test OperationResult model_dump excluding None values."""
        result = OperationResult(success=True, data=42)
        
        dumped = result.model_dump(exclude_none=True)
        assert "data" in dumped
        assert "error" not in dumped
        assert "confirmation_token" not in dumped
    
    def test_operation_result_validation(self):
        """Test OperationResult field validation."""
        # Valid: success with data
        result1 = OperationResult(success=True, data=42)
        assert result1.success is True
        
        # Valid: failure with error
        result2 = OperationResult(success=False, error="Error")
        assert result2.success is False
        
        # Valid: requires confirmation
        result3 = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="token"
        )
        assert result3.requires_confirmation is True
    
    def test_operation_result_all_fields(self):
        """Test OperationResult with all fields set."""
        result = OperationResult(
            success=True,
            data={"result": "ok"},
            requires_confirmation=False,
            confirmation_token=None,
            error=None
        )
        
        assert result.success is True
        assert result.data == {"result": "ok"}
        assert result.requires_confirmation is False
        assert result.confirmation_token is None
        assert result.error is None
    
    def test_operation_result_from_dict(self):
        """Test creating OperationResult from dictionary."""
        data = {
            "success": True,
            "data": 42,
            "requires_confirmation": False
        }
        
        result = OperationResult(**data)
        assert result.success is True
        assert result.data == 42
        assert result.requires_confirmation is False

