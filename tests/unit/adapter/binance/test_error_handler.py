"""
Unit tests for Binance WebSocket Error Handler.

Tests error classification, recovery strategies, and circuit breaker functionality.
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch

from foxtrot.adapter.binance.error_handler import (
    CircuitBreaker, ErrorResponse, ErrorSeverity, ErrorType, WebSocketErrorHandler
)


class TestWebSocketErrorHandler:
    """Test cases for WebSocketErrorHandler."""

    @pytest.fixture
    def handler(self):
        """Create a WebSocketErrorHandler instance."""
        return WebSocketErrorHandler(adapter_name="TestAdapter")

    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert handler.adapter_name == "TestAdapter"
        assert all(count == 0 for count in handler.error_counts.values())
        assert isinstance(handler.circuit_breaker, CircuitBreaker)

    @pytest.mark.asyncio
    async def test_error_classification_network(self, handler):
        """Test classification of network errors."""
        network_errors = [
            Exception("Connection refused"),
            Exception("Timeout error"),
            Exception("Network unreachable"),
            Exception("Socket closed"),
            Exception("Connection reset by peer"),
            Exception("Broken pipe"),
            TimeoutError("Request timeout")
        ]
        
        for error in network_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.NETWORK

    @pytest.mark.asyncio
    async def test_error_classification_auth(self, handler):
        """Test classification of authentication errors."""
        auth_errors = [
            Exception("Authentication failed"),
            Exception("Unauthorized access"),
            Exception("Invalid API key"),
            Exception("Signature verification failed"),
            Exception("Permission denied")
        ]
        
        for error in auth_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.AUTHENTICATION

    @pytest.mark.asyncio
    async def test_error_classification_rate_limit(self, handler):
        """Test classification of rate limit errors."""
        rate_errors = [
            Exception("Rate limit exceeded"),
            Exception("Too many requests"),
            Exception("Error 429: Too Many Requests"),
            Exception("Request throttled")
        ]
        
        for error in rate_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_error_classification_symbol(self, handler):
        """Test classification of symbol errors."""
        symbol_errors = [
            Exception("Invalid symbol"),
            Exception("Market not found: INVALID/USDT"),
            Exception("Unknown symbol BTCUSD")
        ]
        
        for error in symbol_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.SYMBOL

    @pytest.mark.asyncio
    async def test_error_classification_exchange(self, handler):
        """Test classification of exchange errors."""
        exchange_errors = [
            Exception("Exchange under maintenance"),
            Exception("Service unavailable (503)"),
            Exception("502 Bad Gateway")
        ]
        
        for error in exchange_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.EXCHANGE

    @pytest.mark.asyncio
    async def test_error_classification_data(self, handler):
        """Test classification of data errors."""
        data_errors = [
            Exception("Failed to parse JSON response"),
            Exception("Invalid data format"),
            Exception("Decode error"),
            ValueError("JSON decode error")
        ]
        
        for error in data_errors:
            error_type = handler._classify_error(error)
            assert error_type == ErrorType.DATA

    @pytest.mark.asyncio
    async def test_handle_network_error(self, handler):
        """Test handling network errors."""
        error = Exception("Connection timeout")
        response = await handler.handle_error(error, "connection")
        
        assert response.error_type == ErrorType.NETWORK
        assert response.severity == ErrorSeverity.HIGH
        assert response.should_retry
        assert response.retry_delay == 5.0
        assert response.should_reconnect
        assert not response.should_fallback

    @pytest.mark.asyncio
    async def test_handle_auth_error(self, handler):
        """Test handling authentication errors."""
        error = Exception("Invalid API key")
        response = await handler.handle_error(error, "authentication")
        
        assert response.error_type == ErrorType.AUTHENTICATION
        assert response.severity == ErrorSeverity.CRITICAL
        assert not response.should_retry  # Don't retry with bad credentials
        assert not response.should_reconnect

    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(self, handler):
        """Test handling rate limit errors."""
        error = Exception("Rate limit exceeded")
        response = await handler.handle_error(error, "subscription")
        
        assert response.error_type == ErrorType.RATE_LIMIT
        assert response.severity == ErrorSeverity.MEDIUM
        assert response.should_retry
        assert response.retry_delay == 60.0  # Default rate limit delay

    @pytest.mark.asyncio
    async def test_handle_rate_limit_with_retry_after(self, handler):
        """Test extracting retry-after from rate limit error."""
        error = Exception("Rate limited. Retry-after: 30 seconds")
        response = await handler.handle_error(error, "subscription")
        
        assert response.error_type == ErrorType.RATE_LIMIT
        assert response.retry_delay == 30.0

    @pytest.mark.asyncio
    async def test_handle_symbol_error(self, handler):
        """Test handling symbol errors."""
        error = Exception("Unknown symbol INVALID")
        response = await handler.handle_error(error, "subscription")
        
        assert response.error_type == ErrorType.SYMBOL
        assert response.severity == ErrorSeverity.LOW
        assert not response.should_retry  # Don't retry invalid symbols
        assert not response.should_reconnect

    @pytest.mark.asyncio
    async def test_error_statistics(self, handler):
        """Test error statistics tracking."""
        # Generate some errors
        await handler.handle_error(Exception("Network error"), "test")
        await handler.handle_error(Exception("Auth failed"), "test")
        await handler.handle_error(Exception("Auth failed"), "test")
        
        stats = handler.get_error_statistics()
        
        assert stats["error_counts"]["network"] == 1
        assert stats["error_counts"]["authentication"] == 2
        assert stats["total_errors"] == 3
        assert "circuit_breaker_state" in stats

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, handler):
        """Test circuit breaker triggering on auth errors."""
        # Generate multiple auth failures
        for _ in range(5):
            await handler.handle_error(Exception("Auth failed"), "test")
        
        # Next auth error should trigger fallback
        response = await handler.handle_error(Exception("Auth failed"), "test")
        assert response.should_fallback


class TestCircuitBreaker:
    """Test cases for CircuitBreaker."""

    @pytest.fixture
    def breaker(self):
        """Create a CircuitBreaker instance."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,
            half_open_max_calls=2
        )

    def test_initialization(self, breaker):
        """Test circuit breaker initialization."""
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 1.0
        assert breaker.half_open_max_calls == 2
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    def test_closed_state_operations(self, breaker):
        """Test operations in CLOSED state."""
        # Should allow attempts
        assert breaker.can_attempt()
        
        # Record success - should stay closed
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    def test_circuit_trip_on_failures(self, breaker):
        """Test circuit trips after threshold failures."""
        # Record failures up to threshold
        for i in range(3):
            breaker.record_failure()
            if i < 2:
                assert breaker.state == "CLOSED"
            else:
                assert breaker.state == "OPEN"
        
        assert breaker.should_trip()
        assert not breaker.can_attempt()

    def test_recovery_timeout(self, breaker):
        """Test circuit moves to HALF_OPEN after timeout."""
        # Trip the circuit
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == "OPEN"
        assert not breaker.can_attempt()
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should allow attempt and move to HALF_OPEN
        assert breaker.can_attempt()
        assert breaker.state == "HALF_OPEN"

    def test_half_open_success_recovery(self, breaker):
        """Test recovery from HALF_OPEN state with successes."""
        # Trip circuit and move to HALF_OPEN
        for _ in range(3):
            breaker.record_failure()
        time.sleep(1.1)
        breaker.can_attempt()  # Moves to HALF_OPEN
        
        # Record successes
        breaker.record_success()
        assert breaker.state == "HALF_OPEN"
        
        breaker.record_success()
        assert breaker.state == "CLOSED"  # Recovered
        assert breaker.failure_count == 0

    def test_half_open_failure_reopens(self, breaker):
        """Test failure in HALF_OPEN reopens circuit."""
        # Trip circuit and move to HALF_OPEN
        for _ in range(3):
            breaker.record_failure()
        time.sleep(1.1)
        breaker.can_attempt()  # Moves to HALF_OPEN
        
        # Any failure reopens
        breaker.record_failure()
        assert breaker.state == "OPEN"
        assert not breaker.can_attempt()

    def test_reset(self, breaker):
        """Test resetting circuit breaker."""
        # Create some state
        for _ in range(2):
            breaker.record_failure()
        
        # Reset
        breaker.reset()
        
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
        assert breaker.half_open_calls == 0
        assert breaker.half_open_failures == 0

    def test_success_resets_failure_count(self, breaker):
        """Test success resets failure count in CLOSED state."""
        # Some failures but not enough to trip
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2
        
        # Success should reset
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "CLOSED"