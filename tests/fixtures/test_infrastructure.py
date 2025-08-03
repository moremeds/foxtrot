"""
Test infrastructure improvements for Foxtrot test suite.

Provides standardized timeout handling, retry mechanisms, and cleanup utilities
for all test types (unit, integration, E2E).
"""

import functools
import threading
import time
from typing import Any, Callable, Optional

import pytest


class TestTimeoutError(Exception):
    """Exception raised when test operations exceed timeout limits."""
    pass


class TestInfrastructure:
    """Test infrastructure utilities for improved reliability."""
    
    # Standard timeout configurations
    TIMEOUTS = {
        'unit': 10,          # Unit tests: 10 seconds
        'integration': 30,   # Integration tests: 30 seconds  
        'e2e': 60,          # E2E tests: 60 seconds
        'cleanup': 5,        # Cleanup operations: 5 seconds
        'thread_join': 2,    # Thread join operations: 2 seconds
    }
    
    @staticmethod
    def with_timeout(timeout_type: str = 'unit'):
        """
        Decorator to add standardized timeouts to test methods.
        
        Args:
            timeout_type: Type of timeout ('unit', 'integration', 'e2e', 'cleanup')
        """
        def decorator(func: Callable) -> Callable:
            timeout_seconds = TestInfrastructure.TIMEOUTS.get(timeout_type, 10)
            
            @functools.wraps(func)
            @pytest.mark.timeout(timeout_seconds)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def retry_on_failure(max_attempts: int = 3, delay: float = 0.5, 
                        exceptions: tuple = (Exception,)):
        """
        Decorator to retry test operations on failure.
        
        Args:
            max_attempts: Maximum number of retry attempts
            delay: Delay between retry attempts in seconds
            exceptions: Tuple of exceptions to catch and retry on
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                            continue
                        else:
                            break
                
                # If all retries failed, raise the last exception
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod 
    def cleanup_threads(timeout: float = 2.0, aggressive: bool = False) -> bool:
        """
        Clean up any lingering threads from test operations.
        
        Args:
            timeout: Maximum time to wait for thread cleanup
            aggressive: Whether to use aggressive cleanup methods
            
        Returns:
            bool: True if cleanup was successful, False if threads remain
        """
        initial_thread_count = threading.active_count()
        start_time = time.time()
        
        # Give threads time to finish naturally
        while (threading.active_count() > 1 and 
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        final_thread_count = threading.active_count()
        
        if final_thread_count > 1 and aggressive:
            # Log remaining threads for debugging
            remaining_threads = [t for t in threading.enumerate() 
                               if t != threading.current_thread()]
            
            # In test environment, we just log - don't force kill threads
            # as that can cause instability
            pass
        
        return final_thread_count <= 1
    
    @staticmethod
    def ensure_cleanup(cleanup_func: Callable, timeout: float = 5.0) -> bool:
        """
        Ensure cleanup function completes within timeout.
        
        Args:
            cleanup_func: Function to call for cleanup
            timeout: Maximum time to wait for cleanup
            
        Returns:
            bool: True if cleanup completed successfully
        """
        try:
            # Create a thread to run cleanup with timeout
            cleanup_thread = threading.Thread(target=cleanup_func, daemon=True)
            cleanup_thread.start()
            cleanup_thread.join(timeout=timeout)
            
            if cleanup_thread.is_alive():
                # Cleanup didn't complete in time
                return False
            
            return True
            
        except Exception:
            return False


class EnhancedTestCase:
    """Enhanced test case base class with improved cleanup and timeouts."""
    
    def setUp(self) -> None:
        """Enhanced setup with timeout monitoring."""
        self._start_time = time.time()
        self._cleanup_items = []
    
    def tearDown(self) -> None:
        """Enhanced teardown with comprehensive cleanup."""
        # Execute all registered cleanup items
        for cleanup_item in reversed(self._cleanup_items):
            try:
                if callable(cleanup_item):
                    TestInfrastructure.ensure_cleanup(cleanup_item)
                elif hasattr(cleanup_item, 'close'):
                    cleanup_item.close()
                elif hasattr(cleanup_item, 'stop'):
                    cleanup_item.stop()
            except Exception:
                # Log but don't fail teardown on cleanup errors
                pass
        
        # Clean up any remaining threads
        TestInfrastructure.cleanup_threads(timeout=2.0)
    
    def add_cleanup(self, item: Any) -> None:
        """
        Register an item for cleanup during tearDown.
        
        Args:
            item: Object with close/stop method or callable to execute
        """
        self._cleanup_items.append(item)
    
    def assert_timeout_completion(self, func: Callable, timeout: float = 5.0, 
                                 message: str = "Operation timed out") -> Any:
        """
        Assert that a function completes within the specified timeout.
        
        Args:
            func: Function to execute
            timeout: Maximum time to wait
            message: Error message if timeout occurs
            
        Returns:
            Result of the function call
        """
        start_time = time.time()
        result = None
        completed = False
        
        def run_func():
            nonlocal result, completed
            try:
                result = func()
                completed = True
            except Exception as e:
                result = e
                completed = True
        
        thread = threading.Thread(target=run_func, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if not completed:
            raise TestTimeoutError(f"{message} (timeout: {timeout}s)")
        
        if isinstance(result, Exception):
            raise result
            
        return result


def test_with_cleanup(*cleanup_items):
    """
    Decorator to ensure cleanup of resources after test completion.
    
    Args:
        *cleanup_items: Items to clean up (objects with close/stop or callables)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                # Clean up all items
                for item in reversed(cleanup_items):
                    try:
                        if callable(item):
                            item()
                        elif hasattr(item, 'close'):
                            item.close()
                        elif hasattr(item, 'stop'):
                            item.stop()
                    except Exception:
                        # Don't fail test on cleanup errors
                        pass
        return wrapper
    return decorator


# Predefined decorators for common use cases
unit_test = TestInfrastructure.with_timeout('unit')
integration_test = TestInfrastructure.with_timeout('integration')
e2e_test = TestInfrastructure.with_timeout('e2e')

retry_flaky = TestInfrastructure.retry_on_failure(max_attempts=3, delay=0.5)
retry_network = TestInfrastructure.retry_on_failure(
    max_attempts=2, 
    delay=1.0,
    exceptions=(ConnectionError, TimeoutError)
)