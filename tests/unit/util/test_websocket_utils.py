"""
Unit tests for WebSocket utilities.

Tests AsyncThreadBridge and WebSocketReconnectManager functionality.
"""

import asyncio
import pytest
import threading
import time
from unittest.mock import MagicMock, patch

from foxtrot.core.event import Event
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.websocket_utils import AsyncThreadBridge, WebSocketReconnectManager


class TestAsyncThreadBridge:
    """Test cases for AsyncThreadBridge."""

    @pytest.fixture
    def mock_event_engine(self):
        """Create a mock EventEngine."""
        engine = MagicMock(spec=EventEngine)
        return engine

    @pytest.fixture
    def bridge(self, mock_event_engine):
        """Create an AsyncThreadBridge instance."""
        bridge = AsyncThreadBridge(mock_event_engine)
        yield bridge
        # Cleanup
        if bridge._running:
            bridge.stop()

    def test_initialization(self, bridge, mock_event_engine):
        """Test bridge initialization."""
        assert bridge.event_engine == mock_event_engine
        assert bridge.loop is None
        assert bridge.bridge_thread is None
        assert not bridge._running
        assert bridge._event_queue.empty()

    def test_start_stop(self, bridge):
        """Test starting and stopping the bridge."""
        # Start bridge
        bridge.start()
        assert bridge._running
        assert bridge.loop is not None
        assert bridge.bridge_thread is not None
        assert bridge.bridge_thread.is_alive()

        # Stop bridge
        bridge.stop()
        assert not bridge._running
        # Give thread time to terminate
        time.sleep(0.1)
        assert not bridge.bridge_thread.is_alive()

    def test_double_start(self, bridge):
        """Test starting an already running bridge."""
        bridge.start()
        
        # Attempt to start again
        with patch.object(bridge.logger, 'warning') as mock_warning:
            bridge.start()
            mock_warning.assert_called_with("AsyncThreadBridge already running")

    def test_run_async_in_thread(self, bridge):
        """Test running async coroutine from sync context."""
        bridge.start()

        async def test_coro():
            await asyncio.sleep(0.01)
            return "test_result"

        future = bridge.run_async_in_thread(test_coro())
        result = future.result(timeout=1.0)
        assert result == "test_result"

    def test_run_async_when_not_running(self, bridge):
        """Test running async when bridge is not started."""
        async def test_coro():
            return "test"

        with pytest.raises(RuntimeError, match="AsyncThreadBridge is not running"):
            bridge.run_async_in_thread(test_coro())

    def test_emit_event_threadsafe(self, bridge, mock_event_engine):
        """Test thread-safe event emission."""
        bridge.start()
        
        test_event = Event("TEST_EVENT", {"data": "test"})
        bridge.emit_event_threadsafe(test_event)
        
        mock_event_engine.put.assert_called_once_with(test_event)

    def test_emit_event_without_engine(self):
        """Test event queuing when no EventEngine provided."""
        bridge = AsyncThreadBridge(event_engine=None)
        bridge.start()
        
        test_event = Event("TEST_EVENT", {"data": "test"})
        bridge.emit_event_threadsafe(test_event)
        
        # Event should be queued
        assert not bridge._event_queue.empty()
        queued_event = bridge._event_queue.get_nowait()
        assert queued_event == test_event
        
        bridge.stop()

    def test_call_soon_threadsafe(self, bridge):
        """Test scheduling callback in event loop."""
        bridge.start()
        
        callback_called = threading.Event()
        test_data = []
        
        def test_callback(data):
            test_data.append(data)
            callback_called.set()
        
        bridge.call_soon_threadsafe(test_callback, "test_value")
        
        assert callback_called.wait(timeout=1.0)
        assert test_data == ["test_value"]

    def test_create_task(self, bridge):
        """Test creating a task in the event loop."""
        bridge.start()
        
        async def test_coro():
            await asyncio.sleep(0.01)
            return "task_result"
        
        task = bridge.create_task(test_coro())
        assert task is not None
        assert isinstance(task, asyncio.Task)

    def test_create_task_when_not_running(self, bridge):
        """Test creating task when bridge is not started."""
        async def test_coro():
            return "test"
        
        task = bridge.create_task(test_coro())
        assert task is None

    def test_event_loop_error_handling(self, bridge):
        """Test error handling in event loop thread."""
        bridge.start()
        
        # Force an error by closing the loop
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)
        time.sleep(0.1)
        
        # Bridge should handle the error gracefully
        assert not bridge._running


class TestWebSocketReconnectManager:
    """Test cases for WebSocketReconnectManager."""

    @pytest.fixture
    def manager(self):
        """Create a WebSocketReconnectManager instance."""
        return WebSocketReconnectManager(
            base_delay=1.0,
            max_delay=60.0,
            max_attempts=5,
            backoff_factor=2.0
        )

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.base_delay == 1.0
        assert manager.max_delay == 60.0
        assert manager.max_attempts == 5
        assert manager.backoff_factor == 2.0
        assert manager.reconnect_attempts == 0
        assert manager.consecutive_failures == 0

    def test_should_reconnect(self, manager):
        """Test reconnection decision logic."""
        # Should allow reconnection initially
        assert manager.should_reconnect()
        
        # Simulate max attempts
        for _ in range(5):
            manager.record_attempt()
        
        # Should not allow after max attempts
        assert not manager.should_reconnect()

    def test_exponential_backoff(self, manager):
        """Test exponential backoff calculation."""
        # First attempt - base delay
        delay1 = manager.get_reconnect_delay()
        assert 1.0 <= delay1 <= 1.1  # Base delay + jitter
        
        # Second attempt - 2x base
        manager.record_attempt()
        delay2 = manager.get_reconnect_delay()
        assert 2.0 <= delay2 <= 2.2
        
        # Third attempt - 4x base
        manager.record_attempt()
        delay3 = manager.get_reconnect_delay()
        assert 4.0 <= delay3 <= 4.4
        
        # Verify exponential growth
        assert delay2 > delay1
        assert delay3 > delay2

    def test_max_delay_cap(self, manager):
        """Test that delay is capped at max_delay."""
        # Simulate many attempts
        for _ in range(10):
            manager.record_attempt()
        
        delay = manager.get_reconnect_delay()
        assert delay <= 66.0  # max_delay + 10% jitter

    def test_record_success(self, manager):
        """Test recording successful reconnection."""
        # Simulate some failures
        manager.record_attempt()
        manager.record_attempt()
        manager.record_failure()
        manager.record_failure()
        
        assert manager.reconnect_attempts == 2
        assert manager.consecutive_failures == 2
        
        # Record success
        manager.record_success()
        
        assert manager.reconnect_attempts == 0
        assert manager.consecutive_failures == 0

    def test_reset(self, manager):
        """Test resetting manager state."""
        # Create some state
        manager.record_attempt()
        manager.record_failure()
        manager.last_attempt_time = time.time()
        
        # Reset
        manager.reset()
        
        assert manager.reconnect_attempts == 0
        assert manager.consecutive_failures == 0
        assert manager.last_attempt_time == 0.0

    def test_jitter_variation(self, manager):
        """Test that jitter provides variation in delays."""
        delays = []
        for _ in range(10):
            delay = manager.get_reconnect_delay()
            delays.append(delay)
        
        # All delays should be unique due to jitter
        assert len(set(delays)) == len(delays)
        
        # All should be within expected range
        for delay in delays:
            assert 1.0 <= delay <= 1.1