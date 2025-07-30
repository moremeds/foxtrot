"""
Event Engine Adapter for TUI Integration

This module provides a thread-safe bridge between the foxtrot EventEngine 
(which runs on background threads) and Textual's asyncio-based event loop.
"""

import asyncio
import weakref
from typing import Callable, Dict, List, Optional, Any, Set
from collections import defaultdict
from functools import partial
import logging

from foxtrot.core.event_engine import EventEngine, Event
from foxtrot.util.event_type import *


# Set up logging for debugging
logger = logging.getLogger(__name__)


class EventEngineAdapter:
    """
    Thread-safe adapter that bridges EventEngine (threading) with Textual (asyncio).
    
    This adapter solves the critical integration challenge between foxtrot's
    existing threading-based event system and Textual's asyncio-based UI system.
    
    Key Features:
        - Thread-safe event bridging
        - Asyncio task management
        - Event handler registration and cleanup
        - Performance optimization with batching
        - Error handling and recovery
    """
    
    def __init__(self, event_engine: EventEngine) -> None:
        """
        Initialize the event adapter.
        
        Args:
            event_engine: The foxtrot EventEngine instance
        """
        self.event_engine = event_engine
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Event handler storage
        # Maps event_type -> list of async handlers
        self.handlers: Dict[str, List[Callable[[Event], Any]]] = defaultdict(list)
        
        # Internal storage for EventEngine callback references
        self._engine_callbacks: Dict[str, Callable] = {}
        
        # Batching and performance optimization
        self.batch_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.batch_task: Optional[asyncio.Task] = None
        self.batch_interval = 0.016  # ~60 FPS for UI updates
        
        # State tracking
        self.is_started = False
        self.registered_event_types: Set[str] = set()
        
        # Weak references to TUI components for cleanup
        self.component_refs: Set[weakref.ReferenceType] = set()
    
    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Start the event adapter with the given asyncio loop.
        
        Args:
            loop: The asyncio event loop to use for async operations
        """
        if self.is_started:
            logger.warning("EventEngineAdapter is already started")
            return
        
        self.loop = loop
        self.batch_queue = asyncio.Queue()
        
        # Start the batch processing task
        self.batch_task = asyncio.create_task(self._batch_processor())
        
        self.is_started = True
        logger.info("EventEngineAdapter started successfully")
    
    async def stop(self) -> None:
        """Stop the event adapter and clean up resources."""
        if not self.is_started:
            return
        
        # Cancel batch processing
        if self.batch_task and not self.batch_task.done():
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        # Unregister all event handlers from EventEngine
        for event_type in list(self.registered_event_types):
            self._unregister_engine_callback(event_type)
        
        # Clear all handlers and state
        self.handlers.clear()
        self._engine_callbacks.clear()
        self.registered_event_types.clear()
        self.is_started = False
        
        logger.info("EventEngineAdapter stopped successfully")
    
    def register(self, event_type: str, handler: Callable[[Event], Any], 
                 component: Optional[Any] = None) -> None:
        """
        Register an async handler for the specified event type.
        
        Args:
            event_type: The type of event to listen for
            handler: Async function to call when event occurs
            component: Optional TUI component reference for cleanup
        """
        if not asyncio.iscoroutinefunction(handler):
            # Wrap sync functions to make them async
            async def async_wrapper(event: Event) -> Any:
                return handler(event)
            handler = async_wrapper
        
        # Add handler to our registry
        self.handlers[event_type].append(handler)
        
        # Track component reference for cleanup
        if component is not None:
            self.component_refs.add(weakref.ref(component))
        
        # Register with EventEngine if this is the first handler for this event type
        if event_type not in self.registered_event_types:
            self._register_engine_callback(event_type)
        
        logger.debug(f"Registered handler for event type: {event_type}")
    
    def unregister(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """
        Unregister a specific handler for an event type.
        
        Args:
            event_type: The event type to unregister from
            handler: The specific handler to remove
        """
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                
                # If no handlers left for this event type, unregister from EventEngine
                if not self.handlers[event_type]:
                    self._unregister_engine_callback(event_type)
                    del self.handlers[event_type]
                
                logger.debug(f"Unregistered handler for event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
    
    def _register_engine_callback(self, event_type: str) -> None:
        """Register a callback with the EventEngine for the given event type."""
        callback = partial(self._on_engine_event, event_type)
        self._engine_callbacks[event_type] = callback
        self.event_engine.register(event_type, callback)
        self.registered_event_types.add(event_type)
        
        logger.debug(f"Registered EventEngine callback for: {event_type}")
    
    def _unregister_engine_callback(self, event_type: str) -> None:
        """Unregister the callback from EventEngine for the given event type."""
        if event_type in self._engine_callbacks:
            callback = self._engine_callbacks[event_type]
            self.event_engine.unregister(event_type, callback)
            del self._engine_callbacks[event_type]
            self.registered_event_types.discard(event_type)
            
            logger.debug(f"Unregistered EventEngine callback for: {event_type}")
    
    def _on_engine_event(self, event_type: str, event: Event) -> None:
        """
        Callback from EventEngine (runs on EventEngine thread).
        
        This method safely transfers the event to the asyncio thread.
        """
        if not self.is_started or not self.loop:
            return
        
        # Thread-safe call to asyncio
        if not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(self._schedule_event_processing, event)
            except RuntimeError as e:
                logger.error(f"Failed to schedule event processing: {e}")
    
    def _schedule_event_processing(self, event: Event) -> None:
        """Schedule event processing on the asyncio loop (runs on asyncio thread)."""
        try:
            # Add to batch queue for processing
            self.batch_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event: {event.type}")
    
    async def _batch_processor(self) -> None:
        """
        Process batched events to optimize UI updates.
        
        This processor collects events over a short interval and processes them
        together to prevent UI flickering and improve performance.
        """
        try:
            pending_events: List[Event] = []
            
            while True:
                try:
                    # Collect events for batching interval
                    while True:
                        try:
                            event = await asyncio.wait_for(
                                self.batch_queue.get(), 
                                timeout=self.batch_interval
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
        Process a batch of events.
        
        Args:
            events: List of events to process
        """
        # Group events by type for efficient processing
        events_by_type: Dict[str, List[Event]] = defaultdict(list)
        for event in events:
            events_by_type[event.type].append(event)
        
        # Process each event type
        for event_type, type_events in events_by_type.items():
            handlers = self.handlers.get(event_type, [])
            
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
    
    def cleanup_dead_references(self) -> None:
        """Clean up dead weak references to components."""
        self.component_refs = {ref for ref in self.component_refs if ref() is not None}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get adapter statistics for monitoring and debugging.
        
        Returns:
            Dictionary containing adapter statistics
        """
        return {
            "is_started": self.is_started,
            "registered_event_types": len(self.registered_event_types),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "queue_size": self.batch_queue.qsize() if self.batch_queue else 0,
            "batch_interval": self.batch_interval,
            "component_refs": len(self.component_refs),
        }


class TUIEventMixin:
    """
    Mixin class for TUI components that need event handling.
    
    This mixin provides convenient methods for TUI components to register
    and handle events from the EventEngine.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_handlers: List[tuple[str, Callable]] = []
        self._event_adapter: Optional[EventEngineAdapter] = None
    
    def set_event_adapter(self, adapter: EventEngineAdapter) -> None:
        """Set the event adapter for this component."""
        self._event_adapter = adapter
    
    def register_event_handler(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """
        Register an event handler for this component.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function (can be sync or async)
        """
        if not self._event_adapter:
            raise RuntimeError("Event adapter not set. Call set_event_adapter first.")
        
        self._event_adapter.register(event_type, handler, self)
        self._event_handlers.append((event_type, handler))
    
    def unregister_all_handlers(self) -> None:
        """Unregister all event handlers for this component."""
        if not self._event_adapter:
            return
        
        for event_type, handler in self._event_handlers:
            self._event_adapter.unregister(event_type, handler)
        
        self._event_handlers.clear()
    
    def cleanup_events(self) -> None:
        """Clean up event handlers (call when component is destroyed)."""
        self.unregister_all_handlers()