"""
Async Bridge for TUI Backend Integration

This module provides async wrappers and utilities for non-blocking
communication between the TUI and backend EventEngine.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Coroutine
from concurrent.futures import ThreadPoolExecutor

from textual import work
from textual.app import App

logger = logging.getLogger(__name__)

T = TypeVar('T')

class AsyncBridge:
    """
    Provides async utilities for bridging TUI and backend operations.
    
    Key features:
    - Non-blocking backend calls using thread pool
    - Proper error handling and logging
    - Background task management
    - Event loop integration
    """
    
    _instance: Optional['AsyncBridge'] = None
    _executor: Optional[ThreadPoolExecutor] = None
    
    def __new__(cls) -> 'AsyncBridge':
        """Singleton pattern for global async bridge."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the async bridge."""
        if self._initialized:
            return
            
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tui-backend")
        self._background_tasks: set[asyncio.Task] = set()
        self._initialized = True
        logger.info("AsyncBridge initialized with thread pool executor")
    
    async def run_in_thread(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Run a blocking function in a thread pool to avoid blocking the event loop.
        
        Args:
            func: The blocking function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
        """
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                functools.partial(func, *args, **kwargs)
            )
            return result
        except Exception as e:
            logger.error(f"Error running {func.__name__} in thread: {e}")
            raise
    
    def create_background_task(
        self, 
        coro: Coroutine[Any, Any, T],
        name: Optional[str] = None,
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> asyncio.Task[T]:
        """
        Create a background task with proper cleanup and error handling.
        
        Args:
            coro: The coroutine to run
            name: Optional name for the task
            error_handler: Optional error handler function
            
        Returns:
            The created task
        """
        task = asyncio.create_task(coro, name=name)
        self._background_tasks.add(task)
        
        def task_done_callback(t: asyncio.Task) -> None:
            self._background_tasks.discard(t)
            try:
                if exc := t.exception():
                    if error_handler:
                        error_handler(exc)
                    else:
                        logger.error(f"Background task {name or 'unnamed'} failed: {exc}")
            except asyncio.CancelledError:
                logger.debug(f"Background task {name or 'unnamed'} was cancelled")
        
        task.add_done_callback(task_done_callback)
        return task
    
    async def wait_with_timeout(
        self,
        coro: Coroutine[Any, Any, T],
        timeout: float = 30.0,
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Wait for a coroutine with a timeout.
        
        Args:
            coro: The coroutine to wait for
            timeout: Maximum time to wait in seconds
            default: Default value to return on timeout
            
        Returns:
            The result of the coroutine or default value on timeout
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            return default
    
    async def cleanup(self) -> None:
        """Clean up resources and cancel background tasks."""
        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for all tasks to complete cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shutdown thread pool
        if self._executor:
            self._executor.shutdown(wait=False)
        
        logger.info("AsyncBridge cleanup completed")


class AsyncEventHandler:
    """
    Decorator and utilities for async event handling in TUI components.
    """
    
    @staticmethod
    def async_handler(timeout: float = 5.0):
        """
        Decorator for async event handlers with timeout and error handling.
        
        Args:
            timeout: Maximum time for handler execution
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                try:
                    return await asyncio.wait_for(
                        func(self, *args, **kwargs),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"{func.__name__} timed out after {timeout}s")
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}")
                    # Re-raise to allow proper error handling
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def background_task(name: Optional[str] = None):
        """
        Decorator to run a method as a background task.
        
        Args:
            name: Optional name for the task
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                bridge = AsyncBridge()
                coro = func(self, *args, **kwargs)
                return bridge.create_background_task(coro, name=name or func.__name__)
            return wrapper
        return decorator


class AsyncDataFetcher:
    """
    Provides async data fetching patterns for TUI components.
    """
    
    def __init__(self, backend_engine: Any) -> None:
        """
        Initialize the data fetcher.
        
        Args:
            backend_engine: The backend engine instance
        """
        self.backend_engine = backend_engine
        self.bridge = AsyncBridge()
    
    async def fetch_market_data(self, symbol: str) -> Optional[dict]:
        """
        Fetch market data asynchronously.
        
        Args:
            symbol: The symbol to fetch data for
            
        Returns:
            Market data dictionary or None on error
        """
        def _fetch():
            # This would be the actual blocking call to backend
            try:
                return self.backend_engine.get_tick(symbol)
            except Exception as e:
                logger.error(f"Failed to fetch market data for {symbol}: {e}")
                return None
        
        return await self.bridge.run_in_thread(_fetch)
    
    async def fetch_positions(self) -> list:
        """
        Fetch all positions asynchronously.
        
        Returns:
            List of position data
        """
        def _fetch():
            try:
                return self.backend_engine.get_all_positions()
            except Exception as e:
                logger.error(f"Failed to fetch positions: {e}")
                return []
        
        return await self.bridge.run_in_thread(_fetch)
    
    async def fetch_orders(self, active_only: bool = True) -> list:
        """
        Fetch orders asynchronously.
        
        Args:
            active_only: Whether to fetch only active orders
            
        Returns:
            List of order data
        """
        def _fetch():
            try:
                return self.backend_engine.get_all_active_orders() if active_only else self.backend_engine.get_all_orders()
            except Exception as e:
                logger.error(f"Failed to fetch orders: {e}")
                return []
        
        return await self.bridge.run_in_thread(_fetch)
    
    async def send_order(self, order_req: Any) -> Optional[str]:
        """
        Send an order asynchronously.
        
        Args:
            order_req: The order request object
            
        Returns:
            Order ID or None on error
        """
        def _send():
            try:
                return self.backend_engine.send_order(order_req)
            except Exception as e:
                logger.error(f"Failed to send order: {e}")
                return None
        
        return await self.bridge.run_in_thread(_send)
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order asynchronously.
        
        Args:
            order_id: The order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        def _cancel():
            try:
                self.backend_engine.cancel_order(order_id)
                return True
            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")
                return False
        
        return await self.bridge.run_in_thread(_cancel)


# Global async bridge instance
async_bridge = AsyncBridge()