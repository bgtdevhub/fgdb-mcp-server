"""Unit tests for SafetyManager and related safety components."""
import pytest
from utils.safety import SafetyManager, RiskLevel, PendingOperation

pytestmark = pytest.mark.unit


class TestRiskLevel:
    """Tests for RiskLevel enum."""
    
    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.EXTREME == "extreme"
    
    def test_risk_level_string_representation(self):
        """Test RiskLevel string representation."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        # For str, Enum, the enum itself can be compared to string
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"


class TestPendingOperation:
    """Tests for PendingOperation dataclass."""
    
    def test_pending_operation_creation(self):
        """Test creating a pending operation."""
        pending = PendingOperation(
            operation="insert",
            endpoint="insert",
            parameters={"dataset": "Test", "rows": 1},
            token="test-token-123"
        )
        
        assert pending.operation == "insert"
        assert pending.endpoint == "insert"
        assert pending.parameters == {"dataset": "Test", "rows": 1}
        assert pending.token == "test-token-123"


class TestSafetyManager:
    """Unit tests for SafetyManager class."""
    
    def test_safety_manager_initialization(self):
        """Test SafetyManager initialization."""
        manager = SafetyManager()
        assert manager._pending_operations == {}
    
    def test_evaluate_low_risk(self):
        """Test evaluating low risk operation."""
        manager = SafetyManager()
        allowed, token = manager.evaluate(RiskLevel.LOW)
        
        assert allowed is True
        assert token is None
    
    def test_evaluate_medium_risk(self):
        """Test evaluating medium risk operation."""
        manager = SafetyManager()
        allowed, token = manager.evaluate(RiskLevel.MEDIUM)
        
        assert allowed is False
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_evaluate_high_risk(self):
        """Test evaluating high risk operation."""
        manager = SafetyManager()
        allowed, token = manager.evaluate(RiskLevel.HIGH)
        
        assert allowed is False
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_evaluate_extreme_risk(self):
        """Test evaluating extreme risk operation."""
        manager = SafetyManager()
        allowed, token = manager.evaluate(RiskLevel.EXTREME)
        
        assert allowed is False
        assert token is None
    
    def test_evaluate_generates_unique_tokens(self):
        """Test that evaluate generates unique tokens for each call."""
        manager = SafetyManager()
        _, token1 = manager.evaluate(RiskLevel.MEDIUM)
        _, token2 = manager.evaluate(RiskLevel.MEDIUM)
        
        assert token1 != token2
        assert token1 is not None
        assert token2 is not None
    
    def test_register_pending_operation(self):
        """Test registering a pending operation."""
        manager = SafetyManager()
        token = "test-token-123"
        parameters = {"dataset": "Test", "rows": 1, "fields": [], "values": []}
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters=parameters
        )
        
        assert token in manager._pending_operations
        pending = manager._pending_operations[token]
        assert pending.operation == "insert"
        assert pending.endpoint == "insert"
        assert pending.parameters == parameters
        assert pending.token == token
    
    def test_register_pending_operation_overwrites_existing(self):
        """Test that registering with same token overwrites existing operation."""
        manager = SafetyManager()
        token = "test-token-123"
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters={"dataset": "Test1"}
        )
        
        manager.register_pending_operation(
            token=token,
            operation="update",
            endpoint="update",
            parameters={"dataset": "Test2"}
        )
        
        pending = manager._pending_operations[token]
        assert pending.operation == "update"
        assert pending.parameters == {"dataset": "Test2"}
    
    def test_validate_token_valid(self):
        """Test validating a valid token."""
        manager = SafetyManager()
        token = "test-token-123"
        parameters = {"dataset": "Test", "rows": 1}
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters=parameters
        )
        
        pending = manager.validate_token(token)
        assert pending is not None
        assert pending.operation == "insert"
        assert pending.token == token
        # Token should still exist (not consumed)
        assert token in manager._pending_operations
    
    def test_validate_token_invalid(self):
        """Test validating an invalid token."""
        manager = SafetyManager()
        pending = manager.validate_token("invalid-token")
        assert pending is None
    
    def test_validate_token_not_consumed(self):
        """Test that validate_token does not consume the token."""
        manager = SafetyManager()
        token = "test-token-123"
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters={}
        )
        
        # Validate multiple times
        pending1 = manager.validate_token(token)
        pending2 = manager.validate_token(token)
        
        assert pending1 is not None
        assert pending2 is not None
        assert token in manager._pending_operations
    
    def test_confirm_with_token_valid(self):
        """Test confirming with a valid token."""
        manager = SafetyManager()
        token = "test-token-123"
        parameters = {"dataset": "Test", "rows": 1}
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters=parameters
        )
        
        pending = manager.confirm_with_token(token)
        assert pending is not None
        assert pending.operation == "insert"
        # Token should be consumed (removed)
        assert token not in manager._pending_operations
    
    def test_confirm_with_token_invalid(self):
        """Test confirming with an invalid token."""
        manager = SafetyManager()
        pending = manager.confirm_with_token("invalid-token")
        assert pending is None
    
    def test_confirm_with_token_consumes_token(self):
        """Test that confirm_with_token consumes the token."""
        manager = SafetyManager()
        token = "test-token-123"
        
        manager.register_pending_operation(
            token=token,
            operation="insert",
            endpoint="insert",
            parameters={}
        )
        
        pending1 = manager.confirm_with_token(token)
        pending2 = manager.confirm_with_token(token)
        
        assert pending1 is not None
        assert pending2 is None  # Token already consumed
        assert token not in manager._pending_operations
    
    def test_reset_confirmation(self):
        """Test resetting all pending operations."""
        manager = SafetyManager()
        
        # Register multiple operations
        manager.register_pending_operation(
            token="token1",
            operation="insert",
            endpoint="insert",
            parameters={}
        )
        manager.register_pending_operation(
            token="token2",
            operation="delete",
            endpoint="delete",
            parameters={}
        )
        
        assert len(manager._pending_operations) == 2
        
        manager.reset_confirmation()
        
        assert len(manager._pending_operations) == 0
        assert manager.validate_token("token1") is None
        assert manager.validate_token("token2") is None
    
    def test_reset_confirmation_empty(self):
        """Test resetting when no operations are pending."""
        manager = SafetyManager()
        manager.reset_confirmation()
        assert len(manager._pending_operations) == 0
    
    def test_multiple_operations_same_manager(self):
        """Test managing multiple pending operations."""
        manager = SafetyManager()
        
        token1 = "token1"
        token2 = "token2"
        
        manager.register_pending_operation(
            token=token1,
            operation="insert",
            endpoint="insert",
            parameters={"dataset": "Test1"}
        )
        manager.register_pending_operation(
            token=token2,
            operation="delete",
            endpoint="delete",
            parameters={"dataset": "Test2"}
        )
        
        assert len(manager._pending_operations) == 2
        assert manager.validate_token(token1) is not None
        assert manager.validate_token(token2) is not None
        
        # Confirm one, other should still exist
        manager.confirm_with_token(token1)
        assert token1 not in manager._pending_operations
        assert token2 in manager._pending_operations

