"""
Event-driven framework of Silvertine framework.
"""

from collections import defaultdict
from collections.abc import Callable
from queue import Empty, Queue
from threading import Thread
from time import sleep
from typing import Any

from ..util.logger import get_performance_logger, FoxtrotLogger, create_foxtrot_logger

EVENT_TIMER = "eTimer"


class Event:
    """
    Event object consists of a type string which is used
    by event engine for distributing event, and a data
    object which contains the real data.
    """

    def __init__(self, type: str, data: Any = None) -> None:
        """"""
        self.type: str = type
        self.data: Any = data


# Defines handler function to be used in event engine.
HandlerType = Callable[[Event], None]


class EventEngine:
    """
    Event engine distributes event object based on its type
    to those handlers registered.

    It also generates timer event by every interval seconds,
    which can be used for timing purpose.
    """

    def __init__(self, interval: float = 1.0, foxtrot_logger: FoxtrotLogger | None = None) -> None:
        """
        Timer event is generated every 1 second by default, if
        interval not specified.
        
        Args:
            interval: Timer interval in seconds
            foxtrot_logger: Optional FoxtrotLogger instance for dependency injection
        """
        self._interval: float = interval
        self._queue: Queue[Event] = Queue()
        self._active: bool = False
        self._thread: Thread = Thread(target=self._run)
        self._timer: Thread = Thread(target=self._run_timer)
        self._handlers: defaultdict[str, list[HandlerType]] = defaultdict(list)
        self._general_handlers: list[HandlerType] = []
        
        # Performance-optimized logger for hot path
        if foxtrot_logger is None:
            # Fallback: create a new logger instance for backward compatibility
            foxtrot_logger = create_foxtrot_logger()
        self._logger = get_performance_logger("EventEngine", foxtrot_logger)

    def _run(self) -> None:
        """
        Get event from queue and then process it.
        """
        while self._active:
            try:
                event: Event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event) -> None:
        """
        First distribute event to those handlers registered listening
        to this type.

        Then distribute event to those general handlers which listens
        to all types.
        """
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    # Don't hold reference to exception object to prevent memory leaks  
                    # MIGRATION: Replace print with structured logging
                    self._logger.error(
                        "Event handler failed",
                        extra={
                            "event_type": event.type,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                            "handler_name": getattr(handler, '__name__', 'unknown')
                        }
                    )

        if self._general_handlers:
            for handler in self._general_handlers:
                try:
                    handler(event)
                except Exception as e:
                    # Don't hold reference to exception object to prevent memory leaks
                    # MIGRATION: Replace print with structured logging
                    self._logger.error(
                        "General event handler failed", 
                        extra={
                            "event_type": event.type,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                            "handler_name": getattr(handler, '__name__', 'unknown'),
                            "handler_type": "general"
                        }
                    )

    def _run_timer(self) -> None:
        """
        Sleep by interval second(s) and then generate a timer event.
        """
        while self._active:
            sleep(self._interval)
            event: Event = Event(EVENT_TIMER)
            self.put(event)

    def start(self) -> None:
        """
        Start event engine to process events and generate timer events.
        This method is idempotent - multiple calls are safe.
        """
        # If already active and threads are alive, do nothing
        if (
            self._active
            and hasattr(self, "_thread")
            and self._thread.is_alive()
            and hasattr(self, "_timer")
            and self._timer.is_alive()
        ):
            return

        self._active = True

        # Create new threads only if needed (not alive or don't exist)
        if not hasattr(self, "_thread") or not self._thread.is_alive():
            self._thread = Thread(target=self._run)

        if not hasattr(self, "_timer") or not self._timer.is_alive():
            self._timer = Thread(target=self._run_timer)

        # Start threads only if they're not already running
        if not self._thread.is_alive():
            self._thread.start()
        if not self._timer.is_alive():
            self._timer.start()

    def stop(self) -> None:
        """
        Stop event engine with timeout handling to prevent hanging.
        This method is idempotent - multiple calls are safe.
        """
        if not self._active:
            return  # Already stopped

        self._active = False

        # Join threads with timeout to prevent hanging in test environments
        if hasattr(self, "_timer") and self._timer.is_alive():
            self._timer.join(timeout=5.0)
            if self._timer.is_alive():
                # MIGRATION: Replace print with WARNING logging
                self._logger.warning(
                    "Timer thread didn't terminate within timeout",
                    extra={"thread_type": "timer", "timeout_seconds": 5.0}
                )

        if hasattr(self, "_thread") and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                # MIGRATION: Replace print with WARNING logging
                self._logger.warning(
                    "Main thread didn't terminate within timeout",
                    extra={"thread_type": "main", "timeout_seconds": 5.0}
                )

    def put(self, event: Event) -> None:
        """
        Put an event object into event queue.
        """
        self._queue.put(event)

    def register(self, type: str, handler: HandlerType) -> None:
        """
        Register a new handler function for a specific event type. Every
        function can only be registered once for each event type.
        """
        handler_list: list[HandlerType] = self._handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type: str, handler: HandlerType) -> None:
        """
        Unregister an existing handler function from event engine.
        """
        handler_list: list[HandlerType] = self._handlers[type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type)

    def register_general(self, handler: HandlerType) -> None:
        """
        Register a new handler function for all event types. Every
        function can only be registered once for each event type.
        """
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: HandlerType) -> None:
        """
        Unregister an existing general handler function.
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)

    def clear_handlers(self) -> None:
        """
        Clear all registered handlers - useful for testing and cleanup.
        This removes all type-specific and general handlers.
        """
        self._handlers.clear()
        self._general_handlers.clear()
