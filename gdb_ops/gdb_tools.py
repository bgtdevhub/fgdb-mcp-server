from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from dtos.requestobjects import Connection, OperationResult
from utils import safety
from utils.safety import SafetyManager
from .gdb import FileGDBBackend

logger = logging.getLogger(__name__)

Backend = FileGDBBackend

@dataclass
class GDBTools:
    backend: Backend
    safety: safety.SafetyManager
    def list_all_feature_classes(self) -> List[str]:
        return self.backend.list_all_feature_classes()

    def describe(self, dataset: str) -> Dict[str, Any]:
        return self.backend.describe(dataset)

    def select(self, dataset: str, where = None, fields = [], limit=50000) -> Dict[Dict[str, Any]]:
        return self.backend.select(dataset, where,fields,limit)

    def select_by_geometry(self, dataset: str, overlap_type: str, selection_type: str, outputLayer:str) -> int:
        allowed, token = self.safety.evaluate(safety.RiskLevel.LOW)
        if not allowed:
            raise PermissionError(f"Operation blocked. Confirm token: {token}")
        return self.backend.select_by_geometry(dataset, overlap_type, selection_type, outputLayer)

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
                result = self.backend.insert(dataset, rows, fields, values)
                logger.info(f"Operation: insert, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Rows: {rows}, Fields: {fields}, Values: {values}")
                return OperationResult(success=True, data=result)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # No confirmed token, evaluate safety
        allowed, token = self.safety.evaluate(safety.RiskLevel.MEDIUM)
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation="insert",
                    endpoint="insert",
                    parameters={"dataset": dataset, "rows": rows, "fields": fields, "values": values}
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
            result = self.backend.insert(dataset, rows, fields, values)
            logger.info(f"Operation: insert, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Rows: {rows}, Fields: {fields}, Values: {values}")
            return OperationResult(success=True, data=result)
        except Exception as e:
            return OperationResult(success=False, error=str(e))

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
                result = self.backend.update(dataset, updates, where)
                logger.info(f"Operation: update, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Updates: {updates}, Where: {where}")
                return OperationResult(success=True, data=result)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # No confirmed token, evaluate safety
        allowed, token = self.safety.evaluate(safety.RiskLevel.MEDIUM)
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation="update",
                    endpoint="update",
                    parameters={"dataset": dataset, "updates": updates, "where": where}
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
            result = self.backend.update(dataset, updates, where)
            logger.info(f"Operation: update, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Updates: {updates}, Where: {where}")
            return OperationResult(success=True, data=result)
        except Exception as e:
            return OperationResult(success=False, error=str(e))

    def delete(self, dataset: str, where: Optional[str] = None, confirmed_token: Optional[str] = None) -> OperationResult:
        """Delete records from a dataset.
        
        Args:
            dataset: Name of the dataset
            where: Optional WHERE clause
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
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
                result = self.backend.delete(dataset, where)
                logger.info(f"Operation: delete, Risk: {safety.RiskLevel.HIGH.value}, Dataset: {dataset}, Where: {where}")
                return OperationResult(success=True, data=result)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # No confirmed token, evaluate safety
        allowed, token = self.safety.evaluate(safety.RiskLevel.HIGH)
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation="delete",
                    endpoint="delete",
                    parameters={"dataset": dataset, "where": where}
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
            result = self.backend.delete(dataset, where)
            logger.info(f"Operation: delete, Risk: {safety.RiskLevel.HIGH.value}, Dataset: {dataset}, Where: {where}")
            return OperationResult(success=True, data=result)
        except Exception as e:
            return OperationResult(success=False, error=str(e))

    def delete_field(self, dataset: str, name: str, confirmed_token: Optional[str] = None) -> OperationResult:
        """Delete a field from a dataset.
        
        Args:
            dataset: Name of the dataset
            name: Name of the field to delete
            confirmed_token: Token from confirmation if this is a confirmed operation
            
        Returns:
            OperationResult with success status or confirmation requirements
        """
        allowed, token = self.safety.evaluate(safety.RiskLevel.HIGH)
        
        # If a confirmed token is provided, validate it
        if confirmed_token:
            pending = self.safety.confirm_with_token(confirmed_token)
            if pending is None:
                return OperationResult(
                    success=False,
                    error="Invalid or expired confirmation token"
                )
            # Token is valid, proceed with operation
            allowed = True
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation="delete_field",
                    endpoint="delete_field",
                    parameters={"dataset": dataset, "name": name}
                )
                return OperationResult(
                    success=False,
                    requires_confirmation=True,
                    confirmation_token=token
                )
            return OperationResult(
                success=False,
                error="Operation blocked. Enable unsafe mode first."
            )
        
        # Operation is allowed, execute it
        try:
            self.backend.delete_field(dataset, name)
            logger.info(f"Operation: delete_field, Risk: {safety.RiskLevel.HIGH.value}, Dataset: {dataset}, Field: {name}")
            return OperationResult(success=True)
        except Exception as e:
            return OperationResult(success=False, error=str(e))
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
                self.backend.add_field(dataset, name, field_type, length)
                logger.info(f"Operation: add_field, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Field: {name}, Type: {field_type}, Length: {length}")
                return OperationResult(success=True)
            except Exception as e:
                return OperationResult(success=False, error=str(e))
        
        # No confirmed token, evaluate safety
        allowed, token = self.safety.evaluate(safety.RiskLevel.MEDIUM)
        
        if not allowed:
            if token:
                # Register this operation as pending
                self.safety.register_pending_operation(
                    token=token,
                    operation="add_field",
                    endpoint="add_field",
                    parameters={"dataset": dataset, "name": name, "field_type": field_type, "length": length}
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
            self.backend.add_field(dataset, name, field_type, length)
            logger.info(f"Operation: add_field, Risk: {safety.RiskLevel.MEDIUM.value}, Dataset: {dataset}, Field: {name}, Type: {field_type}, Length: {length}")
            return OperationResult(success=True)
        except Exception as e:
            return OperationResult(success=False, error=str(e))


def create_tools_from_env(connection:Connection, safety: Optional[SafetyManager] = None) -> GDBTools:
    safety_manager = safety or SafetyManager()
    gdb_path = connection.connection_string
    
    print(f"gdb_path: {gdb_path}")
    if gdb_path or gdb_path == "":
        try:
            backend = FileGDBBackend(gdb_path=gdb_path)
            return GDBTools(backend=backend, safety=safety_manager)

        except Exception as ex:
            raise RuntimeError(ex)