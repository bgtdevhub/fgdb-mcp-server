from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import uuid

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class PendingOperation:
    """Stores information about a pending operation waiting for confirmation."""
    operation: str
    endpoint: str
    parameters: Dict[str, Any]
    token: str


class SafetyManager:
    def __init__(self) -> None:
        self._pending_operations: Dict[str, PendingOperation] = {}

    def evaluate(self, risk: RiskLevel) -> tuple[bool, Optional[str]]:
        """Evaluate if an operation with given risk level is allowed.
        
        Returns:
            tuple[bool, Optional[str]]: (allowed, token)
                - If allowed=True: operation can proceed, token is None
                - If allowed=False and token is not None: operation needs confirmation with this token
                - If allowed=False and token is None: operation is blocked
        """
        if risk == RiskLevel.LOW:
            return True, None
        
        if risk == RiskLevel.MEDIUM:
            # Always require confirmation for medium-risk operations
            token = str(uuid.uuid4())
            return False, token
        
        if risk == RiskLevel.HIGH:
            # Always require confirmation for high-risk operations
            token = str(uuid.uuid4())
            return False, token
        
        # EXTREME or any other risk level
        return False, None

    def register_pending_operation(
        self, 
        token: str, 
        operation: str, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> None:
        """Register a pending operation that requires confirmation."""
        self._pending_operations[token] = PendingOperation(
            operation=operation,
            endpoint=endpoint,
            parameters=parameters,
            token=token
        )

    def validate_token(self, token: str) -> Optional[PendingOperation]:
        """Validate a token without consuming it.
        
        Returns:
            PendingOperation if token is valid, None otherwise
        """
        return self._pending_operations.get(token)

    def confirm_with_token(self, token: str) -> Optional[PendingOperation]:
        """Confirm and consume an operation with a token.
        
        Returns:
            PendingOperation if token is valid, None otherwise
        """
        pending = self._pending_operations.pop(token, None)
        return pending

    def reset_confirmation(self) -> None:
        """Clear all pending operations."""
        self._pending_operations.clear()