"""Unit tests for configuration parsing and management."""
import pytest
import os
from unittest.mock import patch
from utils.config import ServerConfig, get_config, set_config


class TestServerConfig:
    """Tests for ServerConfig class."""
    
    def test_server_config_defaults(self):
        """Test ServerConfig default values."""
        config = ServerConfig()
        
        assert config.max_select_limit == 50000
        assert config.log_file == "fgdb_server.log"
        assert config.log_level == "INFO"
        assert config.log_max_bytes == 10 * 1024 * 1024
        assert config.log_backup_count == 5
        assert config.api_version == "v1"
        assert config.supported_api_versions == ["v1"]
        assert config.features == {"experimental": False}
    
    def test_is_feature_enabled_default(self):
        """Test is_feature_enabled with default features."""
        config = ServerConfig()
        
        assert config.is_feature_enabled("experimental") is False
        assert config.is_feature_enabled("nonexistent") is False
    
    def test_is_feature_enabled_custom(self):
        """Test is_feature_enabled with custom features."""
        config = ServerConfig()
        config.features = {
            "experimental": True,
            "new_feature": True,
            "disabled_feature": False
        }
        
        assert config.is_feature_enabled("experimental") is True
        assert config.is_feature_enabled("new_feature") is True
        assert config.is_feature_enabled("disabled_feature") is False
        assert config.is_feature_enabled("nonexistent") is False
    
    def test_is_api_version_supported(self):
        """Test is_api_version_supported method."""
        config = ServerConfig()
        config.supported_api_versions = ["v1", "v2"]
        
        assert config.is_api_version_supported("v1") is True
        assert config.is_api_version_supported("v2") is True
        assert config.is_api_version_supported("v3") is False
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_defaults(self):
        """Test from_env with no environment variables (defaults)."""
        config = ServerConfig.from_env()
        
        assert config.max_select_limit == 50000
        assert config.log_file == "fgdb_server.log"
        assert config.log_level == "INFO"
        assert config.log_max_bytes == 10 * 1024 * 1024
        assert config.log_backup_count == 5
        assert config.api_version == "v1"
        assert config.supported_api_versions == ["v1"]
        assert config.features == {"experimental": False}
    
    @patch.dict(os.environ, {
        "FGDB_MAX_SELECT_LIMIT": "100000",
        "FGDB_LOG_FILE": "custom.log",
        "FGDB_LOG_LEVEL": "DEBUG",
        "FGDB_LOG_MAX_BYTES": "20971520",
        "FGDB_LOG_BACKUP_COUNT": "10",
        "FGDB_API_VERSION": "v2",
        "FGDB_SUPPORTED_VERSIONS": "v1,v2,v3",
        "FGDB_FEATURE_EXPERIMENTAL": "true"
    })
    def test_from_env_custom_values(self):
        """Test from_env with custom environment variables."""
        config = ServerConfig.from_env()
        
        assert config.max_select_limit == 100000
        assert config.log_file == "custom.log"
        assert config.log_level == "DEBUG"
        assert config.log_max_bytes == 20971520
        assert config.log_backup_count == 10
        assert config.api_version == "v2"
        assert config.supported_api_versions == ["v1", "v2", "v3"]
        assert config.features == {"experimental": True}
    
    @patch.dict(os.environ, {
        "FGDB_FEATURE_EXPERIMENTAL": "false"
    })
    def test_from_env_feature_flags_false(self):
        """Test from_env with feature flag set to false."""
        config = ServerConfig.from_env()
        assert config.features == {"experimental": False}
    
    @patch.dict(os.environ, {
        "FGDB_FEATURE_EXPERIMENTAL": "True"
    })
    def test_from_env_feature_flags_case_insensitive(self):
        """Test from_env with feature flag case insensitive."""
        config = ServerConfig.from_env()
        assert config.features == {"experimental": True}
    
    @patch.dict(os.environ, {
        "FGDB_SUPPORTED_VERSIONS": "v1, v2 , v3"
    })
    def test_from_env_api_versions_with_spaces(self):
        """Test from_env with API versions containing spaces."""
        config = ServerConfig.from_env()
        assert config.supported_api_versions == ["v1", "v2", "v3"]
    
    @patch.dict(os.environ, {
        "FGDB_SUPPORTED_VERSIONS": "v1"
    })
    def test_from_env_single_api_version(self):
        """Test from_env with single API version."""
        config = ServerConfig.from_env()
        assert config.supported_api_versions == ["v1"]
    
    @patch.dict(os.environ, {
        "FGDB_MAX_SELECT_LIMIT": "invalid"
    })
    def test_from_env_invalid_integer(self):
        """Test from_env with invalid integer value."""
        with pytest.raises(ValueError):
            ServerConfig.from_env()
    
    def test_setup_logging(self):
        """Test setup_logging method."""
        config = ServerConfig()
        config.log_file = "test_log.log"
        config.log_level = "DEBUG"
        
        # Should not raise an exception
        config.setup_logging()
        
        # Verify log file would be created (directory)
        import logging
        assert logging.getLogger().level <= logging.DEBUG


class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_config_returns_singleton(self):
        """Test that get_config returns the same instance."""
        # Reset global config
        set_config(None)
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_config_uses_env(self):
        """Test that get_config uses environment variables."""
        # Reset global config
        set_config(None)
        
        with patch.dict(os.environ, {"FGDB_MAX_SELECT_LIMIT": "75000"}):
            config = get_config()
            assert config.max_select_limit == 75000
    
    def test_set_config(self):
        """Test set_config function."""
        custom_config = ServerConfig()
        custom_config.max_select_limit = 99999
        
        set_config(custom_config)
        retrieved = get_config()
        
        assert retrieved is custom_config
        assert retrieved.max_select_limit == 99999


class TestConfigEdgeCases:
    """Tests for configuration edge cases."""
    
    @patch.dict(os.environ, {
        "FGDB_LOG_LEVEL": "INVALID_LEVEL"
    })
    def test_from_env_invalid_log_level(self):
        """Test from_env with invalid log level."""
        config = ServerConfig.from_env()
        # Should not raise, but log level might default
        assert config.log_level == "INVALID_LEVEL"  # Stored as-is, validated in setup_logging
    
    @patch.dict(os.environ, {
        "FGDB_SUPPORTED_VERSIONS": ""
    })
    def test_from_env_empty_versions(self):
        """Test from_env with empty supported versions."""
        config = ServerConfig.from_env()
        assert config.supported_api_versions == [""]
    
    @patch.dict(os.environ, {
        "FGDB_FEATURE_EXPERIMENTAL": "yes"  # Not "true"
    })
    def test_from_env_feature_flag_not_true(self):
        """Test from_env with feature flag not exactly 'true'."""
        config = ServerConfig.from_env()
        assert config.features == {"experimental": False}  # Only "true" (case-insensitive) enables
    
    def test_config_custom_features(self):
        """Test ServerConfig with custom features."""
        config = ServerConfig()
        config.features = {
            "feature1": True,
            "feature2": False,
            "feature3": True
        }
        
        assert config.is_feature_enabled("feature1") is True
        assert config.is_feature_enabled("feature2") is False
        assert config.is_feature_enabled("feature3") is True

