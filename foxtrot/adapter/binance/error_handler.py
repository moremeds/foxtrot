"""
WebSocket Error Handler for Binance adapter.

This module provides comprehensive error handling and classification
for WebSocket operations, including:
- Error classification and appropriate responses
- Recovery strategies for different error types
- Circuit breaker pattern for automatic fallback
"""

from enum import Enum
from typing import Any, Dict, Optional
import time
import asyncio

from foxtrot.util.logger import get_adapter_logger


class ErrorType(Enum):
    """Classification of WebSocket errors."""
    NETWORK = "network"              # Connection failures, timeouts
    AUTHENTICATION = "authentication" # Auth failures, invalid credentials
    RATE_LIMIT = "rate_limit"        # Rate limiting errors
    SYMBOL = "symbol"                # Invalid symbol, not found
    EXCHANGE = "exchange"            # Exchange maintenance, unavailable
    DATA = "data"                    # Data parsing, format errors
    UNKNOWN = "unknown"              # Unclassified errors


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"          # Continue operation, log only
    MEDIUM = "medium"    # Retry with backoff
    HIGH = "high"        # Reconnect required
    CRITICAL = "critical" # Fallback to HTTP required


class ErrorResponse:
    """Response strategy for an error."""
    
    def __init__(
        self,
        error_type: ErrorType,
        severity: ErrorSeverity,
        should_retry: bool,
        retry_delay: float = 0.0,
        should_reconnect: bool = False,
        should_fallback: bool = False,
        message: str = ""
    ):
        """Initialize error response."""
        self.error_type = error_type
        self.severity = severity
        self.should_retry = should_retry
        self.retry_delay = retry_delay
        self.should_reconnect = should_reconnect
        self.should_fallback = should_fallback
        self.message = message


