"""Orchestrator utilities for Futu connection management."""

import time
from typing import Any, Dict


def get_comprehensive_connection_status(
    api_client_ref,
    last_settings: Dict[str, Any],
    context_manager: Any,
    health_monitor: Any
) -> Dict[str, Any]:
    """Get comprehensive connection status from all components."""
    api_client = api_client_ref() if api_client_ref else None
    
    status = {
        "api_client_alive": api_client is not None,
        "connected": getattr(api_client, 'connected', False) if api_client else False,
        "has_last_settings": bool(last_settings),
    }

    # Add context status
    if context_manager:
        try:
            context_status = context_manager.get_context_status()
            status.update({"context_" + k: v for k, v in context_status.items()})
        except Exception as e:
            status["context_error"] = str(e)

    # Add health monitoring status  
    if health_monitor:
        try:
            health_status = health_monitor.get_health_status()
            status.update({"health_" + k: v for k, v in health_status.items()})
        except Exception as e:
            status["health_error"] = str(e)

    return status


def run_connection_tests(context_manager: Any, health_monitor: Any) -> Dict[str, Any]:
    """Test all connection components."""
    results = {}
    
    # Test contexts
    if context_manager:
        try:
            context_tests = context_manager.test_contexts()
            results["context_tests"] = context_tests
        except Exception as e:
            results["context_tests"] = {"error": str(e)}
    
    # Force health check
    if health_monitor:
        try:
            health_ok = health_monitor.force_health_check()
            results["health_check"] = {"success": health_ok}
        except Exception as e:
            results["health_check"] = {"error": str(e)}
    
    # Test validation
    try:
        validation_ok = True  # Placeholder for validation test
        results["validation_test"] = {"success": validation_ok}
    except Exception as e:
        results["validation_test"] = {"error": str(e)}

    return results


def perform_reconnection_attempt(
    api_client_ref,
    context_manager: Any,
    last_settings: Dict[str, Any],
    connect_func
) -> bool:
    """Perform a reconnection attempt with cleanup."""
    if not last_settings:
        return False
        
    api_client = api_client_ref() if api_client_ref else None
    if not api_client:
        return False
    
    try:
        # Clean up existing connections first
        if context_manager:
            context_manager.cleanup_contexts()
        
        # Wait before reconnecting
        time.sleep(2)
        
        # Attempt reconnection
        return connect_func(last_settings)
    except Exception:
        return False


def validate_connection_settings(validator, settings: Dict[str, Any]) -> tuple[bool, str]:
    """Validate connection settings using the validator."""
    if not validator or not settings:
        return False, "Validator or settings not available"
    
    try:
        return validator.validate_settings(settings)
    except Exception as e:
        return False, f"Validation error: {e}"