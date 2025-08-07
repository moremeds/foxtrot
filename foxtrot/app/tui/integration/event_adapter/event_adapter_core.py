"""
Core EventEngineAdapter for thread-safe bridging between EventEngine and Textual.

This module contains the main EventEngineAdapter class that provides the critical
threading/asyncio bridge functionality with minimal dependencies.
"""

import asyncio
import contextlib
import logging
import threading
import weakref
from collections import defaultdict
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.util.event_type import EVENT_ORDER

from .event_adapter_utils import EventAdapterUtils
from .event_command_publisher import EventCommandPublisher
from .event_batch_processor import EventBatchProcessor
from .adapter_delegation_mixin import AdapterDelegationMixin

logger = logging.getLogger(__name__)


class EventEngineAdapter(AdapterDelegationMixin):
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
        """Initialize the event adapter with EventEngine instance."""
        self.event_engine = event_engine
        self.loop: asyncio.AbstractEventLoop | None = None
        # Event handling state
        self.handlers: Dict[str, List[Callable[[Event], Any]]] = defaultdict(list)
        self._engine_callbacks: Dict[str, Callable] = {}
        self.is_started: bool = False
        self.registered_event_types: Set[str] = set()
        # Component management
        self.component_refs: Set[weakref.ReferenceType] = set()
        self.pending_commands: Dict[str, asyncio.Future] = {}
        self.command_timeout: float = 30.0
        
        # Thread synchronization locks
        self._handlers_lock = threading.RLock()
        self._callbacks_lock = threading.RLock()
        self._event_types_lock = threading.RLock()
        self._component_refs_lock = threading.RLock()
        self._pending_commands_lock = threading.RLock()
        
        # Initialize modular components
        self._utils = EventAdapterUtils(weakref.ref(self))
        self._command_publisher = EventCommandPublisher(weakref.ref(self))
        self._batch_processor = EventBatchProcessor(weakref.ref(self))

        # Register the command response handler
        self.register(EVENT_ORDER, self._command_publisher.handle_command_response)
    
    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the event adapter with the given asyncio loop."""
        if self.is_started:
            logger.warning("EventEngineAdapter is already started")
            return

        self.loop = loop
        await self._batch_processor.start()
        self.is_started = True
        logger.info("EventEngineAdapter started successfully")

    async def stop(self) -> None:
        """Stop the event adapter and clean up resources."""
        if not self.is_started:
            return

        await self._batch_processor.stop()
        for event_type in list(self.registered_event_types):
            self._unregister_engine_callback(event_type)

        self.handlers.clear()
        self._engine_callbacks.clear()
        self.registered_event_types.clear()
        self.is_started = False
        logger.info("EventEngineAdapter stopped successfully")

    def register(
        self, event_type: str, handler: Callable[[Event], Any], component: Optional[Any] = None
    ) -> None:
        """Register an async handler for the specified event type."""
        if not asyncio.iscoroutinefunction(handler):
            # Wrap sync functions to make them async
            async def async_wrapper(event: Event) -> Any:
                return handler(event)

            handler = async_wrapper

        # Thread-safe handler registration
        with self._handlers_lock:
            self.handlers[event_type].append(handler)

        # Thread-safe component reference tracking
        if component is not None:
            with self._component_refs_lock:
                self.component_refs.add(weakref.ref(component))

        # Thread-safe event type registration
        with self._event_types_lock:
            if event_type not in self.registered_event_types:
                self._register_engine_callback(event_type)

        logger.debug(f"Registered handler for event type: {event_type}")

    def unregister(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Unregister a specific handler for an event type."""
        # Thread-safe handler unregistration
        with self._handlers_lock:
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

        # Thread-safe callback registration
        with self._callbacks_lock:
            self._engine_callbacks[event_type] = callback

        # Register with EventEngine
        self.event_engine.register(event_type, callback)

        # Thread-safe event type tracking
        with self._event_types_lock:
            self.registered_event_types.add(event_type)

        logger.debug(f"Registered EventEngine callback for: {event_type}")

    def _unregister_engine_callback(self, event_type: str) -> None:
        """Unregister the callback from EventEngine for the given event type."""
        callback = None

        # Thread-safe callback retrieval and removal
        with self._callbacks_lock:
            if event_type in self._engine_callbacks:
                callback = self._engine_callbacks[event_type]
                del self._engine_callbacks[event_type]

        # Unregister from EventEngine if callback was found
        if callback:
            self.event_engine.unregister(event_type, callback)

            # Thread-safe event type removal
            with self._event_types_lock:
                self.registered_event_types.discard(event_type)

            logger.debug(f"Unregistered EventEngine callback for: {event_type}")

    def _on_engine_event(self, event_type: str, event: Event) -> None:
        """
        Callback from EventEngine (runs on EventEngine thread).

        This method safely transfers the event to the asyncio thread.
        """
        if not self.is_started or not self.loop:
            return

        # Handle specific order events for command responses
        if event.type.startswith(EVENT_ORDER) and event.type != EVENT_ORDER:
            self._command_publisher.handle_command_response(event)

        # Thread-safe call to asyncio
        if not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(self._schedule_event_processing, event)
            except RuntimeError as e:
                logger.error(f"Failed to schedule event processing - loop may be closed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during event scheduling: {e}")
    
    def _schedule_event_processing(self, event: Event) -> None:
        """Schedule event processing on the asyncio loop (runs on asyncio thread)."""
        self._batch_processor.schedule_event(event)