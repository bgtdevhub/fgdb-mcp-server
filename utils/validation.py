"""Validation utilities for geodatabase operations."""
from typing import Optional
import re

try:
    import arcpy  # type: ignore
    ARCPY_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    ARCPY_AVAILABLE = False


def validate_dataset(dataset: str, workspace: Optional[str] = None) -> None:
    """Validate that dataset is not None/empty and exists in the geodatabase.
    
    Args:
        dataset: Name of the dataset to validate
        workspace: Optional workspace path. If provided, sets arcpy.env.workspace before validation.
        
    Raises:
        ValueError: If dataset is invalid or doesn't exist
        RuntimeError: If ArcPy is not available
    """
    if not dataset or not isinstance(dataset, str) or not dataset.strip():
        raise ValueError("Dataset name cannot be None or empty")
    
    if not ARCPY_AVAILABLE:
        raise RuntimeError("ArcPy is required for dataset validation")
    
    # Set workspace if provided
    if workspace is not None:
        arcpy.env.workspace = workspace
    
    if not arcpy.Exists(dataset):
        raise ValueError(f"Dataset '{dataset}' does not exist in the geodatabase")


def validate_where_clause(where: Optional[str], max_length: int = 10000) -> None:
    """Validate WHERE clause for length and basic character safety.
    
    Args:
        where: WHERE clause string to validate (can be None)
        max_length: Maximum allowed length for WHERE clause (default: 10000)
        
    Raises:
        ValueError: If WHERE clause is invalid or contains dangerous patterns
    """
    if where is None:
        return
    
    if not isinstance(where, str):
        raise ValueError("WHERE clause must be a string or None")
    
    if len(where) > max_length:
        raise ValueError(f"WHERE clause exceeds maximum length of {max_length} characters")
    
    if not where.strip():
        # Empty string is treated as None
        return
    
    # Basic validation: check for potentially dangerous patterns
    # Allow common SQL operators and characters, but block obvious injection attempts
    # Note: ArcPy will handle the actual SQL parsing, this is just basic input validation
    dangerous_patterns = [
        r';\s*(drop|delete|truncate|alter|create|exec|execute)',
        r'--',
        r'/\*',
        r'\*/',
    ]
    where_lower = where.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, where_lower, re.IGNORECASE):
            raise ValueError(f"WHERE clause contains potentially dangerous pattern: {pattern}")


def validate_limit(limit: int, max_limit: int = 500000) -> None:
    """Validate that limit is within acceptable bounds.
    
    Args:
        limit: Limit value to validate
        max_limit: Maximum allowed limit value (default: 500000)
        
    Raises:
        ValueError: If limit is invalid or exceeds maximum
    """
    if not isinstance(limit, int):
        raise ValueError("Limit must be an integer")
    
    if limit < 1:
        raise ValueError("Limit must be greater than 0")
    
    if limit > max_limit:
        raise ValueError(f"Limit {limit} exceeds maximum allowed limit of {max_limit}")

