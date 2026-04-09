from __future__ import annotations

import logging
from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional, Union, Callable, Protocol, runtime_checkable

from dtos.requestobjects import Connection, OperationResult
from utils import safety
from utils.safety import SafetyManager
from .gdb import FileGDBBackend, GDBBackendProtocol

logger = logging.getLogger(__name__)


@dataclass
class MutatingCommand:
    """Command object encapsulating a mutating operation with its metadata.
    
    This command pattern allows operations to be encapsulated with their
    execution logic, safety requirements, and logging context.
    """
    operation_name: str
    endpoint: str
    risk_level: safety.RiskLevel
    execute: Callable[[], Any]  # The actual operation to execute
    parameters: Dict[str, Any]
    log_context: Dict[str, Any] = field(default_factory=dict)
    
    def get_log_message(self) -> str:
        """Generate log message for this operation."""
        context_str = ", ".join(f"{k}: {v}" for k, v in self.log_context.items())
        return f"Operation: {self.operation_name}, Risk: {self.risk_level.value}, {context_str}"


@runtime_checkable
class CommandExecutorProtocol(Protocol):
    """Protocol defining the interface for command execution with safety confirmation.
    
    This protocol uses structural typing (duck typing), meaning any class that
    implements the execute method with compatible signature automatically
    satisfies this protocol. No explicit inheritance or declaration is needed.
    
    Example:
        SafetyCommandExecutor automatically implements this protocol. You can verify:
        
        >>> executor = SafetyCommandExecutor(safety_manager)
        >>> isinstance(executor, CommandExecutorProtocol)  # True (with @runtime_checkable)
    """
    
    def execute(
        self,
        command: MutatingCommand,
        confirmed_token: Optional[str] = None
    ) -> OperationResult:
        """Execute a command with safety confirmation.
        
        Args:
            command: The command to execute
            confirmed_token: Optional confirmation token
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        ...


class SafetyCommandExecutor:
    """Default implementation of CommandExecutorProtocol with safety confirmation logic.
    
    This executor handles the safety confirmation flow for mutating operations,
    including token validation, risk evaluation, and pending operation registration.
    """
    
    def __init__(self, safety_manager: SafetyManager):
        self.safety = safety_manager
    
    def execute(
        self,
        command: MutatingCommand,
        confirmed_token: Optional[str] = None
    ) -> OperationResult:
        """Execute a command with safety confirmation."""
        # If a confirmed token is provided, validate it and proceed directly
        if confirmed_token:
            pending = self.safety.confirm_with_token(confirmed_token)
            if pending is None:
                return OperationResult(
                    success=False,
                    error="Invalid or expired confirmation token"
                )
            # Token is valid, execute the operation
            try:
                result = command.execute()
                logger.info(command.get_log_message())
                return OperationResult(success=True, data=result)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # No confirmed token, evaluate safety
        allowed, token = self.safety.evaluate(command.risk_level)
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation=command.operation_name,
                    endpoint=command.endpoint,
                    parameters=command.parameters
                )
                return OperationResult(
                    success=False,
                    requires_confirmation=True,
                    confirmation_token=token
                )
            # This should only happen for EXTREME risk
            return OperationResult(
                success=False,
                error="Operation blocked."
            )
        
        # Operation is allowed, execute it
        try:
            result = command.execute()
            logger.info(command.get_log_message())
            return OperationResult(success=True, data=result)
        except Exception as e:
            return OperationResult(success=False, error=str(e))

@dataclass
class GDBTools:
    """Tools for interacting with a File Geodatabase.
    
    Uses dependency injection for backend, safety manager, and command executor
    to enable testing and flexible execution strategies.
    """
    backend: GDBBackendProtocol
    safety: SafetyManager
    executor: CommandExecutorProtocol = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize the command executor if not provided."""
        if self.executor is None:
            self.executor = SafetyCommandExecutor(self.safety)
    
    def list_all_feature_classes(self) -> List[str]:
        return self.backend.list_all_feature_classes()

    def list_domains(self) -> List[Dict[str, Any]]:
        return self.backend.list_domains()

    def list_datasets_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        return self.backend.list_datasets_by_domain(domain_name)

    def describe(self, dataset: str) -> Dict[str, Any]:
        return self.backend.describe(dataset)

    def select(self, dataset: str, where = None, fields = [], limit=50000) -> Dict[str, Any]:
        return self.backend.select(dataset, where,fields,limit)

    def count(self, dataset: str) -> int:
        return self.backend.count(dataset)

    # Data modifications
    def insert(self, dataset: str, rows, fields, values, confirmed_token: Optional[str] = None) -> OperationResult:
        """Insert records into a dataset.
        
        Args:
            dataset: Name of the dataset
            rows: Rows to insert
            fields: Fields for the insert
            values: Values for the insert
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        command = MutatingCommand(
            operation_name="insert",
            endpoint="insert",
            risk_level=safety.RiskLevel.MEDIUM,
            execute=lambda: self.backend.insert(dataset, rows, fields, values),
            parameters={"dataset": dataset, "rows": rows, "fields": fields, "values": values},
            log_context={"Dataset": dataset, "Rows": rows, "Fields": fields, "Values": values}
        )
        return self.executor.execute(command, confirmed_token)

    def update(self, dataset: str, updates: Dict[str, Any], where: Optional[str] = None, confirmed_token: Optional[str] = None) -> OperationResult:
        """Update records in a dataset.
        
        Args:
            dataset: Name of the dataset
            updates: Dictionary of field updates
            where: Optional WHERE clause
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        command = MutatingCommand(
            operation_name="update",
            endpoint="update",
            risk_level=safety.RiskLevel.MEDIUM,
            execute=lambda: self.backend.update(dataset, updates, where),
            parameters={"dataset": dataset, "updates": updates, "where": where},
            log_context={"Dataset": dataset, "Updates": updates, "Where": where}
        )
        return self.executor.execute(command, confirmed_token)

    def delete(self, dataset: str, where: Optional[str] = None, confirmed_token: Optional[str] = None) -> OperationResult:
        """Delete records from a dataset.
        
        Args:
            dataset: Name of the dataset
            where: Optional WHERE clause
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        command = MutatingCommand(
            operation_name="delete",
            endpoint="delete",
            risk_level=safety.RiskLevel.HIGH,
            execute=lambda: self.backend.delete(dataset, where),
            parameters={"dataset": dataset, "where": where},
            log_context={"Dataset": dataset, "Where": where}
        )
        return self.executor.execute(command, confirmed_token)

    def delete_field(self, dataset: str, name: str, confirmed_token: Optional[str] = None) -> OperationResult:
        """Delete a field from a dataset.
        
        Args:
            dataset: Name of the dataset
            name: Name of the field to delete
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        command = MutatingCommand(
            operation_name="delete_field",
            endpoint="delete_field",
            risk_level=safety.RiskLevel.HIGH,
            execute=lambda: self.backend.delete_field(dataset, name),
            parameters={"dataset": dataset, "name": name},
            log_context={"Dataset": dataset, "Field": name}
        )
        return self.executor.execute(command, confirmed_token)
    # Schema
    def add_field(self, dataset: str, name: str, field_type: str, length: Optional[int] = None, confirmed_token: Optional[str] = None) -> OperationResult:
        """Add a field to a dataset.
        
        Args:
            dataset: Name of the dataset
            name: Name of the field to add
            field_type: Type of the field
            length: Optional length for the field
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        command = MutatingCommand(
            operation_name="add_field",
            endpoint="add_field",
            risk_level=safety.RiskLevel.MEDIUM,
            execute=lambda: self.backend.add_field(dataset, name, field_type, length),
            parameters={"dataset": dataset, "name": name, "field_type": field_type, "length": length},
            log_context={"Dataset": dataset, "Field": name, "Type": field_type, "Length": length}
        )
        return self.executor.execute(command, confirmed_token)


def _is_valid_fgdb_path(path: str) -> bool:
    """Return True if path is a valid file geodatabase (directory ending in .gdb)."""
    return bool(
        path
        and path.strip().lower().endswith(".gdb")
        and os.path.isdir(path)
    )


def _is_valid_sde_path(path: str) -> bool:
    """Return True if path is a valid SDE connection file (file ending in .sde)."""
    return bool(
        path
        and path.strip().lower().endswith(".sde")
        and os.path.isfile(path)
    )


def create_tools_from_env(
    connection: Connection,
    safety: Optional[SafetyManager] = None,
    executor: Optional[CommandExecutorProtocol] = None,
) -> GDBTools:
    """Factory function to create GDBTools with dependencies.

    Accepts either a file geodatabase path (directory ending in .gdb) or an
    SDE connection file path (file ending in .sde). ArcPy uses the path as the
    workspace; the .sde file is not read or parsed by this code.

    Args:
        connection: Connection object with geodatabase or SDE path
        safety: Optional SafetyManager (creates default if not provided)
        executor: Optional CommandExecutorProtocol (creates default if not provided)

    Returns:
        Configured GDBTools instance

    Raises:
        ValueError: If connection string is not a valid .gdb or .sde path
        RuntimeError: If backend initialization fails
    """
    safety_manager = safety or SafetyManager()
    workspace_path = (connection.connection_string or "").strip()
    if not workspace_path:
        raise ValueError("Connection string cannot be empty")

    if not _is_valid_fgdb_path(workspace_path) and not _is_valid_sde_path(workspace_path):
        raise ValueError(
            "Invalid workspace path: must be either (1) a file geodatabase directory "
            "ending in .gdb, or (2) an SDE connection file ending in .sde"
        )

    try:
        backend = FileGDBBackend(gdb_path=workspace_path)
        tools = GDBTools(backend=backend, safety=safety_manager)
        if executor is not None:
            tools.executor = executor
        return tools
    except Exception as ex:
        raise RuntimeError(ex) from ex