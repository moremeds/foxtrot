"""
Event batch processor facade for optimized UI updates.

This module provides a unified interface to batch processing operations
by coordinating the batch scheduler and processor core components.
"""

from typing import Any, Dict

from foxtrot.core.event_engine import Event
from .batch_processor_core import BatchProcessorCore
from .batch_scheduler import BatchScheduler


class EventBatchProcessor:
    """
    Batched event processor facade for UI performance optimization.
    
    This processor coordinates the batch scheduler and core processor
    to collect and process events together, preventing UI flickering.
    """

    def __init__(self, adapter_ref, batch_interval: float = 0.016):
        """
        Initialize the batch processor.
        
        Args:
            adapter_ref: Weak reference to the EventEngineAdapter
            batch_interval: Batching interval in seconds (~60 FPS default)
        """
        self._adapter_ref = adapter_ref
        self.batch_scheduler = BatchScheduler(adapter_ref, batch_interval)
        self.processor_core = BatchProcessorCore(adapter_ref, self.batch_scheduler)
        
        # Expose key properties for backward compatibility
        self.batch_interval = self.batch_scheduler.batch_interval
        self.batch_queue = self.batch_scheduler.batch_queue
        self.batch_task = self.batch_scheduler.batch_task

    async def start(self) -> None:
        """Start the batch processing task."""
        await self.batch_scheduler.start(self.processor_core.batch_processor)

    async def stop(self) -> None:
        """Stop the batch processing task."""
        await self.batch_scheduler.stop()

    def schedule_event(self, event: Event) -> None:
        """
        Schedule an event for batch processing.
        
        Args:
            event: Event to be processed
        """
        self.batch_scheduler.schedule_event(event)

    def get_queue_size(self) -> int:
        """Get current batch queue size."""
        return self.batch_scheduler.get_queue_size()

    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.
        
        Returns:
            Dictionary with batch processing metrics
        """
        return self.batch_scheduler.get_batch_stats()

    def update_batch_interval(self, new_interval: float) -> None:
        """
        Update the batch processing interval.
        
        Args:
            new_interval: New batch interval in seconds
        """
        self.batch_scheduler.update_batch_interval(new_interval)
        self.batch_interval = new_interval  # Update exposed property

    def is_healthy(self) -> bool:
        """
        Check if the batch processor is healthy.
        
        Returns:
            True if processor is running and queue is not severely backed up
        """
        return self.batch_scheduler.is_healthy()
        
    # Property delegation for backward compatibility
    @property 
    def batch_task(self):
        """Access to the batch task for compatibility."""
        return self.batch_scheduler.batch_task
        
    @batch_task.setter
    def batch_task(self, value):
        """Set the batch task for compatibility."""
        self.batch_scheduler.batch_task = value
        
    @property
    def batch_queue(self):
        """Access to the batch queue for compatibility."""
        return self.batch_scheduler.batch_queue
        
    @batch_queue.setter  
    def batch_queue(self, value):
        """Set the batch queue for compatibility."""
        self.batch_scheduler.batch_queue = value