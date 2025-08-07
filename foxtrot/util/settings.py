"""
Global setting of the trading platform.
"""

from logging import CRITICAL
from typing import Any

from tzlocal import get_localzone_name

from .utility import load_json

class FoxtrotSettings:
    """Configuration class for Foxtrot trading platform."""
    
    def __init__(self, config_file: str = "vt_setting.json") -> None:
        """Initialize settings with default values and optional config file."""
        self._config_file = config_file
        
        # Default configuration values
        self._defaults: dict[str, Any] = {
            "font.family": "微软雅黑",
            "font.size": 12,
            "log.active": True,
            "log.level": CRITICAL,
            "log.console": True,
            "log.file": True,
            "email.server": "smtp.qq.com",
            "email.port": 465,
            "email.username": "",
            "email.password": "",
            "email.sender": "",
            "email.receiver": "",
            "datafeed.name": "",
            "datafeed.username": "",
            "datafeed.password": "",
            "database.timezone": get_localzone_name(),
            "database.name": "sqlite",
            "database.database": "database.db",
            "database.host": "",
            "database.port": 0,
            "database.user": "",
            "database.password": "",
            # WebSocket settings
            "websocket.enabled": False,  # Global WebSocket enable/disable
            "websocket.binance.enabled": True,  # Per-adapter WebSocket settings
            "websocket.binance.symbols": [],  # Empty list means all symbols, or specify ["BTCUSDT", "ETHUSDT"]
            "websocket.reconnect.max_attempts": 50,
            "websocket.reconnect.base_delay": 1.0,
            "websocket.reconnect.max_delay": 60.0,
            "websocket.heartbeat.interval": 30.0,
            "websocket.circuit_breaker.failure_threshold": 5,
            "websocket.circuit_breaker.recovery_timeout": 60.0,
        }
        
        # Load user overrides from file
        self._settings = self._defaults.copy()
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """Load settings from configuration file."""
        user_settings = load_json(self._config_file)
        if user_settings:
            self._settings.update(user_settings)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._settings[key] = value
    
    def update(self, settings: dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._settings.update(settings)
    
    def get_all(self) -> dict[str, Any]:
        """Get all configuration values as a dictionary."""
        return self._settings.copy()


# Factory function for creating settings instances
def create_foxtrot_settings(config_file: str = "vt_setting.json") -> FoxtrotSettings:
    """Create a new FoxtrotSettings instance."""
    return FoxtrotSettings(config_file)


# For backward compatibility - create a default settings instance
# TODO: This should be removed once all components use dependency injection
SETTINGS = create_foxtrot_settings().get_all()
SETTING_FILENAME: str = "vt_setting.json"
