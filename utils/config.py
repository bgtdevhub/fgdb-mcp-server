"""Configuration management for FGDB server."""
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
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
    
    # Safety settings
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        return cls(
            max_select_limit=int(os.getenv("FGDB_MAX_SELECT_LIMIT", "50000")),
            log_file=os.getenv("FGDB_LOG_FILE", "fgdb_server.log"),
            log_level=os.getenv("FGDB_LOG_LEVEL", "INFO"),
            log_max_bytes=int(os.getenv("FGDB_LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            log_backup_count=int(os.getenv("FGDB_LOG_BACKUP_COUNT", "5")),
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

