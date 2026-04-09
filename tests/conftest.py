"""Pytest configuration and fixtures for FGDB MCP Server tests."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from gdb_ops.gdb import GDBBackendProtocol
from gdb_ops.gdb_tools import GDBTools, CommandExecutorProtocol, SafetyCommandExecutor
from utils.safety import SafetyManager, RiskLevel, PendingOperation
from utils.config import ServerConfig
from dtos.requestobjects import Connection, OperationResult


class FakeGDBBackend:
    """Fake implementation of GDBBackendProtocol for testing."""
    
    def __init__(self):
        self.feature_classes = ["Sewerage\\SewerageLine", "Sewerage\\SewerageJunction"]
        self.datasets: Dict[str, Dict[str, Any]] = {
            "TestDataset": {
                "name": "TestDataset",
                "datasetType": "FeatureClass",
                "shapeType": "Polyline",
                "spatialReference": "SVY21_Singapore_TM",
                "fields": [
                    {"name": "OBJECTID", "type": "OID", "length": None, "nullable": False},
                    {"name": "Shape", "type": "Geometry", "length": None, "nullable": True},
                    {"name": "Name", "type": "String", "length": 50, "nullable": True},
                ]
            }
        }
        self.records: Dict[str, List[Dict[str, Any]]] = {
            "TestDataset": [
                {"OBJECTID": 1, "Name": "Record 1"},
                {"OBJECTID": 2, "Name": "Record 2"},
                {"OBJECTID": 3, "Name": "Record 3"},
            ]
        }
        self.insert_count = 0
        self.update_count = 0
        self.delete_count = 0
        self.domains: List[Dict[str, Any]] = [
            {
                "name": "StatusDomain",
                "domainType": "CodedValue",
                "codedValues": [
                    {"value": 1, "description": "Active"},
                    {"value": 2, "description": "Inactive"},
                ],
            },
            {
                "name": "ElevationDomain",
                "domainType": "Range",
                "range": {"min": 0.0, "max": 1000.0},
            },
        ]
    
    def list_all_feature_classes(self) -> List[str]:
        return self.feature_classes
    
    def list_domains(self) -> List[Dict[str, Any]]:
        return self.domains

    def list_datasets_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        # Fake: TestDataset has a field "Name" that uses "StatusDomain"
        if domain_name == "StatusDomain":
            return [{"dataset": "TestDataset", "fields": ["Name"]}]
        return []

    def describe(self, dataset: str) -> Dict[str, Any]:
        if dataset not in self.datasets:
            raise ValueError(f"Dataset '{dataset}' does not exist")
        return self.datasets[dataset]
    
    def select(
        self, 
        dataset: str, 
        where: Optional[str] = None, 
        fields: Optional[List[str]] = None, 
        limit: int = 50000
    ) -> Dict[str, Any]:
        if dataset not in self.records:
            raise ValueError(f"Dataset '{dataset}' does not exist")
        
        data = self.records[dataset].copy()
        
        # Simple WHERE clause filtering (for testing)
        if where:
            if "OBJECTID > 2" in where:
                data = [r for r in data if r["OBJECTID"] > 2]
            elif "OBJECTID = 1" in where:
                data = [r for r in data if r["OBJECTID"] == 1]
        
        # Field filtering
        if fields:
            # Always include OBJECTID if it exists in the record
            fields_with_oid = set(fields)
            if any("OBJECTID" in r for r in data):
                fields_with_oid.add("OBJECTID")
            data = [{k: v for k, v in r.items() if k in fields_with_oid} for r in data]
        
        # Limit
        data = data[:limit]
        
        return {
            "data": data,
            "hasMore": len(self.records[dataset]) > len(data)
        }
    
    def count(self, dataset: str, where: Optional[str] = None) -> int:
        if dataset not in self.records:
            raise ValueError(f"Dataset '{dataset}' does not exist")
        
        count = len(self.records[dataset])
        
        # Simple WHERE clause filtering
        if where:
            if "OBJECTID > 2" in where:
                count = len([r for r in self.records[dataset] if r["OBJECTID"] > 2])
            elif "OBJECTID = 1" in where:
                count = 1
        
        return count
    
    def insert(self, dataset: str, rows: int, fields: List[str], values: List[str]) -> int:
        self.insert_count += rows
        return rows
    
    def update(self, dataset: str, updates: Dict[str, Any], where: Optional[str] = None) -> int:
        self.update_count += 1
        return 1
    
    def delete(self, dataset: str, where: Optional[str] = None) -> int:
        self.delete_count += 1
        return 1
    
    def add_field(self, dataset: str, name: str, field_type: str, length: Optional[int] = None) -> None:
        if dataset not in self.datasets:
            raise ValueError(f"Dataset '{dataset}' does not exist")
        self.datasets[dataset]["fields"].append({
            "name": name,
            "type": field_type,
            "length": length,
            "nullable": True
        })
    
    def delete_field(self, dataset: str, name: str) -> None:
        if dataset not in self.datasets:
            raise ValueError(f"Dataset '{dataset}' does not exist")
        self.datasets[dataset]["fields"] = [
            f for f in self.datasets[dataset]["fields"] if f["name"] != name
        ]


class FakeCommandExecutor:
    """Fake implementation of CommandExecutorProtocol for testing."""
    
    def __init__(self, auto_confirm: bool = False):
        self.auto_confirm = auto_confirm
        self.executed_commands = []
    
    def execute(
        self,
        command: Any,
        confirmed_token: Optional[str] = None
    ) -> OperationResult:
        self.executed_commands.append((command, confirmed_token))
        
        if confirmed_token or self.auto_confirm:
            try:
                result = command.execute()
                return OperationResult(success=True, data=result)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # Simulate requiring confirmation
        token = "test-token-123"
        return OperationResult(
            success=False,
            requires_confirmation=True,
            confirmation_token=token
        )


@pytest.fixture
def fake_backend():
    """Create a fake GDB backend for testing."""
    return FakeGDBBackend()


@pytest.fixture
def fake_safety_manager():
    """Create a fake safety manager for testing."""
    return SafetyManager()


@pytest.fixture
def fake_executor(fake_safety_manager):
    """Create a fake command executor for testing."""
    return SafetyCommandExecutor(fake_safety_manager)


@pytest.fixture
def fake_tools(fake_backend, fake_safety_manager, fake_executor):
    """Create GDBTools with fake dependencies."""
    tools = GDBTools(
        backend=fake_backend,
        safety=fake_safety_manager
    )
    tools.executor = fake_executor
    return tools


@pytest.fixture
def mock_server_config():
    """Create a mock server configuration."""
    config = ServerConfig()
    config.max_select_limit = 50000
    return config


@pytest.fixture
def mock_server(mock_server_config, fake_tools):
    """Create a mock server instance."""
    from fgdb_toolserver import FGDBMCPServer
    
    server = FGDBMCPServer(config=mock_server_config)
    server._tools = fake_tools
    server._current_connection = "C:\\test\\test.gdb"
    return server


@pytest.fixture
def sample_connection():
    """Create a sample connection object."""
    conn = Connection(connection_string="C:\\test\\test.gdb")
    return conn


@pytest.fixture
def sample_operation_result_success():
    """Create a successful operation result."""
    return OperationResult(success=True, data=5)


@pytest.fixture
def sample_operation_result_confirmation():
    """Create an operation result requiring confirmation."""
    return OperationResult(
        success=False,
        requires_confirmation=True,
        confirmation_token="test-token-123"
    )


@pytest.fixture
def sample_operation_result_error():
    """Create a failed operation result."""
    return OperationResult(
        success=False,
        error="Test error message"
    )


@pytest.fixture
def sample_pending_operation():
    """Create a sample pending operation."""
    return PendingOperation(
        operation="insert",
        endpoint="insert",
        parameters={"dataset": "TestDataset", "rows": 1, "fields": ["Name"], "values": ["Test"]},
        token="test-token-123"
    )

