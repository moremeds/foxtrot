"""
Cleanup operations for EventEngineAdapter.

This module provides maintenance and resource cleanup functionality
including dead reference cleanup and expired command management.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CleanupManager:
    """Cleanup and maintenance operations for EventEngineAdapter."""

    def __init__(self, adapter_ref):
        """Initialize cleanup manager with weak reference to adapter."""
        self._adapter_ref = adapter_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference, returning None if dead."""
        return self._adapter_ref()

    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references to components."""
        adapter = self._get_adapter()
        if not adapter:
            logger.warning("Cannot cleanup dead references: adapter reference is dead")
            return 0

        try:
            initial_count = 0
            final_count = 0
            
            with adapter._component_refs_lock:
                initial_count = len(adapter.component_refs)
                adapter.component_refs = {ref for ref in adapter.component_refs if ref() is not None}
                final_count = len(adapter.component_refs)

            cleaned_count = initial_count - final_count
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} dead component references")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up dead references: {e}")
            return 0

    def cleanup_expired_commands(self) -> int:
        """Clean up expired command futures."""
        adapter = self._get_adapter()
        if not adapter:
            logger.warning("Cannot cleanup expired commands: adapter reference is dead")
            return 0

        try:
            current_time = datetime.now().timestamp()
            expired_commands = []

            # Thread-safe identification of expired commands
            with adapter._pending_commands_lock:
                for order_id, future in adapter.pending_commands.items():
                    try:
                        # Extract timestamp from order ID (format: TUI_{uuid}_{timestamp})
                        order_timestamp = float(order_id.split('_')[-1])
                        is_expired = (current_time - order_timestamp) > adapter.command_timeout
                        
                        if future.done() or is_expired:
                            expired_commands.append(order_id)
                    except (ValueError, IndexError):
                        # Invalid order ID format, consider it expired
                        if future.done():
                            expired_commands.append(order_id)

            # Thread-safe cleanup of expired commands
            cleaned_count = 0
            for order_id in expired_commands:
                with adapter._pending_commands_lock:
                    future = adapter.pending_commands.pop(order_id, None)
                if future and not future.done():
                    future.cancel()
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} expired commands")
                
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired commands: {e}")
            return 0