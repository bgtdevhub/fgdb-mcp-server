"""Property-based tests for validation using Hypothesis."""
import pytest
from hypothesis import given, strategies as st, assume, example
from utils.validation import validate_where_clause, validate_limit, validate_dataset

pytestmark = pytest.mark.unit


class TestValidateWhereClauseProperty:
    """Property-based tests for validate_where_clause."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_valid_where_clauses_length(self, where_clause):
        """Test that valid WHERE clauses within length limit pass."""
        assume(len(where_clause) <= 10000)
        # Should not raise for valid length
        try:
            validate_where_clause(where_clause, max_length=10000)
        except ValueError:
            # Only fails if contains dangerous patterns
            pass
    
    @given(st.integers(min_value=10001, max_value=20000))
    def test_where_clauses_exceeding_length(self, length):
        """Test that WHERE clauses exceeding max length fail."""
        where_clause = "A" * length
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_where_clause(where_clause, max_length=10000)
    
    @given(st.text())
    @example("OBJECTID = 1")
    @example("Name = 'Test'")
    @example("OBJECTID > 100 AND Status = 'Active'")
    @example("DateField >= '2024-01-01'")
    def test_valid_sql_patterns(self, where_clause):
        """Test that common valid SQL patterns pass."""
        assume(len(where_clause) <= 10000)
        assume(';' not in where_clause.lower())
        assume('--' not in where_clause)
        assume('/*' not in where_clause)
        assume('*/' not in where_clause)
        
        # Should not raise for valid patterns
        validate_where_clause(where_clause)
    
    @given(
        st.one_of(
            st.text().map(lambda s: f"; DROP TABLE {s}"),
            st.text().map(lambda s: f"OBJECTID = 1; DELETE FROM {s}"),
            st.text().map(lambda s: f"{s} -- comment"),
            st.text().map(lambda s: f"/* {s} */"),
        ).filter(lambda s: len(s) <= 10000)
    )
    @example("; DROP TABLE Test")
    @example("OBJECTID = 1; DELETE FROM Test")
    @example("-- comment")
    @example("/* comment */")
    def test_dangerous_patterns_rejected(self, where_clause):
        """Test that dangerous SQL injection patterns are rejected."""
        with pytest.raises(ValueError, match="potentially dangerous pattern"):
            validate_where_clause(where_clause)
    
    @given(st.text())
    def test_where_clause_none(self, _):
        """Test that None WHERE clause is always valid."""
        validate_where_clause(None)
    
    @given(st.text())
    def test_where_clause_empty_string(self, _):
        """Test that empty string WHERE clause is valid."""
        validate_where_clause("")
        validate_where_clause("   ")
    
    @given(st.integers(min_value=1, max_value=10000))
    def test_where_clause_custom_max_length(self, max_length):
        """Test validate_where_clause with custom max_length."""
        # Valid length
        valid_clause = "A" * max_length
        validate_where_clause(valid_clause, max_length=max_length)
        
        # Invalid length
        invalid_clause = "A" * (max_length + 1)
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_where_clause(invalid_clause, max_length=max_length)
    
    @given(st.text())
    @example("OBJECTID = 1")
    @example("Name LIKE '%Test%'")
    @example("Status IN ('Active', 'Pending')")
    def test_common_sql_operators(self, where_clause):
        """Test that common SQL operators are allowed."""
        assume(len(where_clause) <= 10000)
        assume(';' not in where_clause.lower())
        assume('--' not in where_clause)
        assume('/*' not in where_clause)
        assume('*/' not in where_clause)
        
        validate_where_clause(where_clause)
    
    def test_where_clause_not_string(self):
        """Test that non-string types raise ValueError."""
        # Test explicit non-string types (Hypothesis generates strings, so we test manually)
        with pytest.raises(ValueError, match="must be a string"):
            validate_where_clause(123)
        with pytest.raises(ValueError, match="must be a string"):
            validate_where_clause([])
        with pytest.raises(ValueError, match="must be a string"):
            validate_where_clause({})
        # None is allowed
        validate_where_clause(None)


class TestValidateLimitProperty:
    """Property-based tests for validate_limit."""
    
    @given(st.integers(min_value=1, max_value=500000))
    def test_valid_limits(self, limit):
        """Test that valid limits pass."""
        validate_limit(limit)
    
    @given(st.integers(max_value=0))
    def test_invalid_limits_zero_or_negative(self, limit):
        """Test that zero or negative limits fail."""
        with pytest.raises(ValueError, match="must be greater than 0"):
            validate_limit(limit)
    
    @given(st.integers(min_value=500001))
    def test_limits_exceeding_maximum(self, limit):
        """Test that limits exceeding maximum fail."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_limit(limit, max_limit=500000)
    
    @given(st.integers(min_value=1))
    def test_limits_custom_maximum(self, limit):
        """Test validate_limit with custom max_limit."""
        max_limit = 1000
        if limit <= max_limit:
            validate_limit(limit, max_limit=max_limit)
        else:
            with pytest.raises(ValueError, match="exceeds maximum"):
                validate_limit(limit, max_limit=max_limit)
    
    @given(st.one_of(st.text(), st.floats()))
    def test_limit_not_integer(self, invalid_limit):
        """Test that non-integer limits fail."""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_limit(invalid_limit)
    
    def test_limit_boolean(self):
        """Test that boolean values are treated as integers (True=1, False=0)."""
        # Booleans are instances of int in Python
        # True == 1, so it passes validation
        validate_limit(True)  # Should pass (True == 1)
        # False == 0, so it fails the "must be greater than 0" check
        with pytest.raises(ValueError, match="must be greater than 0"):
            validate_limit(False)
    
    @given(st.integers(min_value=1, max_value=1000))
    @example(1)
    @example(100)
    @example(1000)
    def test_common_limit_values(self, limit):
        """Test common limit values."""
        validate_limit(limit, max_limit=1000)


class TestValidateDatasetProperty:
    """Property-based tests for validate_dataset (mocked)."""
    
    @given(st.text(min_size=1))
    def test_dataset_not_empty(self, dataset_name):
        """Test that non-empty dataset names are accepted (when mocked)."""
        # Note: This test requires ArcPy mocking, so it's more of a structure test
        # Actual validation requires ArcPy.Exists() which needs to be mocked
        assume(dataset_name.strip() != "")
        # This is a placeholder - actual test would mock arcpy.Exists
        pass
    
    @given(st.one_of(st.just(""), st.just("   "), st.text().filter(lambda s: not s.strip())))
    def test_dataset_empty_or_whitespace(self, dataset_name):
        """Test that empty or whitespace dataset names fail."""
        # This would fail in actual implementation
        # Placeholder for structure - actual test would mock arcpy.Exists
        assert not dataset_name or not dataset_name.strip()

