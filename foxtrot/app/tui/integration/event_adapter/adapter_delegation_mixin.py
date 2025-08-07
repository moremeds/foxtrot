"""
Delegation mixin for EventEngineAdapter.

This mixin contains all the delegation methods that forward calls to 
modular components, keeping the main adapter class focused on core functionality.
"""

from typing import Any


class AdapterDelegationMixin:
    """Mixin that provides delegation methods for EventEngineAdapter."""
    
    def cleanup_dead_references(self) -> None:
        """Clean up dead weak references to components."""
        self._utils.cleanup_dead_references()

    def get_stats(self) -> dict[str, Any]:
        """Get adapter statistics for monitoring and debugging."""
        stats = self._utils.get_stats()
        batch_stats = self._batch_processor.get_batch_stats()
        stats.update(batch_stats)
        return stats

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance-related metrics for the adapter."""
        return self._utils.get_performance_metrics()

    def diagnose_issues(self) -> list[str]:
        """Diagnose potential issues with the adapter."""
        return self._utils.diagnose_issues()

    # Batch processing properties
    @property
    def batch_interval(self) -> float:
        """Get current batch processing interval."""
        return self._batch_processor.batch_interval

    @batch_interval.setter
    def batch_interval(self, value: float) -> None:
        """Set batch processing interval."""
        self._batch_processor.update_batch_interval(value)

    @property
    def batch_queue(self):
        """Get batch queue for compatibility."""
        return self._batch_processor.batch_queue

    @property
    def batch_task(self):
        """Get batch task for compatibility."""
        return self._batch_processor.batch_task

    # Command publishing delegation methods
    async def publish_order(self, order_data: dict[str, Any]) -> str:
        """Publish an order command to the MainEngine."""
        return await self._command_publisher.publish_order(order_data)

    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """Cancel an existing order."""
        return await self._command_publisher.cancel_order(order_id, symbol, exchange)

    async def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        return await self._command_publisher.cancel_all_orders()

    async def request_account_info(self) -> bool:
        """Request account information update."""
        return await self._command_publisher.request_account_info()

    async def request_position_info(self) -> bool:
        """Request position information update."""
        return await self._command_publisher.request_position_info()

    def get_pending_commands_info(self) -> dict[str, Any]:
        """Get information about pending commands."""
        return self._command_publisher.get_pending_commands_info()