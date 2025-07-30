"""
Event Engine Adapter for TUI Integration

This module provides a thread-safe bridge between the foxtrot EventEngine
(which runs on background threads) and Textual's asyncio-based event loop.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable
from functools import partial
import logging
from typing import Any, Dict, Optional
import weakref
import uuid
from datetime import datetime

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.util.event_type import *
from foxtrot.util.object import OrderData, CancelRequest

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
        self.loop: asyncio.AbstractEventLoop | None = None

        # Event handler storage
        # Maps event_type -> list of async handlers
        self.handlers: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)

        # Internal storage for EventEngine callback references
        self._engine_callbacks: dict[str, Callable] = {}

        # Batching and performance optimization
        self.batch_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.batch_task: asyncio.Task | None = None
        self.batch_interval = 0.016  # ~60 FPS for UI updates

        # State tracking
        self.is_started = False
        self.registered_event_types: set[str] = set()

        # Weak references to TUI components for cleanup
        self.component_refs: set[weakref.ReferenceType] = set()
        
        # Command tracking for responses
        self.pending_commands: Dict[str, asyncio.Future] = {}
        self.command_timeout = 30.0  # seconds

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

    def register(
        self, event_type: str, handler: Callable[[Event], Any], component: Any | None = None
    ) -> None:
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
            pending_events: list[Event] = []

            while True:
                try:
                    # Collect events for batching interval
                    while True:
                        try:
                            event = await asyncio.wait_for(
                                self.batch_queue.get(), timeout=self.batch_interval
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

    async def _process_events_batch(self, events: list[Event]) -> None:
        """
        Process a batch of events.

        Args:
            events: List of events to process
        """
        # Group events by type for efficient processing
        events_by_type: dict[str, list[Event]] = defaultdict(list)
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

    def get_stats(self) -> dict[str, Any]:
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
            "pending_commands": len(self.pending_commands),
        }
    
    # Command Publishing Methods
    
    async def publish_order(self, order_data: Dict[str, Any]) -> str:
        """
        Publish an order command to the MainEngine.
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Order ID for tracking
            
        Raises:
            RuntimeError: If adapter is not started
            asyncio.TimeoutError: If command times out
        """
        if not self.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        
        # Generate unique order ID
        order_id = f"TUI_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # Create OrderData object
        from foxtrot.util.constants import Exchange as ExchangeEnum, Direction as DirectionEnum, OrderType as OrderTypeEnum
        
        order_obj = OrderData(
            symbol=order_data["symbol"],
            exchange=ExchangeEnum.SMART,  # Default exchange
            orderid=order_id,
            type=OrderTypeEnum.LIMIT,  # Convert string to enum
            direction=DirectionEnum.LONG if order_data["direction"] == "BUY" else DirectionEnum.SHORT,
            volume=float(order_data["volume"]),
            price=float(order_data.get("price", 0.0)),
            adapter_name="TUI"
        )
        
        # Create event
        event = Event(EVENT_ORDER, order_obj)
        
        # Create future for response tracking
        response_future = asyncio.Future()
        self.pending_commands[order_id] = response_future
        
        try:
            # Publish event to EventEngine
            self.event_engine.put(event)
            
            # Wait for response or timeout
            await asyncio.wait_for(response_future, timeout=self.command_timeout)
            
            logger.info(f"Order published successfully: {order_id}")
            return order_id
            
        except asyncio.TimeoutError:
            # Clean up pending command
            self.pending_commands.pop(order_id, None)
            logger.error(f"Order command timed out: {order_id}")
            raise
        except Exception as e:
            # Clean up pending command
            self.pending_commands.pop(order_id, None)
            logger.error(f"Failed to publish order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of order to cancel
            symbol: Symbol of the order
            exchange: Exchange where order was placed
            
        Returns:
            True if cancel request was submitted successfully
            
        Raises:
            RuntimeError: If adapter is not started
        """
        if not self.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        
        try:
            # Create cancel request
            cancel_req = CancelRequest(
                orderid=order_id,
                symbol=symbol,
                exchange=exchange
            )
            
            # Create event
            event = Event(EVENT_ORDER_CANCEL, cancel_req)
            
            # Publish event to EventEngine
            self.event_engine.put(event)
            
            logger.info(f"Cancel request published: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish cancel request: {e}")
            return False
    
    async def cancel_all_orders(self) -> bool:
        """
        Cancel all open orders.
        
        Returns:
            True if cancel all request was submitted successfully
            
        Raises:
            RuntimeError: If adapter is not started
        """
        if not self.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        
        try:
            # Create cancel all event
            event = Event(EVENT_ORDER_CANCEL_ALL, {})
            
            # Publish event to EventEngine
            self.event_engine.put(event)
            
            logger.info("Cancel all orders request published")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish cancel all request: {e}")
            return False
    
    async def request_account_info(self) -> bool:
        """
        Request account information update.
        
        Returns:
            True if request was submitted successfully
        """
        if not self.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        
        try:
            # Create account info request event
            event = Event(EVENT_ACCOUNT_REQUEST, {})
            
            # Publish event to EventEngine
            self.event_engine.put(event)
            
            logger.info("Account info request published")
            return True
            
        except Exception as e:
            logger.error(f"Failed to request account info: {e}")
            return False
    
    async def request_position_info(self) -> bool:
        """
        Request position information update.
        
        Returns:
            True if request was submitted successfully
        """
        if not self.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        
        try:
            # Create position info request event
            event = Event(EVENT_POSITION_REQUEST, {})
            
            # Publish event to EventEngine
            self.event_engine.put(event)
            
            logger.info("Position info request published")
            return True
            
        except Exception as e:
            logger.error(f"Failed to request position info: {e}")
            return False
    
    def _handle_command_response(self, event: Event) -> None:
        """
        Handle command response events.
        
        Args:
            event: Response event from MainEngine
        """
        # Extract order ID from event data
        if hasattr(event.data, 'orderid'):
            order_id = event.data.orderid
            
            # Check if we have a pending command for this order
            if order_id in self.pending_commands:
                future = self.pending_commands.pop(order_id)
                
                if not future.done():
                    future.set_result(event.data)
                    logger.debug(f"Command response handled: {order_id}")
    
    def cleanup_expired_commands(self) -> None:
        """Clean up expired command futures."""
        current_time = datetime.now().timestamp()
        expired_commands = []
        
        for order_id, future in self.pending_commands.items():
            if future.done() or (current_time - float(order_id.split('_')[-1]) > self.command_timeout):
                expired_commands.append(order_id)
        
        for order_id in expired_commands:
            future = self.pending_commands.pop(order_id, None)
            if future and not future.done():
                future.cancel()
        
        if expired_commands:
            logger.debug(f"Cleaned up {len(expired_commands)} expired commands")


