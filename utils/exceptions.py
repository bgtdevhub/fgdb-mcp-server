"""Custom exception classes for FGDB server."""


class FGDBError(Exception):
    """Base exception for all FGDB server errors."""
    pass


class DatabaseConnectionError(FGDBError):
    """Raised when there's an error establishing or using a database connection."""
    pass


class OperationBlockedError(FGDBError):
    """Raised when an operation is blocked by safety checks."""
    pass


class ValidationError(FGDBError):
    """Raised when input validation fails."""
    pass


class ArcPyError(FGDBError):
    """Raised when ArcPy is required but unavailable or encounters an error."""
    pass


class ConfigurationError(FGDBError):
    """Raised when there's a configuration error."""
    pass

