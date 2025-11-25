"""Configuration management for FGDB server."""
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List
from logging.handlers import RotatingFileHandler


@dataclass
class ServerConfig:
    """Server configuration settings."""
    # Database settings
    max_select_limit: int = 50000
    
    # Logging settings
    log_file: str = "fgdb_server.log"
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # API Versioning
    api_version: str = "v1"
    supported_api_versions: List[str] = field(default_factory=lambda: ["v1"])
    
    # Feature Flags (for future experimental features)
    features: Dict[str, bool] = field(default_factory=lambda: {
        "experimental": False,
    })
    
    # Safety settings
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.features.get(feature_name, False)
    
    def is_api_version_supported(self, version: str) -> bool:
        """Check if an API version is supported.
        
        Args:
            version: API version to check (e.g., "v1")
            
        Returns:
            True if version is supported, False otherwise
        """
        return version in self.supported_api_versions
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        # Parse feature flags from environment (only experimental for now)
        features = {
            "experimental": os.getenv("FGDB_FEATURE_EXPERIMENTAL", "false").lower() == "true",
        }
        
        # Parse supported API versions
        supported_versions_str = os.getenv("FGDB_SUPPORTED_VERSIONS", "v1")
        supported_versions = [v.strip() for v in supported_versions_str.split(",")]
        
        return cls(
            max_select_limit=int(os.getenv("FGDB_MAX_SELECT_LIMIT", "50000")),
            log_file=os.getenv("FGDB_LOG_FILE", "fgdb_server.log"),
            log_level=os.getenv("FGDB_LOG_LEVEL", "INFO"),
            log_max_bytes=int(os.getenv("FGDB_LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            log_backup_count=int(os.getenv("FGDB_LOG_BACKUP_COUNT", "5")),
            api_version=os.getenv("FGDB_API_VERSION", "v1"),
            supported_api_versions=supported_versions,
            features=features,
        )
    
    def setup_logging(self) -> None:
        """Configure logging based on this configuration."""
        handlers = []
        
        # File handler with rotation
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                self.log_file,
                maxBytes=self.log_max_bytes,
                backupCount=self.log_backup_count
            )
        )
        
        # Set log level
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True  # Override any existing configuration
        )


# Global configuration instance
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ServerConfig.from_env()
    return _config


def set_config(config: ServerConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config

