"""
Futu status provider for comprehensive status and health reporting.

This module aggregates status information from all components and provides
unified interfaces for connection health, diagnostics, and monitoring data.
"""

import time
import weakref
from typing import Any, Dict

from .status_diagnostics import StatusDiagnostics
from .status_utils import create_base_status, get_context_health_status, get_opend_gateway_status


class FutuStatusProvider:
    """
    Provider for comprehensive Futu connection and component status.
    
    This class aggregates status information from all modular components
    and provides unified interfaces for health monitoring and diagnostics.
    """

    def __init__(
        self, 
        api_client_ref: weakref.ref,
        connection_orchestrator: Any,
        health_monitor: Any,
        manager_coordinator: Any,
        callback_manager: Any
    ):
        """Initialize status provider."""
        self._api_client_ref = api_client_ref
        self.connection_orchestrator = connection_orchestrator
        self.health_monitor = health_monitor
        self.manager_coordinator = manager_coordinator
        self.callback_manager = callback_manager

    def get_connection_health(self) -> Dict[str, Any]:
        """Get detailed connection health information."""
        api_client = self._api_client_ref()
        base_status = create_base_status(api_client)
        
        if not api_client:
            return base_status

        # Add health monitor status
        health_status = self.health_monitor.get_health_status()
        base_status.update({
            "last_heartbeat": health_status.get("last_heartbeat", 0),
            "time_since_heartbeat": health_status.get("time_since_heartbeat"),
            "reconnect_attempts": health_status.get("reconnect_attempts", 0),
            "max_reconnect_attempts": health_status.get("max_reconnect_attempts", 5),
            "health_monitor_running": health_status.get("monitor_running", False),
            "keep_alive_interval": health_status.get("keep_alive_interval", 30),
        })

        # Add context health status
        base_status.update(get_context_health_status(api_client))
        return base_status

    def get_opend_status(self) -> Dict[str, Any]:
        """Get OpenD gateway status information."""
        return get_opend_gateway_status(self._api_client_ref())

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status from all components."""
        status = {
            "timestamp": time.time(),
            "api_client_alive": self._api_client_ref() is not None
        }

        # Connection orchestrator status
        try:
            connection_status = self.connection_orchestrator.get_connection_status()
            status["connection"] = connection_status
        except Exception as e:
            status["connection"] = {"error": str(e)}

        # Health monitor status
        try:
            health_status = self.health_monitor.get_health_status()
            status["health"] = health_status
        except Exception as e:
            status["health"] = {"error": str(e)}

        # Manager coordinator status
        try:
            manager_status = self.manager_coordinator.get_status() if self.manager_coordinator else {}
            status["managers"] = manager_status
        except Exception as e:
            status["managers"] = {"error": str(e)}

        # Callback manager status
        try:
            callback_status = self.callback_manager.get_status() if self.callback_manager else {}
            status["callbacks"] = callback_status
        except Exception as e:
            status["callbacks"] = {"error": str(e)}

        return status

    def run_comprehensive_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic tests on all components."""
        return StatusDiagnostics.run_comprehensive_diagnostics(
            self.connection_orchestrator,
            self.health_monitor,
            self.manager_coordinator,
            self.callback_manager
        )

    def get_component_summary(self) -> Dict[str, Any]:
        """Get a summary of all component states."""
        return StatusDiagnostics.get_component_summary(
            self._api_client_ref,
            self.connection_orchestrator,
            self.health_monitor,
            self.manager_coordinator,
            self.callback_manager
        )