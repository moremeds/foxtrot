"""
WebSocket utilities for asyncio-threading bridge.

This module provides utilities for bridging asyncio WebSocket operations
with the threading model used by the BaseAdapter.
"""

import asyncio
import threading
from typing import Any, Callable, Coroutine, Optional
from queue import Queue, Empty
import time

from foxtrot.core.event import Event
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.logger import get_component_logger


class AsyncThreadBridge:
    """
    Bridge between asyncio WebSocket operations and threading model.
    
    This class manages a dedicated asyncio event loop in a separate thread,
    allowing WebSocket operations to run asynchronously while maintaining
    compatibility with the threading-based BaseAdapter interface.
    """
    
    def __init__(self, event_engine: Optional[EventEngine] = None, shutdown_timeout: float = 30.0):
        """
        Initialize the async-thread bridge.
        
        Args:
            event_engine: Optional EventEngine for thread-safe event emission
            shutdown_timeout: Timeout for graceful shutdown (default: 30 seconds)
        """
        self.event_engine = event_engine
        self.logger = get_component_logger("AsyncBridge")
        self.shutdown_timeout = shutdown_timeout
        
        # Asyncio components
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.bridge_thread: Optional[threading.Thread] = None
        
        # Thread synchronization
        self._started = threading.Event()
        self._shutdown = threading.Event()
        self._event_queue: Queue[Event] = Queue()
        
        # State tracking
        self._running = False
        
    def start(self) -> None:
        """Start the asyncio event loop in a dedicated thread."""
        if self._running:
            self.logger.warning("AsyncThreadBridge already running")
            return
            
        self._running = True
        self._shutdown.clear()
        self._started.clear()
        
        # Start the bridge thread (non-daemon for proper cleanup)
        self.bridge_thread = threading.Thread(
            target=self._run_event_loop,
            name="AsyncThreadBridge",
            daemon=False  # Changed from True for proper shutdown handling
        )
        self.bridge_thread.start()
        
        # Wait for the event loop to be ready
        if not self._started.wait(timeout=5.0):
            raise RuntimeError("Failed to start AsyncThreadBridge event loop")
            
        self.logger.info("AsyncThreadBridge started successfully")
        
    def stop(self, timeout: Optional[float] = None) -> bool:
        """
        Stop the asyncio event loop and cleanup with proper timeout handling.
        
        Args:
            timeout: Override shutdown timeout (uses self.shutdown_timeout if not provided)
            
        Returns:
            True if shutdown completed cleanly, False if timeout occurred
        """
        if not self._running:
            return True
            
        self.logger.info("Initiating AsyncThreadBridge shutdown")
        self._running = False
        self._shutdown.set()
        
        # Use provided timeout or default
        shutdown_timeout = timeout if timeout is not None else self.shutdown_timeout
        
        # Stop the event loop
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        # Wait for thread to finish with proper timeout
        if self.bridge_thread and self.bridge_thread.is_alive():
            self.bridge_thread.join(timeout=shutdown_timeout)
            if self.bridge_thread.is_alive():
                self.logger.error(
                    f"AsyncThreadBridge thread did not terminate within {shutdown_timeout}s timeout"
                )
                return False
                
        self.logger.info("AsyncThreadBridge stopped successfully")
        return True
        
    def run_async_in_thread(self, coro: Coroutine) -> asyncio.Future:
        """
        Execute an async coroutine from a synchronous context.
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Future that can be awaited or checked for results
            
        Raises:
            RuntimeError: If the bridge is not running
        """
        if not self._running or not self.loop:
            raise RuntimeError("AsyncThreadBridge is not running")
            
        # Schedule the coroutine in the event loop
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future
        
    def emit_event_threadsafe(self, event: Event) -> None:
        """
        Thread-safe event emission from async context.
        
        Args:
            event: Event to emit
        """
        if self.event_engine:
            # Direct thread-safe emission
            self.event_engine.put(event)
        else:
            # Queue for later processing
            self._event_queue.put(event)
            
    def process_queued_events(self) -> None:
        """Process any queued events (if no EventEngine provided)."""
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                # Process event (would be handled by caller)
                self.logger.debug(f"Queued event: {event.type}")
            except Empty:
                break
                
    def call_soon_threadsafe(self, callback: Callable, *args: Any) -> None:
        """
        Schedule a callback to be called in the event loop thread.
        
        Args:
            callback: Function to call
            *args: Arguments for the callback
        """
        if self.loop and self._running:
            self.loop.call_soon_threadsafe(callback, *args)
            
    def create_task(self, coro: Coroutine) -> Optional[asyncio.Task]:
        """
        Create a task in the event loop.
        
        Args:
            coro: Coroutine to run as a task
            
        Returns:
            Created task or None if bridge not running
        """
        if not self._running or not self.loop:
            return None
            
        # Create task in the event loop thread
        future = asyncio.run_coroutine_threadsafe(
            self._create_task_internal(coro), self.loop
        )
        
        try:
            return future.result(timeout=1.0)
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            return None
            
    async def _create_task_internal(self, coro: Coroutine) -> asyncio.Task:
        """Internal method to create a task in the event loop."""
        return asyncio.create_task(coro)
        
    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a dedicated thread with proper shutdown handling."""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Signal that the loop is ready
            self._started.set()
            
            # Run the event loop until shutdown is requested
            self.logger.debug("AsyncThreadBridge event loop started")
            
            # Create a task to monitor shutdown event
            async def monitor_shutdown():
                """Monitor shutdown event in async context."""
                while not self._shutdown.is_set():
                    await asyncio.sleep(0.1)
                self.loop.stop()
            
            # Schedule shutdown monitor
            asyncio.ensure_future(monitor_shutdown(), loop=self.loop)
            
            # Run the event loop
            self.loop.run_forever()
            
        except Exception as e:
            self.logger.error(f"Error in AsyncThreadBridge event loop: {e}")
        finally:
            # Comprehensive cleanup
            self.logger.info("AsyncThreadBridge event loop cleanup starting")
            
            if self.loop and not self.loop.is_closed():
                # Cancel all pending tasks with proper timeout
                # Use the newer API for getting tasks
                try:
                    pending = asyncio.all_tasks(self.loop)
                except AttributeError:
                    # Fallback for Python 3.7+
                    pending = {task for task in asyncio.Task.all_tasks(self.loop) 
                              if not task.done()}
                
                if pending:
                    self.logger.debug(f"Cancelling {len(pending)} pending tasks")
                    for task in pending:
                        task.cancel()
                    
                    # Give tasks time to handle cancellation
                    try:
                        self.loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*pending, return_exceptions=True),
                                timeout=5.0  # Allow 5 seconds for task cleanup
                            )
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning("Some tasks did not cancel within timeout")
                
                # Close the loop
                self.loop.close()
                
            self._running = False
            self.logger.info("AsyncThreadBridge event loop terminated cleanly")


class WebSocketReconnectManager:
    """
    Manages WebSocket reconnection with exponential backoff.
    
    This class implements a robust reconnection strategy with:
    - Exponential backoff delays
    - Maximum retry attempts
    - Connection state tracking
    - Failure statistics
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_attempts: int = 50,
        backoff_factor: float = 2.0
    ):
        """
        Initialize the reconnect manager.
        
        Args:
            base_delay: Initial delay between reconnection attempts (seconds)
            max_delay: Maximum delay between attempts (seconds)
            max_attempts: Maximum number of reconnection attempts
            backoff_factor: Multiplier for exponential backoff
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        
        # State tracking
        self.reconnect_attempts = 0
        self.last_attempt_time = 0.0
        self.consecutive_failures = 0
        
    def should_reconnect(self) -> bool:
        """
        Determine if reconnection should be attempted.
        
        Returns:
            True if reconnection should be attempted, False otherwise
        """
        return self.reconnect_attempts < self.max_attempts
        
    def get_reconnect_delay(self) -> float:
        """
        Calculate the delay before next reconnection attempt.
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff with jitter
        delay = min(
            self.base_delay * (self.backoff_factor ** self.reconnect_attempts),
            self.max_delay
        )
        
        # Add 10% jitter to prevent thundering herd
        import random
        jitter = delay * 0.1 * random.random()
        
        return delay + jitter
        
    def record_attempt(self) -> None:
        """Record a reconnection attempt."""
        self.reconnect_attempts += 1
        self.last_attempt_time = time.time()
        
    def record_success(self) -> None:
        """Record successful reconnection."""
        self.reconnect_attempts = 0
        self.consecutive_failures = 0
        
    def record_failure(self) -> None:
        """Record failed reconnection."""
        self.consecutive_failures += 1
        
    def reset(self) -> None:
        """Reset reconnection state."""
        self.reconnect_attempts = 0
        self.consecutive_failures = 0
        self.last_attempt_time = 0.0