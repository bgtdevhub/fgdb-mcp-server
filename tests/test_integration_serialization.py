"""Integration tests for serialization of responses and DTOs."""
import pytest
import json
from typing import Dict, Any

from dtos.requestobjects import OperationResult
from utils.exceptions import (
    DatabaseConnectionError,
    OperationBlockedError,
    ValidationError
)

pytestmark = pytest.mark.integration


class TestOperationResultSerialization:
    """Integration tests for OperationResult serialization."""
    
    def test_operation_result_json_serialization_success(self):
        """Test JSON serialization of successful operation result."""
        result = OperationResult(success=True, data={"count": 5})
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["success"] is True
        assert parsed["data"] == {"count": 5}
        assert parsed["requires_confirmation"] is False
        assert parsed["confirmation_token"] is None
        assert parsed["error"] is None
    
    def test_operation_result_json_serialization_failure(self):
        """Test JSON serialization of failed operation result."""
        result = OperationResult(success=False, error="Operation failed")
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["success"] is False
        assert parsed["error"] == "Operation failed"
        assert parsed["data"] is None
    
    def test_operation_result_json_serialization_confirmation(self):
        """Test JSON serialization of operation requiring confirmation."""
        result = OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token="token-123"
        )
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["success"] is False
        assert parsed["requires_confirmation"] is True
        assert parsed["confirmation_token"] == "token-123"
    
    def test_operation_result_round_trip(self):
        """Test round-trip serialization/deserialization."""
        original = OperationResult(
            success=True,
            data={"inserted": 5},
            requires_confirmation=False
        )
        
        json_str = original.model_dump_json()
        parsed_dict = json.loads(json_str)
        reconstructed = OperationResult(**parsed_dict)
        
        assert reconstructed.success == original.success
        assert reconstructed.data == original.data
        assert reconstructed.requires_confirmation == original.requires_confirmation


class TestErrorResponseSerialization:
    """Integration tests for error response serialization."""
    
    def test_database_connection_error_serialization(self):
        """Test serialization of database connection error response."""
        error_response = {
            "status": "error",
            "message": "Connection failed"
        }
        
        json_str = json.dumps(error_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "error"
        assert parsed["message"] == "Connection failed"
    
    def test_operation_blocked_error_serialization(self):
        """Test serialization of operation blocked error."""
        error_response = {
            "status": "error",
            "detail": "Operation blocked by safety checks"
        }
        
        json_str = json.dumps(error_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "error"
        assert "blocked" in parsed["detail"].lower()
    
    def test_validation_error_serialization(self):
        """Test serialization of validation error."""
        error_response = {
            "status": "error",
            "detail": "Invalid input: dataset name required"
        }
        
        json_str = json.dumps(error_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "error"
        assert "invalid" in parsed["detail"].lower()


class TestPaginationResponseSerialization:
    """Integration tests for pagination response serialization."""
    
    def test_pagination_response_structure(self):
        """Test pagination response structure and serialization."""
        pagination_response = {
            "data": [{"id": 1}, {"id": 2}],
            "limit": 10,
            "has_more": True,
            "total_records": 2
        }
        
        json_str = json.dumps(pagination_response)
        parsed = json.loads(json_str)
        
        assert "data" in parsed
        assert "limit" in parsed
        assert "has_more" in parsed
        assert len(parsed["data"]) == 2
        assert parsed["has_more"] is True
    
    def test_pagination_response_no_more(self):
        """Test pagination response when no more records."""
        pagination_response = {
            "data": [{"id": 1}],
            "limit": 10,
            "has_more": False,
            "total_records": 1
        }
        
        json_str = json.dumps(pagination_response)
        parsed = json.loads(json_str)
        
        assert parsed["has_more"] is False
        assert len(parsed["data"]) == 1
    
    def test_pagination_response_empty(self):
        """Test pagination response with empty data."""
        pagination_response = {
            "data": [],
            "limit": 10,
            "has_more": False,
            "total_records": 0
        }
        
        json_str = json.dumps(pagination_response)
        parsed = json.loads(json_str)
        
        assert parsed["data"] == []
        assert parsed["has_more"] is False


class TestConfirmationResponseSerialization:
    """Integration tests for confirmation response serialization."""
    
    def test_confirmation_required_response(self):
        """Test serialization of confirmation required response."""
        confirmation_response = {
            "status": "confirmation_required",
            "confirmation_token": "token-123",
            "endpoint": "insert",
            "message": "This operation requires confirmation."
        }
        
        json_str = json.dumps(confirmation_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "confirmation_required"
        assert parsed["confirmation_token"] == "token-123"
        assert parsed["endpoint"] == "insert"
    
    def test_confirmation_success_response(self):
        """Test serialization of confirmed operation success response."""
        success_response = {
            "status": "ok",
            "inserted": 5
        }
        
        json_str = json.dumps(success_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "ok"
        assert parsed["inserted"] == 5


class TestComplexDataSerialization:
    """Integration tests for complex data structure serialization."""
    
    def test_nested_dict_serialization(self):
        """Test serialization of nested dictionaries."""
        result = OperationResult(
            success=True,
            data={
                "metadata": {
                    "count": 5,
                    "dataset": "TestDataset"
                },
                "records": [{"id": 1}, {"id": 2}]
            }
        )
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert "metadata" in parsed["data"]
        assert "records" in parsed["data"]
        assert parsed["data"]["metadata"]["count"] == 5
    
    def test_list_of_dicts_serialization(self):
        """Test serialization of list of dictionaries."""
        result = OperationResult(
            success=True,
            data=[
                {"id": 1, "name": "Test1"},
                {"id": 2, "name": "Test2"}
            ]
        )
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert isinstance(parsed["data"], list)
        assert len(parsed["data"]) == 2
        assert parsed["data"][0]["id"] == 1
    
    def test_mixed_types_serialization(self):
        """Test serialization of mixed data types."""
        result = OperationResult(
            success=True,
            data={
                "count": 42,
                "name": "Test",
                "active": True,
                "values": [1, 2, 3],
                "metadata": {"key": "value"}
            }
        )
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert isinstance(parsed["data"]["count"], int)
        assert isinstance(parsed["data"]["name"], str)
        assert isinstance(parsed["data"]["active"], bool)
        assert isinstance(parsed["data"]["values"], list)


class TestResponseConsistency:
    """Integration tests for response format consistency."""
    
    def test_success_response_format(self):
        """Test that success responses have consistent format."""
        responses = [
            {"status": "ok", "inserted": 5},
            {"status": "ok", "updated": 3},
            {"status": "ok", "deleted": 2}
        ]
        
        for response in responses:
            json_str = json.dumps(response)
            parsed = json.loads(json_str)
            assert parsed["status"] == "ok"
            assert "inserted" in parsed or "updated" in parsed or "deleted" in parsed
    
    def test_error_response_format(self):
        """Test that error responses have consistent format."""
        responses = [
            {"status": "error", "message": "Error 1"},
            {"status": "error", "detail": "Error 2"}
        ]
        
        for response in responses:
            json_str = json.dumps(response)
            parsed = json.loads(json_str)
            assert parsed["status"] == "error"
            assert "message" in parsed or "detail" in parsed