class WebSocketErrorHandler:
    """
    Comprehensive error handling for WebSocket operations.
    
    Features:
    - Error classification and analysis
    - Appropriate response strategies
    - Circuit breaker pattern
    - Error statistics tracking
    """
    
    def __init__(self, adapter_name: str = "BinanceAdapter"):
        """Initialize the error handler."""
        self.adapter_name = adapter_name
        self.logger = get_adapter_logger(f"{adapter_name}Error")
        
        # Error statistics
        self.error_counts: Dict[ErrorType, int] = {et: 0 for et in ErrorType}
        self.last_errors: Dict[ErrorType, float] = {}
        
        # Circuit breaker state with configurable settings
        from foxtrot.util.settings import SETTINGS
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=SETTINGS.get("websocket.circuit_breaker.failure_threshold", 5),
            recovery_timeout=SETTINGS.get("websocket.circuit_breaker.recovery_timeout", 60.0)
        )
        
    async def handle_error(self, error: Exception, context: str) -> ErrorResponse:
        """
        Classify error and determine appropriate response.
        
        Args:
            error: The exception that occurred
            context: Context where error occurred (e.g., "connection", "subscription")
            
        Returns:
            ErrorResponse with recommended actions
        """
        # Classify the error
        error_type = self._classify_error(error)
        
        # Update statistics
        self.error_counts[error_type] += 1
        self.last_errors[error_type] = time.time()
        
        # Log the error
        self.logger.error(f"WebSocket error in {context}: {error_type.value} - {str(error)}")
        
        # Determine response based on error type
        if error_type == ErrorType.NETWORK:
            return await self._handle_network_error(error, context)
        elif error_type == ErrorType.AUTHENTICATION:
            return await self._handle_auth_error(error, context)
        elif error_type == ErrorType.RATE_LIMIT:
            return await self._handle_rate_limit_error(error, context)
        elif error_type == ErrorType.SYMBOL:
            return await self._handle_symbol_error(error, context)
        elif error_type == ErrorType.EXCHANGE:
            return await self._handle_exchange_error(error, context)
        elif error_type == ErrorType.DATA:
            return await self._handle_data_error(error, context)
        else:
            return await self._handle_unknown_error(error, context)
            
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error into appropriate type."""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Network errors
        if any(keyword in error_str for keyword in [
            "connection", "timeout", "network", "socket", "unreachable",
            "refused", "reset", "broken pipe", "eof"
        ]):
            return ErrorType.NETWORK
            
        # Authentication errors
        if any(keyword in error_str for keyword in [
            "auth", "unauthorized", "forbidden", "invalid api",
            "signature", "permission", "credentials"
        ]):
            return ErrorType.AUTHENTICATION
            
        # Rate limit errors
        if any(keyword in error_str for keyword in [
            "rate limit", "too many requests", "429", "throttle"
        ]):
            return ErrorType.RATE_LIMIT
            
        # Symbol errors
        if any(keyword in error_str for keyword in [
            "symbol", "market not found", "invalid market", "unknown symbol"
        ]):
            return ErrorType.SYMBOL
            
        # Exchange errors
        if any(keyword in error_str for keyword in [
            "maintenance", "exchange", "unavailable", "503", "502"
        ]):
            return ErrorType.EXCHANGE
            
        # Data errors
        if any(keyword in error_str for keyword in [
            "parse", "json", "format", "decode", "invalid data"
        ]):
            return ErrorType.DATA
            
        # Check error type names
        if "timeout" in error_type_name:
            return ErrorType.NETWORK
        elif "json" in error_type_name:
            return ErrorType.DATA
            
        return ErrorType.UNKNOWN
        
    async def _handle_network_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle network-related errors."""
        # Network errors typically require reconnection
        return ErrorResponse(
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.HIGH,
            should_retry=True,
            retry_delay=5.0,
            should_reconnect=True,
            message="Network error detected, will attempt reconnection"
        )
        
    async def _handle_auth_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle authentication errors."""
        # Auth errors may require credential refresh
        self.circuit_breaker.record_failure()
        
        return ErrorResponse(
            error_type=ErrorType.AUTHENTICATION,
            severity=ErrorSeverity.CRITICAL,
            should_retry=False,  # Don't retry with same credentials
            should_fallback=self.circuit_breaker.should_trip(),
            message="Authentication failed, check API credentials"
        )
        
    async def _handle_rate_limit_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle rate limiting errors."""
        # Extract retry delay if available
        retry_delay = 60.0  # Default to 1 minute
        
        error_str = str(error)
        # Try to extract retry-after from error message
        import re
        retry_match = re.search(r'retry[_-]?after[:\s]+(\d+)', error_str, re.IGNORECASE)
        if retry_match:
            retry_delay = float(retry_match.group(1))
            
        return ErrorResponse(
            error_type=ErrorType.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            should_retry=True,
            retry_delay=retry_delay,
            message=f"Rate limited, waiting {retry_delay}s before retry"
        )
        
    async def _handle_symbol_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle symbol-related errors."""
        # Symbol errors don't affect other symbols
        return ErrorResponse(
            error_type=ErrorType.SYMBOL,
            severity=ErrorSeverity.LOW,
            should_retry=False,  # Don't retry invalid symbols
            message="Invalid symbol, skipping"
        )
        
    async def _handle_exchange_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle exchange-related errors."""
        # Exchange errors may be temporary
        return ErrorResponse(
            error_type=ErrorType.EXCHANGE,
            severity=ErrorSeverity.HIGH,
            should_retry=True,
            retry_delay=30.0,  # Wait longer for exchange issues
            should_reconnect=True,
            message="Exchange error, will retry after delay"
        )
        
    async def _handle_data_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle data parsing errors."""
        # Data errors might indicate API changes
        self.circuit_breaker.record_failure()
        
        return ErrorResponse(
            error_type=ErrorType.DATA,
            severity=ErrorSeverity.MEDIUM,
            should_retry=True,
            retry_delay=1.0,
            should_fallback=self.circuit_breaker.should_trip(),
            message="Data parsing error, may indicate API changes"
        )
        
    async def _handle_unknown_error(self, error: Exception, context: str) -> ErrorResponse:
        """Handle unclassified errors."""
        # Unknown errors treated conservatively
        self.circuit_breaker.record_failure()
        
        return ErrorResponse(
            error_type=ErrorType.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            should_retry=True,
            retry_delay=10.0,
            should_reconnect=True,
            should_fallback=self.circuit_breaker.should_trip(),
            message="Unknown error occurred"
        )
        
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": {et.value: count for et, count in self.error_counts.items()},
            "circuit_breaker_state": self.circuit_breaker.state,
            "total_errors": sum(self.error_counts.values())
        }


class CircuitBreaker:
    """
    Circuit breaker pattern for automatic fallback.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, fallback active
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        self.half_open_failures = 0
        
    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == "HALF_OPEN":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Enough successful calls, close circuit
                self.state = "CLOSED"
                self.failure_count = 0
                self.half_open_calls = 0
                self.half_open_failures = 0
        elif self.state == "CLOSED":
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
                
    def record_failure(self) -> None:
        """Record failed operation."""
        self.last_failure_time = time.time()
        
        if self.state == "CLOSED":
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                # Trip the circuit
                self.state = "OPEN"
                
        elif self.state == "HALF_OPEN":
            self.half_open_failures += 1
            # Any failure in half-open state reopens circuit
            self.state = "OPEN"
            self.half_open_calls = 0
            self.half_open_failures = 0
            
    def should_trip(self) -> bool:
        """Check if circuit breaker should trip (fallback)."""
        return self.state == "OPEN"
        
    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                # Move to half-open state
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                self.half_open_failures = 0
                return True
                
            return False
            
        # HALF_OPEN state
        return self.half_open_calls < self.half_open_max_calls
        
    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        self.half_open_failures = 0