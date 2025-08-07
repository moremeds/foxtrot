"""
Futu health monitor facade for connection monitoring and automatic reconnection.

This module provides a unified interface to health monitoring operations
by coordinating specialized modules for checking, reconnection, and configuration.
"""

import threading
import time
import weakref
from typing import Any, Dict, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ...api_client import FutuApiClient

from .health_checker import HealthChecker
from .monitor_config import MonitorConfig, MonitorLogger
from .reconnection_manager import ReconnectionManager


class FutuHealthMonitor:
    """Health monitoring facade that coordinates specialized modules."""

    def __init__(self, api_client_ref: 'weakref.ref[FutuApiClient]') -> None:
        """Initialize health monitor."""
        self._api_client_ref = api_client_ref
        
        # Initialize specialized modules
        self._logger = MonitorLogger(api_client_ref)
        self._config = MonitorConfig(api_client_ref)
        self._health_checker = HealthChecker(api_client_ref, weakref.ref(self._logger))
        self._reconnection_manager = ReconnectionManager(api_client_ref, weakref.ref(self._logger))
        
        # Monitor state
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._health_monitor_running: bool = False
        
        # Configuration defaults
        self._max_reconnect_attempts: int = 5
        self._reconnect_interval: int = 10
        self._keep_alive_interval: int = 30

    def start_monitoring(self, keep_alive_interval: int = 30, max_reconnect_attempts: int = 5, reconnect_interval: int = 10) -> None:
        """Start connection health monitoring."""
        if self._health_monitor_running:
            return

        # Update configuration
        self._keep_alive_interval = max(10, min(keep_alive_interval, 3600))
        self._max_reconnect_attempts = max(1, min(max_reconnect_attempts, 20))
        self._reconnect_interval = max(1, min(reconnect_interval, 300))

        self._health_monitor_running = True
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            name="FutuHealthMonitor",
            daemon=True
        )
        self._health_monitor_thread.start()
        self._config.update_heartbeat()
        
        self._logger.log_info("Connection health monitor started")

    def stop_monitoring(self) -> None:
        """Stop connection health monitoring."""
        self._health_monitor_running = False
        if self._health_monitor_thread and self._health_monitor_thread.is_alive():
            self._health_monitor_thread.join(timeout=5)
        self._health_monitor_thread = None
        self._logger.log_info("Connection health monitor stopped")

    def _health_monitor_loop(self) -> None:
        """Main health monitoring loop."""
        while self._health_monitor_running:
            try:
                # Check connection health
                if not self._health_checker.check_connection_health():
                    self._logger.log_error("Connection health check failed, attempting reconnection...")
                    self._reconnection_manager.attempt_reconnection(
                        self._max_reconnect_attempts, 
                        self._reconnect_interval
                    )

                # Update heartbeat
                self._config.update_heartbeat()

                # Sleep until next check
                time.sleep(self._keep_alive_interval)

            except Exception as e:
                self._logger.log_error(f"Health monitor error: {e}")
                time.sleep(5)  # Wait before retry on error

    # Health checking delegation
    def force_health_check(self) -> bool:
        """Force an immediate health check."""
        return self._health_checker.force_health_check()

    # Reconnection delegation
    def reset_reconnect_attempts(self) -> None:
        """Reset the reconnection attempt counter."""
        self._reconnection_manager.reset_reconnect_attempts()

    # Configuration delegation
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status information."""
        return self._config.get_health_status(
            self._health_monitor_running,
            self._reconnection_manager.get_reconnect_attempts(),
            self._max_reconnect_attempts,
            self._keep_alive_interval,
            self._reconnect_interval
        )

    def update_configuration(
        self,
        keep_alive_interval: Optional[int] = None,
        max_reconnect_attempts: Optional[int] = None,
        reconnect_interval: Optional[int] = None
    ) -> None:
        """Update health monitoring configuration."""
        updated = self._config.update_configuration(
            keep_alive_interval, max_reconnect_attempts, reconnect_interval
        )
        
        # Apply updates to local configuration
        if 'keep_alive_interval' in updated:
            self._keep_alive_interval = updated['keep_alive_interval']
        if 'max_reconnect_attempts' in updated:
            self._max_reconnect_attempts = updated['max_reconnect_attempts']
        if 'reconnect_interval' in updated:
            self._reconnect_interval = updated['reconnect_interval']

    def is_monitoring(self) -> bool:
        """Check if health monitoring is currently active."""
        return self._health_monitor_running and (
            self._health_monitor_thread is not None and 
            self._health_monitor_thread.is_alive()
        )