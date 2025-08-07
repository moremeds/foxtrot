"""
Status diagnostics utilities for Futu API client.

This module provides diagnostic testing and validation functionality
for the Futu API client components.
"""

from typing import Any, Dict


class StatusDiagnostics:
    """Diagnostic testing utilities for Futu status monitoring."""

    @staticmethod
    def run_comprehensive_diagnostics(
        connection_orchestrator: Any,
        health_monitor: Any,
        manager_coordinator: Any,
        callback_manager: Any
    ) -> Dict[str, Any]:
        """
        Run comprehensive diagnostic tests on all components.
        
        Args:
            connection_orchestrator: Connection orchestrator instance
            health_monitor: Health monitor instance
            manager_coordinator: Manager coordinator instance
            callback_manager: Callback manager instance
            
        Returns:
            Dictionary with diagnostic test results
        """
        diagnostics = {
            "timestamp": __import__('time').time(),
            "tests_run": 0,
            "tests_passed": 0,
            "success_rate": 0.0,
            "results": {}
        }

        # Test manager coordinator
        try:
            manager_status = manager_coordinator.get_status() if manager_coordinator else {}
            diagnostics["results"]["manager_status"] = manager_status
            diagnostics["tests_run"] += 1
            if manager_status.get("initialized", False):
                diagnostics["tests_passed"] += 1
        except Exception as e:
            diagnostics["results"]["manager_status"] = {"error": str(e)}

        # Test callback manager
        try:
            callback_status = callback_manager.get_status() if callback_manager else {}
            diagnostics["results"]["callback_status"] = callback_status
            diagnostics["tests_run"] += 1
            if callback_status.get("registered", False):
                diagnostics["tests_passed"] += 1
        except Exception as e:
            diagnostics["results"]["callback_status"] = {"error": str(e)}

        # Test connection orchestrator
        try:
            if hasattr(connection_orchestrator, 'test_connection'):
                connection_tests = connection_orchestrator.test_connection()
                diagnostics["results"]["connection_tests"] = connection_tests
                diagnostics["tests_run"] += len(connection_tests)
                diagnostics["tests_passed"] += sum(
                    1 for test in connection_tests.values() 
                    if isinstance(test, dict) and test.get("success", False)
                )
        except Exception as e:
            diagnostics["results"]["connection_tests"] = {"error": str(e)}

        # Test health monitor
        try:
            health_check = health_monitor.force_health_check() if health_monitor else False
            diagnostics["results"]["health_check"] = {"success": health_check}
            diagnostics["tests_run"] += 1
            if health_check:
                diagnostics["tests_passed"] += 1
        except Exception as e:
            diagnostics["results"]["health_check"] = {"error": str(e)}

        # Calculate success rate
        if diagnostics["tests_run"] > 0:
            diagnostics["success_rate"] = diagnostics["tests_passed"] / diagnostics["tests_run"]
        else:
            diagnostics["success_rate"] = 0.0

        return diagnostics

    @staticmethod
    def get_component_summary(
        api_client_ref,
        connection_orchestrator: Any,
        health_monitor: Any,
        manager_coordinator: Any,
        callback_manager: Any
    ) -> Dict[str, Any]:
        """
        Get a summary of all component states.
        
        Args:
            api_client_ref: API client reference
            connection_orchestrator: Connection orchestrator instance
            health_monitor: Health monitor instance
            manager_coordinator: Manager coordinator instance
            callback_manager: Callback manager instance
        
        Returns:
            Dictionary with high-level component status
        """
        api_client = api_client_ref() if api_client_ref else None
        
        return {
            "api_client": api_client is not None,
            "connection_orchestrator": connection_orchestrator is not None,
            "health_monitor": health_monitor.is_monitoring() if health_monitor else False,
            "managers_initialized": manager_coordinator.is_initialized() if manager_coordinator else False,
            "callbacks_registered": callback_manager.is_registered() if callback_manager else False,
            "connected": getattr(api_client, 'connected', False) if api_client else False
        }