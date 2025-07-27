"""
Configuration management for IB connection testing.

Supports multiple configuration sources with priority:
1. Command line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Default values (lowest priority)
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class IBConfig:
    """Interactive Brokers connection configuration."""
    
    # Connection settings
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    account: str = ""
    
    # Test settings
    connection_timeout: int = 30
    data_timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 5
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Output settings
    verbose: bool = False
    json_output: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IBConfig":
        """Create config from dictionary, ignoring unknown keys."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class ConfigLoader:
    """Loads and validates IB configuration from multiple sources."""
    
    DEFAULT_CONFIG_FILES = [
        "ib_config.json",
        "foxtrot_config.json",
        ".foxtrot/ib_config.json",
        os.path.expanduser("~/.foxtrot/ib_config.json")
    ]
    
    ENV_PREFIX = "FOXTROT_IB_"
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize config loader.
        
        Args:
            config_file: Optional path to specific config file
        """
        self.config_file = config_file
        self._env_mapping = {
            "HOST": "host",
            "PORT": "port", 
            "CLIENT_ID": "client_id",
            "ACCOUNT": "account",
            "CONNECTION_TIMEOUT": "connection_timeout",
            "DATA_TIMEOUT": "data_timeout",
            "RETRY_ATTEMPTS": "retry_attempts",
            "RETRY_DELAY": "retry_delay",
            "LOG_LEVEL": "log_level",
            "LOG_FILE": "log_file",
            "VERBOSE": "verbose",
            "JSON_OUTPUT": "json_output"
        }
    
    def load(self, **overrides) -> IBConfig:
        """Load configuration from all sources.
        
        Args:
            **overrides: Direct configuration overrides (highest priority)
            
        Returns:
            Validated IBConfig instance
        """
        # Start with defaults
        config_data = {}
        
        # Load from file
        file_config = self._load_from_file()
        if file_config:
            config_data.update(file_config)
        
        # Load from environment
        env_config = self._load_from_env()
        config_data.update(env_config)
        
        # Apply overrides
        config_data.update(overrides)
        
        # Create and validate config
        config = IBConfig.from_dict(config_data)
        self._validate_config(config)
        
        return config
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_files = [self.config_file] if self.config_file else self.DEFAULT_CONFIG_FILES
        
        for config_file in config_files:
            if not config_file:
                continue
                
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                    
                    # Support nested structure
                    if "ib" in data:
                        data = data["ib"]
                    elif "interactive_brokers" in data:
                        data = data["interactive_brokers"]
                    
                    return data
                except (json.JSONDecodeError, IOError) as e:
                    raise ConfigError(f"Failed to load config file {config_file}: {e}")
        
        return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config_data = {}
        
        for env_key, config_key in self._env_mapping.items():
            env_var = f"{self.ENV_PREFIX}{env_key}"
            value = os.getenv(env_var)
            
            if value is not None:
                # Type conversion
                config_data[config_key] = self._convert_env_value(config_key, value)
        
        return config_data
    
    def _convert_env_value(self, key: str, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean fields
        if key in ["verbose", "json_output"]:
            return value.lower() in ("true", "1", "yes", "on")
        
        # Integer fields
        if key in ["port", "client_id", "connection_timeout", "data_timeout", 
                  "retry_attempts", "retry_delay"]:
            try:
                return int(value)
            except ValueError:
                raise ConfigError(f"Invalid integer value for {key}: {value}")
        
        # String fields (no conversion needed)
        return value
    
    def _validate_config(self, config: IBConfig) -> None:
        """Validate configuration values."""
        errors = []
        
        # Validate port range
        if not (1 <= config.port <= 65535):
            errors.append(f"Port must be between 1 and 65535, got {config.port}")
        
        # Validate client ID
        if config.client_id < 0:
            errors.append(f"Client ID must be non-negative, got {config.client_id}")
        
        # Validate timeouts
        if config.connection_timeout <= 0:
            errors.append(f"Connection timeout must be positive, got {config.connection_timeout}")
        
        if config.data_timeout <= 0:
            errors.append(f"Data timeout must be positive, got {config.data_timeout}")
        
        # Validate retry settings
        if config.retry_attempts < 0:
            errors.append(f"Retry attempts must be non-negative, got {config.retry_attempts}")
        
        if config.retry_delay < 0:
            errors.append(f"Retry delay must be non-negative, got {config.retry_delay}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level.upper() not in valid_levels:
            errors.append(f"Log level must be one of {valid_levels}, got {config.log_level}")
        
        if errors:
            raise ConfigError("Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors))


class ConfigError(Exception):
    """Configuration error."""
    pass


def load_config(config_file: Optional[str] = None, **overrides) -> IBConfig:
    """Convenience function to load configuration.
    
    Args:
        config_file: Optional path to config file
        **overrides: Configuration overrides
        
    Returns:
        Validated IBConfig instance
    """
    loader = ConfigLoader(config_file)
    return loader.load(**overrides)


def create_example_config(output_path: str = "ib_config.json") -> None:
    """Create an example configuration file.
    
    Args:
        output_path: Path where to save the example config
    """
    example_config = {
        "ib": {
            "host": "127.0.0.1",
            "port": 7497,
            "client_id": 1,
            "account": "",
            "connection_timeout": 30,
            "data_timeout": 10,
            "retry_attempts": 3,
            "retry_delay": 5,
            "log_level": "INFO",
            "verbose": False,
            "json_output": False
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"Example configuration saved to {output_path}")