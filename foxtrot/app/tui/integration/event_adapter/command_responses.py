"""
Command response handling and diagnostics for EventEngineAdapter.

This module handles command response processing and provides diagnostic
information about pending commands and their status.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from foxtrot.core.event_engine import Event

logger = logging.getLogger(__name__)


class CommandResponses:
    """Command response handling and diagnostics for EventEngineAdapter."""

    def __init__(self, adapter_ref):
        """Initialize command responses with adapter reference."""
        self._adapter_ref = adapter_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference, returning None if dead."""
        return self._adapter_ref()

    def handle_command_response(self, event: Event) -> None:
        """
        Handle command response events.

        Args:
            event: Response event from MainEngine
        """
        adapter = self._get_adapter()
        if not adapter:
            logger.warning("Cannot handle command response: adapter reference is dead")
            return

        # Extract order ID from event data
        order_id = None
        if hasattr(event.data, 'vt_orderid'):
            order_id = event.data.vt_orderid.split('.')[-1]
        elif hasattr(event.data, 'orderid'):
            order_id = event.data.orderid

        if order_id:
            # Thread-safe pending command handling
            future = None
            with adapter._pending_commands_lock:
                if order_id in adapter.pending_commands:
                    future = adapter.pending_commands.pop(order_id)

            if future and not future.done():
                future.set_result(event.data)
                logger.debug(f"Command response handled: {order_id}")

    def get_pending_commands_info(self) -> Dict[str, Any]:
        """Get information about pending commands."""
        adapter = self._get_adapter()
        if not adapter:
            return {"error": "Adapter reference is dead"}

        try:
            with adapter._pending_commands_lock:
                pending_count = len(adapter.pending_commands)
                command_ids = list(adapter.pending_commands.keys())

            current_time = datetime.now().timestamp()
            command_ages = []
            for cmd_id in command_ids:
                try:
                    cmd_timestamp = float(cmd_id.split('_')[-1])
                    command_ages.append(current_time - cmd_timestamp)
                except (ValueError, IndexError):
                    continue

            avg_age = sum(command_ages) / len(command_ages) if command_ages else 0
            max_age = max(command_ages) if command_ages else 0

            return {
                "pending_count": pending_count,
                "command_timeout": adapter.command_timeout,
                "average_age_seconds": round(avg_age, 2),
                "oldest_age_seconds": round(max_age, 2),
                "commands_near_timeout": sum(1 for age in command_ages if age > adapter.command_timeout * 0.8),
            }
            
        except Exception as e:
            logger.error(f"Error getting pending commands info: {e}")
            return {"error": f"Failed to get pending commands info: {e}"}