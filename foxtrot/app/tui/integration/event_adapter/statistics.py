"""
Statistics gathering for EventEngineAdapter.

This module provides comprehensive statistics collection about adapter
state, registered handlers, and operational metrics.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AdapterStatistics:
    """Statistics gathering functionality for EventEngineAdapter."""

    def __init__(self, adapter_ref):
        """Initialize statistics with weak reference to adapter."""
        self._adapter_ref = adapter_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference, returning None if dead."""
        return self._adapter_ref()

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics for monitoring and debugging."""
        adapter = self._get_adapter()
        if not adapter:
            return {"error": "Adapter reference is dead"}

        try:
            # Thread-safe statistics gathering
            with adapter._event_types_lock:
                registered_event_types_count = len(adapter.registered_event_types)

            with adapter._handlers_lock:
                total_handlers = sum(len(handlers) for handlers in adapter.handlers.values())

            with adapter._component_refs_lock:
                component_refs_count = len(adapter.component_refs)

            with adapter._pending_commands_lock:
                pending_commands_count = len(adapter.pending_commands)

            return {
                "is_started": adapter.is_started,
                "registered_event_types": registered_event_types_count,
                "total_handlers": total_handlers,
                "queue_size": adapter.batch_queue.qsize() if adapter.batch_queue else 0,
                "batch_interval": adapter.batch_interval,
                "component_refs": component_refs_count,
                "pending_commands": pending_commands_count,
                "loop_status": "active" if adapter.loop and not adapter.loop.is_closed() else "inactive",
                "batch_task_status": "running" if adapter.batch_task and not adapter.batch_task.done() else "stopped",
            }
        except Exception as e:
            logger.error(f"Error gathering adapter statistics: {e}")
            return {"error": f"Failed to gather statistics: {e}"}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance-related metrics for the adapter."""
        adapter = self._get_adapter()
        if not adapter:
            return {"error": "Adapter reference is dead"}

        try:
            stats = self.get_stats()
            
            # Calculate performance indicators
            queue_utilization = 0
            if adapter.batch_queue:
                # Estimate queue utilization (queue size relative to typical processing rate)
                typical_max_queue = 100  # Assume this is a reasonable maximum
                queue_utilization = min(stats["queue_size"] / typical_max_queue, 1.0) * 100

            handler_efficiency = 0
            if stats["registered_event_types"] > 0:
                handler_efficiency = stats["total_handlers"] / stats["registered_event_types"]

            return {
                "queue_utilization_percent": round(queue_utilization, 2),
                "handler_efficiency": round(handler_efficiency, 2),
                "batch_interval_ms": adapter.batch_interval * 1000,
                "command_timeout_s": adapter.command_timeout,
                "is_healthy": stats["is_started"] and stats["loop_status"] == "active",
                "pending_commands_count": stats["pending_commands"],
                "component_refs_count": stats["component_refs"],
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": f"Failed to get performance metrics: {e}"}