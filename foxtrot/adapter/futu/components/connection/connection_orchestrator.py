"""
Futu connection orchestrator for high-level connection workflow management.

This module orchestrates the complete connection process by coordinating
existing modular components (validator, context manager, health monitor)
and managing the connection lifecycle.
"""

import threading
import weakref
from typing import Any, Dict

from .connection_validator import FutuConnectionValidator
from ..context.context_manager import FutuContextManager
from ..health.health_monitor import FutuHealthMonitor
from .orchestrator_utils import (
    get_comprehensive_connection_status,
    perform_reconnection_attempt,
    run_connection_tests,
    validate_connection_settings
)


class FutuConnectionOrchestrator:
    """High-level coordinator for Futu OpenD connection workflow."""

    def __init__(self, api_client_ref: weakref.ref):
        """Initialize connection orchestrator."""
        self._api_client_ref = api_client_ref
        
        # Initialize modular components
        self.validator = FutuConnectionValidator()
        self.context_manager = FutuContextManager(api_client_ref)
        self.health_monitor = FutuHealthMonitor(api_client_ref)
        
        # Connection state
        self._connection_lock = threading.RLock()
        self._last_settings: Dict[str, Any] = {}

    def connect(self, settings: Dict[str, Any]) -> bool:
        """Orchestrate the complete connection process."""
        with self._connection_lock:
            try:
                # Store settings for reconnection
                self._last_settings = settings.copy()
                
                # Validate settings
                is_valid, error_message = validate_connection_settings(self.validator, settings)
                if not is_valid:
                    self._log_error(f"Settings validation failed: {error_message}")
                    return False
                
                # Initialize contexts
                if not self.context_manager.initialize_contexts(settings):
                    self._log_error("Context initialization failed")
                    return False
                
                # Start health monitoring
                monitor_settings = {
                    "keep_alive_interval": settings.get("Keep Alive Interval", 30),
                    "max_reconnect_attempts": settings.get("Max Reconnect Attempts", 5),
                    "reconnect_interval": settings.get("Reconnect Interval", 10)
                }
                
                self.health_monitor.start_monitoring(**monitor_settings)
                
                # Mark API client as connected
                api_client = self._api_client_ref()
                if api_client:
                    api_client.connected = True
                    api_client.last_settings = settings
                
                self._log_info("Connection orchestration completed successfully")
                return True
                
            except Exception as e:
                self._log_error(f"Connection orchestration error: {e}")
                return False

    def disconnect(self) -> bool:
        """Orchestrate the complete disconnection process."""
        with self._connection_lock:
            try:
                # Stop health monitoring
                self.health_monitor.stop_monitoring()
                
                # Cleanup contexts
                self.context_manager.cleanup_contexts()
                
                # Mark API client as disconnected
                api_client = self._api_client_ref()
                if api_client:
                    api_client.connected = False
                
                self._log_info("Disconnection orchestration completed")
                return True
                
            except Exception as e:
                self._log_error(f"Disconnection orchestration error: {e}")
                return False

    def reconnect(self) -> bool:
        """Orchestrate reconnection using last settings."""
        with self._connection_lock:
            return perform_reconnection_attempt(
                self._api_client_ref,
                self.context_manager,
                self._last_settings,
                self.connect
            )

    def get_connection_status(self) -> Dict[str, Any]:
        """Get comprehensive connection status from all components."""
        return get_comprehensive_connection_status(
            self._api_client_ref,
            self._last_settings,
            self.context_manager,
            self.health_monitor
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test all connection components."""
        return run_connection_tests(self.context_manager, self.health_monitor)

    def is_connected(self) -> bool:
        """Check if connection is active."""
        api_client = self._api_client_ref()
        return getattr(api_client, 'connected', False) if api_client else False

    def get_last_settings(self) -> Dict[str, Any]:
        """Get last successful connection settings."""
        return self._last_settings.copy()

    def _log_info(self, msg: str) -> None:
        """Log info message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_info'):
            api_client._log_info(f"Orchestrator: {msg}")

    def _log_error(self, msg: str) -> None:
        """Log error message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_error'):
            api_client._log_error(f"Orchestrator: {msg}")