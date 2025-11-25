from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class Connection:
    connection_string: Optional[str] = None

class OperationResult(BaseModel):
    """Result of an operation that may require confirmation."""
    success: bool
    data: Optional[Any] = None
    requires_confirmation: bool = False
    confirmation_token: Optional[str] = None
    error: Optional[str] = None