class TUIEventMixin:
    """
    Mixin class for TUI components that need event handling.

    This mixin provides convenient methods for TUI components to register
    and handle events from the EventEngine.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_handlers: list[tuple[str, Callable]] = []
        self._event_adapter: EventEngineAdapter | None = None

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
    
    # Command Publishing Convenience Methods
    
    async def publish_order(self, order_data: Dict[str, Any]) -> Optional[str]:
        """
        Publish an order through the event adapter.
        
        Args:
            order_data: Order information dictionary
            
        Returns:
            Order ID if successful, None if failed
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot publish order.")
            return None
        
        try:
            return await self._event_adapter.publish_order(order_data)
        except Exception as e:
            logger.error(f"Failed to publish order from component: {e}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """
        Cancel an order through the event adapter.
        
        Args:
            order_id: Order ID to cancel
            symbol: Symbol of the order
            exchange: Exchange where order was placed
            
        Returns:
            True if cancel request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot cancel order.")
            return False
        
        try:
            return await self._event_adapter.cancel_order(order_id, symbol, exchange)
        except Exception as e:
            logger.error(f"Failed to cancel order from component: {e}")
            return False
    
    async def cancel_all_orders(self) -> bool:
        """
        Cancel all orders through the event adapter.
        
        Returns:
            True if cancel all request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot cancel all orders.")
            return False
        
        try:
            return await self._event_adapter.cancel_all_orders()
        except Exception as e:
            logger.error(f"Failed to cancel all orders from component: {e}")
            return False
    
    async def request_account_info(self) -> bool:
        """
        Request account information update.
        
        Returns:
            True if request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot request account info.")
            return False
        
        try:
            return await self._event_adapter.request_account_info()
        except Exception as e:
            logger.error(f"Failed to request account info from component: {e}")
            return False
    
    async def request_position_info(self) -> bool:
        """
        Request position information update.
        
        Returns:
            True if request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot request position info.")
            return False
        
        try:
            return await self._event_adapter.request_position_info()
        except Exception as e:
            logger.error(f"Failed to request position info from component: {e}")
            return False
