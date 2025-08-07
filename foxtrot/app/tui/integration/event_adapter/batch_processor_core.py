"""
Core batch processing algorithms for EventEngineAdapter.

This module contains the main batch processing logic including event
collection, grouping, and handler execution algorithms.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, List, Dict

from foxtrot.core.event_engine import Event

logger = logging.getLogger(__name__)


class BatchProcessorCore:
    """Core batch processing algorithms for event handling."""

    def __init__(self, adapter_ref, batch_scheduler_ref):
        """
        Initialize the batch processor core.
        
        Args:
            adapter_ref: Weak reference to the EventEngineAdapter
            batch_scheduler_ref: Reference to the batch scheduler
        """
        self._adapter_ref = adapter_ref
        self._batch_scheduler_ref = batch_scheduler_ref

    async def batch_processor(self) -> None:
        """
        Main batch processing loop.
        
        Collects events over the batch interval and processes them together
        to optimize UI update performance.
        """
        try:
            pending_events: List[Event] = []

            while True:
                try:
                    # Collect events for batching interval
                    while True:
                        try:
                            event = await asyncio.wait_for(
                                self._batch_scheduler_ref.batch_queue.get(), 
                                timeout=self._batch_scheduler_ref.batch_interval
                            )
                            pending_events.append(event)
                        except asyncio.TimeoutError:
                            # Batch interval elapsed, process pending events
                            break

                    # Process all pending events
                    if pending_events:
                        await self._process_events_batch(pending_events)
                        pending_events.clear()

                except asyncio.CancelledError:
                    # Process remaining events before shutdown
                    if pending_events:
                        await self._process_events_batch(pending_events)
                    raise

                except Exception as e:
                    logger.error(f"Error in batch processor: {e}")
                    # Continue processing to avoid breaking the event system

        except asyncio.CancelledError:
            logger.info("Batch processor cancelled")
            raise

    async def _process_events_batch(self, events: List[Event]) -> None:
        """
        Process a batch of events by grouping them by type.

        Args:
            events: List of events to process
        """
        adapter = self._adapter_ref()
        if not adapter:
            logger.warning("Cannot process events: adapter reference is dead")
            return

        # Group events by type for efficient processing
        events_by_type: Dict[str, List[Event]] = defaultdict(list)
        for event in events:
            events_by_type[event.type].append(event)

        # Process each event type
        for event_type, type_events in events_by_type.items():
            await self._process_event_type_batch(adapter, event_type, type_events)

    async def _process_event_type_batch(
        self, adapter: Any, event_type: str, type_events: List[Event]
    ) -> None:
        """
        Process all events of a specific type.

        Args:
            adapter: The EventEngineAdapter instance
            event_type: Type of events being processed
            type_events: List of events of this type
        """
        # Thread-safe handler retrieval
        with adapter._handlers_lock:
            handlers = list(adapter.handlers.get(event_type, []))  # Create a copy

        # Execute all handlers for all events of this type
        for handler in handlers:
            for event in type_events:
                try:
                    # Execute the handler
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)

                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
                    # Continue processing other events