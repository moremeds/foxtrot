"""
Enhanced IB connection tester with retry logic and comprehensive error handling.
"""
import logging
import time
from typing import Optional

from .config import IBConfig
from .ib_tester import IBConnectionTester
from .utils import format_error_message


class EnhancedIBTester:
    """Enhanced IB tester with retry logic and comprehensive error handling."""
    
    def __init__(self, config: IBConfig):
        """Initialize the enhanced tester.
        
        Args:
            config: IB configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.test_attempts = 0
        self.max_attempts = max(1, config.retry_attempts + 1)  # Initial attempt + retries
        
    def run_comprehensive_test(self) -> tuple[bool, Optional[IBConnectionTester]]:
        """Run comprehensive test with retry logic.
        
        Returns:
            Tuple of (success, tester_instance)
        """
        self.logger.info(f"Starting comprehensive IB test (max attempts: {self.max_attempts})")
        
        last_tester = None
        
        for attempt in range(self.max_attempts):
            self.test_attempts = attempt + 1
            
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt}/{self.config.retry_attempts}")
                if self.config.retry_delay > 0:
                    self.logger.info(f"Waiting {self.config.retry_delay} seconds before retry")
                    time.sleep(self.config.retry_delay)
            
            # Create new tester instance for each attempt
            tester = IBConnectionTester(self.config)
            last_tester = tester
            
            try:
                # Run the test
                success = tester.run_test()
                
                if success:
                    self.logger.info(f"Test successful on attempt {self.test_attempts}")
                    return True, tester
                else:
                    self.logger.warning(f"Test failed on attempt {self.test_attempts}: {tester.last_error}")
                    
                    # Determine if we should retry
                    if not self._should_retry(tester.last_error, attempt):
                        break
                        
            except Exception as e:
                error_msg = format_error_message(e, "test execution")
                self.logger.error(f"Test exception on attempt {self.test_attempts}: {error_msg}")
                
                # For exceptions, we usually want to retry unless it's a configuration error
                if not self._should_retry_exception(e, attempt):
                    break
        
        self.logger.error(f"All {self.test_attempts} test attempts failed")
        return False, last_tester
    
    def _should_retry(self, error_message: Optional[str], attempt: int) -> bool:
        """Determine if we should retry based on the error.
        
        Args:
            error_message: Error message from failed test
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if we've reached max attempts
        if attempt >= self.config.retry_attempts:
            return False
        
        if not error_message:
            return True
        
        error_lower = error_message.lower()
        
        # Don't retry for configuration errors
        no_retry_patterns = [
            "configuration validation failed",
            "invalid integer value",
            "port must be between",
            "client id must be",
            "unsupported exchange",
            "symbol parsing failed"
        ]
        
        for pattern in no_retry_patterns:
            if pattern in error_lower:
                self.logger.info(f"Not retrying due to configuration error: {pattern}")
                return False
        
        # Retry for connection and timeout errors
        retry_patterns = [
            "connection timeout",
            "data collection timeout", 
            "cannot connect to tws",
            "connection lost",
            "network error",
            "socket error"
        ]
        
        for pattern in retry_patterns:
            if pattern in error_lower:
                self.logger.info(f"Will retry due to recoverable error: {pattern}")
                return True
        
        # Default to retry for unknown errors
        return True
    
    def _should_retry_exception(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on the exception type.
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if we've reached max attempts
        if attempt >= self.config.retry_attempts:
            return False
        
        # Don't retry for configuration errors
        from .config import ConfigError
        if isinstance(exception, ConfigError):
            self.logger.info("Not retrying due to configuration error")
            return False
        
        # Don't retry for import errors or other programming errors
        if isinstance(exception, (ImportError, AttributeError, TypeError)):
            self.logger.info(f"Not retrying due to programming error: {type(exception).__name__}")
            return False
        
        # Retry for network and connection related errors
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,  # Includes socket errors
            RuntimeError  # Generic runtime issues that might be temporary
        )
        
        if isinstance(exception, retry_exceptions):
            self.logger.info(f"Will retry due to recoverable exception: {type(exception).__name__}")
            return True
        
        # Default to retry for other exceptions
        return True


def run_test_with_retries(config: IBConfig) -> tuple[bool, Optional[IBConnectionTester]]:
    """Convenience function to run test with retries.
    
    Args:
        config: IB configuration
        
    Returns:
        Tuple of (success, tester_instance)
    """
    enhanced_tester = EnhancedIBTester(config)
    return enhanced_tester.run_comprehensive_test()