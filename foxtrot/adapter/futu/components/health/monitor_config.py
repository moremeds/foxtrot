"""
Monitor configuration and status management for Futu health monitoring.

This module provides configuration management, status reporting,
and logging utilities for the health monitoring system.
"""

import time
import weakref
from typing import Any, Dict, Optional


class MonitorConfig:
    """Configuration and status management for health monitoring."""

    def __init__(self, api_client_ref: weakref.ref):
        """Initialize monitor configuration."""
        self._api_client_ref = api_client_ref
        self._last_heartbeat = 0.0

    def get_health_status(self, monitor_running: bool, reconnect_attempts: int, 
                         max_reconnect_attempts: int, keep_alive_interval: int, 
                         reconnect_interval: int) -> Dict[str, Any]:
        """
        Get detailed health status information.
        
        Args:
            monitor_running: Whether monitoring is currently active
            reconnect_attempts: Current reconnection attempt count
            max_reconnect_attempts: Maximum reconnection attempts allowed
            keep_alive_interval: Keep-alive check interval
            reconnect_interval: Reconnection interval
            
        Returns:
            Dictionary with comprehensive health status
        """
        api_client = self._api_client_ref()
        
        status = {
            "monitor_running": monitor_running,
            "last_heartbeat": self._last_heartbeat,
            "time_since_heartbeat": time.time() - self._last_heartbeat if self._last_heartbeat > 0 else None,
            "reconnect_attempts": reconnect_attempts,
            "max_reconnect_attempts": max_reconnect_attempts,
            "keep_alive_interval": keep_alive_interval,
            "reconnect_interval": reconnect_interval,
        }

        if api_client:
            status.update({
                "api_client_alive": True,
                "connected": getattr(api_client, 'connected', False),
                "quote_context_healthy": api_client.quote_ctx is not None,
                "hk_trade_context_healthy": (api_client.trade_ctx_hk is not None 
                                           if getattr(api_client, 'hk_access', False) else None),
                "us_trade_context_healthy": (api_client.trade_ctx_us is not None
                                           if getattr(api_client, 'us_access', False) else None),
            })
        else:
            status.update({
                "api_client_alive": False,
                "connected": False,
                "quote_context_healthy": False,
                "hk_trade_context_healthy": None,
                "us_trade_context_healthy": None,
            })

        return status

    def update_configuration(
        self,
        keep_alive_interval: Optional[int] = None,
        max_reconnect_attempts: Optional[int] = None,
        reconnect_interval: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Update health monitoring configuration with validation.
        
        Args:
            keep_alive_interval: New keep-alive interval in seconds
            max_reconnect_attempts: New maximum reconnection attempts
            reconnect_interval: New reconnection interval in seconds
            
        Returns:
            Dictionary with updated configuration values
        """
        updated_config = {}
        
        if keep_alive_interval is not None:
            updated_config['keep_alive_interval'] = max(10, min(keep_alive_interval, 3600))
            
        if max_reconnect_attempts is not None:
            updated_config['max_reconnect_attempts'] = max(1, min(max_reconnect_attempts, 20))
            
        if reconnect_interval is not None:
            updated_config['reconnect_interval'] = max(1, min(reconnect_interval, 300))
            
        if updated_config:
            self._log_info(f"Health monitor configuration updated: "
                          f"keep_alive={updated_config.get('keep_alive_interval', 'unchanged')}s, "
                          f"max_reconnect={updated_config.get('max_reconnect_attempts', 'unchanged')}, "
                          f"reconnect_interval={updated_config.get('reconnect_interval', 'unchanged')}s")
        
        return updated_config

    def update_heartbeat(self) -> None:
        """Update the last heartbeat timestamp."""
        self._last_heartbeat = time.time()

    def get_last_heartbeat(self) -> float:
        """Get the last heartbeat timestamp."""
        return self._last_heartbeat

    def _log_info(self, msg: str) -> None:
        """Log info message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_info'):
            api_client._log_info(f"HealthMonitor: {msg}")

    def _log_error(self, msg: str) -> None:
        """Log error message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_error'):
            api_client._log_error(f"HealthMonitor: {msg}")


class MonitorLogger:
    """Logging utilities for health monitoring."""

    def __init__(self, api_client_ref: weakref.ref):
        """Initialize monitor logger."""
        self._api_client_ref = api_client_ref

    def log_info(self, msg: str) -> None:
        """Log info message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_info'):
            api_client._log_info(f"HealthMonitor: {msg}")

    def log_error(self, msg: str) -> None:
        """Log error message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_error'):
            api_client._log_error(f"HealthMonitor: {msg}")