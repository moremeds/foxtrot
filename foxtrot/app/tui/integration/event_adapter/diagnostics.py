"""
Diagnostics and health monitoring for EventEngineAdapter.

This module provides comprehensive health monitoring and issue detection
capabilities for the EventEngineAdapter system.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class AdapterDiagnostics:
    """Health monitoring and diagnostics for EventEngineAdapter."""

    def __init__(self, adapter_ref, statistics_ref, cleanup_manager_ref):
        """Initialize diagnostics with references to required components."""
        self._adapter_ref = adapter_ref
        self._statistics_ref = statistics_ref
        self._cleanup_manager_ref = cleanup_manager_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference, returning None if dead."""
        return self._adapter_ref()

    def diagnose_issues(self) -> List[str]:
        """Diagnose potential issues with the adapter."""
        adapter = self._get_adapter()
        if not adapter:
            return ["Adapter reference is dead - critical issue"]

        issues = []
        
        try:
            stats = self._statistics_ref.get_stats()
            
            # Check basic health
            if not stats["is_started"]:
                issues.append("Adapter is not started")
                
            if stats["loop_status"] != "active":
                issues.append("Event loop is not active")
                
            if stats["batch_task_status"] != "running":
                issues.append("Batch processing task is not running")

            # Check performance issues
            if stats["queue_size"] > 50:  # Arbitrary threshold
                issues.append(f"Event queue is backed up ({stats['queue_size']} items)")
                
            if stats["pending_commands"] > 10:  # Arbitrary threshold
                issues.append(f"Many pending commands ({stats['pending_commands']})")
                
            # Check for potential memory leaks
            if stats["component_refs"] > 100:  # Arbitrary threshold
                issues.append(f"Large number of component references ({stats['component_refs']})")

            # Run cleanup and check results
            dead_refs = self._cleanup_manager_ref.cleanup_dead_references()
            if dead_refs > 10:
                issues.append(f"Found {dead_refs} dead component references")
                
            expired_cmds = self._cleanup_manager_ref.cleanup_expired_commands()
            if expired_cmds > 5:
                issues.append(f"Found {expired_cmds} expired commands")

            if not issues:
                issues.append("No issues detected - adapter is healthy")
                
        except Exception as e:
            issues.append(f"Error during diagnostics: {e}")
            
        return issues