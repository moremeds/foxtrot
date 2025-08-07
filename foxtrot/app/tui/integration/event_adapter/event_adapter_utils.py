"""
Event adapter utilities facade for EventEngineAdapter.

This module provides a unified interface to utility operations by delegating
to specialized modules for statistics, cleanup, and diagnostics.
"""

from typing import Any, Dict, List

from .cleanup_manager import CleanupManager
from .diagnostics import AdapterDiagnostics
from .statistics import AdapterStatistics


class EventAdapterUtils:
    """Utility functions facade that delegates to specialized modules."""

    def __init__(self, adapter_ref):
        """Initialize utils with weak reference to adapter."""
        self._adapter_ref = adapter_ref
        self._statistics = AdapterStatistics(adapter_ref)
        self._cleanup_manager = CleanupManager(adapter_ref)
        self._diagnostics = AdapterDiagnostics(adapter_ref, self._statistics, self._cleanup_manager)
    
    def _get_adapter(self):
        """Get adapter from weak reference, returning None if dead."""
        return self._adapter_ref()

    # Statistics operations delegation
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics for monitoring and debugging."""
        return self._statistics.get_stats()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance-related metrics for the adapter."""
        return self._statistics.get_performance_metrics()

    # Cleanup operations delegation
    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references to components."""
        return self._cleanup_manager.cleanup_dead_references()

    def cleanup_expired_commands(self) -> int:
        """Clean up expired command futures."""
        return self._cleanup_manager.cleanup_expired_commands()

    # Diagnostics operations delegation
    def diagnose_issues(self) -> List[str]:
        """Diagnose potential issues with the adapter."""
        return self._diagnostics.diagnose_issues()