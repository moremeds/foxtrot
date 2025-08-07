"""
Batch scheduling and queue management for EventEngineAdapter.

This module handles the lifecycle management and event scheduling
for the batch processing system.
"""

import asyncio
import logging
from typing import Any, Dict

from foxtrot.core.event_engine import Event

logger = logging.getLogger(__name__)


class BatchScheduler:
    """Batch lifecycle and queue management for event processing."""

    def __init__(self, adapter_ref, batch_interval: float = 0.016):
        """
        Initialize the batch scheduler.
        
        Args:
            adapter_ref: Weak reference to the EventEngineAdapter
            batch_interval: Batching interval in seconds (~60 FPS default)
        """
        self._adapter_ref = adapter_ref
        self.batch_interval = batch_interval
        self.batch_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.batch_task: asyncio.Task | None = None

    async def start(self, processor_task) -> None:
        """
        Start the batch processing task.
        
        Args:
            processor_task: The batch processor task to execute
        """
        if self.batch_task and not self.batch_task.done():
            logger.warning("Batch processor already running")
            return

        self.batch_queue = asyncio.Queue()
        self.batch_task = asyncio.create_task(processor_task())
        logger.debug("Batch processor started")

    async def stop(self) -> None:
        """Stop the batch processing task."""
        if self.batch_task and not self.batch_task.done():
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        self.batch_task = None
        logger.debug("Batch processor stopped")

    def schedule_event(self, event: Event) -> None:
        """
        Schedule an event for batch processing.
        
        Args:
            event: Event to be processed
        """
        try:
            self.batch_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event: {event.type}")

    def get_queue_size(self) -> int:
        """Get current batch queue size."""
        return self.batch_queue.qsize() if self.batch_queue else 0

    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.
        
        Returns:
            Dictionary with batch processing metrics
        """
        return {
            "batch_interval": self.batch_interval,
            "queue_size": self.get_queue_size(),
            "is_running": self.batch_task is not None and not self.batch_task.done(),
            "task_status": "running" if (self.batch_task and not self.batch_task.done()) else "stopped",
        }

    def update_batch_interval(self, new_interval: float) -> None:
        """
        Update the batch processing interval.
        
        Args:
            new_interval: New batch interval in seconds
        """
        if new_interval > 0:
            self.batch_interval = new_interval
            logger.debug(f"Batch interval updated to {new_interval}s")
        else:
            logger.warning(f"Invalid batch interval: {new_interval}")

    def is_healthy(self) -> bool:
        """
        Check if the batch processor is healthy.
        
        Returns:
            True if processor is running and queue is not severely backed up
        """
        if not self.batch_task or self.batch_task.done():
            return False
            
        # Check if queue is severely backed up (arbitrary threshold)
        queue_size = self.get_queue_size()
        return queue_size < 100  # Threshold for "healthy" queue size