"""
Unit tests for Binance WebSocket Manager.

Tests WebSocketManager connection lifecycle and subscription management.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from foxtrot.adapter.binance.websocket_manager import (
    ConnectionState, WebSocketManager
)
from foxtrot.util.websocket_utils import AsyncThreadBridge


class TestWebSocketManager:
    """Test cases for WebSocketManager."""

    @pytest.fixture
    def mock_exchange(self):
        """Create a mock CCXT Pro exchange."""
        exchange = AsyncMock()
        exchange.fetch_status = AsyncMock(return_value={"status": "ok"})
        exchange.close = AsyncMock()
        return exchange

    @pytest.fixture
    def mock_bridge(self):
        """Create a mock AsyncThreadBridge."""
        bridge = MagicMock(spec=AsyncThreadBridge)
        return bridge

    @pytest.fixture
    def manager(self, mock_exchange, mock_bridge):
        """Create a WebSocketManager instance."""
        return WebSocketManager(
            exchange=mock_exchange,
            event_bridge=mock_bridge,
            adapter_name="TestAdapter"
        )

    @pytest.mark.asyncio
    async def test_initialization(self, manager, mock_exchange, mock_bridge):
        """Test manager initialization."""
        assert manager.exchange == mock_exchange
        assert manager.event_bridge == mock_bridge
        assert manager.adapter_name == "TestAdapter"
        assert manager.connection_state == ConnectionState.DISCONNECTED
        assert len(manager.subscriptions) == 0
        assert manager._heartbeat_interval == 30.0

    @pytest.mark.asyncio
    async def test_connect_success(self, manager, mock_exchange):
        """Test successful connection."""
        result = await manager.connect()
        
        assert result is True
        assert manager.connection_state == ConnectionState.CONNECTED
        mock_exchange.fetch_status.assert_called_once()
        assert manager._heartbeat_task is not None

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, manager):
        """Test connecting when already connected."""
        manager.connection_state = ConnectionState.CONNECTED
        
        with patch.object(manager.logger, 'info') as mock_log:
            result = await manager.connect()
            assert result is True
            mock_log.assert_called_with("WebSocket already connected")

    @pytest.mark.asyncio
    async def test_connect_timeout(self, manager, mock_exchange):
        """Test connection timeout."""
        # Make fetch_status hang
        async def slow_fetch():
            await asyncio.sleep(15)  # Longer than timeout
            
        mock_exchange.fetch_status = slow_fetch
        
        result = await manager.connect()
        
        assert result is False
        assert manager.connection_state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_connect_exception(self, manager, mock_exchange):
        """Test connection with exception."""
        mock_exchange.fetch_status.side_effect = Exception("Connection error")
        
        result = await manager.connect()
        
        assert result is False
        assert manager.connection_state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_exchange):
        """Test graceful disconnection."""
        # First connect
        manager.connection_state = ConnectionState.CONNECTED
        manager._heartbeat_task = asyncio.create_task(asyncio.sleep(10))
        
        await manager.disconnect()
        
        assert manager.connection_state == ConnectionState.DISCONNECTED
        mock_exchange.close.assert_called_once()
        assert manager._heartbeat_task.cancelled()

    @pytest.mark.asyncio
    async def test_disconnect_when_already_disconnected(self, manager):
        """Test disconnecting when already disconnected."""
        manager.connection_state = ConnectionState.DISCONNECTED
        
        await manager.disconnect()  # Should not raise

    @pytest.mark.asyncio
    async def test_add_remove_subscription(self, manager):
        """Test adding and removing subscriptions."""
        # Add subscription
        await manager.add_subscription("BTCUSDT")
        assert "BTCUSDT" in manager.subscriptions
        
        # Add duplicate
        await manager.add_subscription("BTCUSDT")
        assert len(manager.subscriptions) == 1
        
        # Remove subscription
        await manager.remove_subscription("BTCUSDT")
        assert "BTCUSDT" not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_handle_reconnection_success(self, manager):
        """Test successful reconnection."""
        manager.connection_state = ConnectionState.ERROR
        
        # Mock successful connect
        async def mock_connect():
            manager.connection_state = ConnectionState.CONNECTED
            return True
            
        manager.connect = mock_connect
        manager.restore_subscriptions = AsyncMock()
        
        result = await manager.handle_reconnection()
        
        assert result is True
        assert manager.reconnect_manager.reconnect_attempts == 1
        manager.restore_subscriptions.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_reconnection_max_attempts(self, manager):
        """Test reconnection with max attempts reached."""
        # Simulate max attempts
        manager.reconnect_manager.reconnect_attempts = 50
        
        result = await manager.handle_reconnection()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_restore_subscriptions(self, manager):
        """Test restoring subscriptions after reconnection."""
        # Add some subscriptions
        manager.subscriptions = {"BTCUSDT", "ETHUSDT", "BNBUSDT"}
        
        with patch.object(manager.logger, 'info') as mock_log:
            await manager.restore_subscriptions()
            
            # Check logging
            mock_log.assert_any_call("Restoring 3 subscriptions")
            mock_log.assert_any_call("Restored 3/3 subscriptions")

    @pytest.mark.asyncio
    async def test_heartbeat_monitoring(self, manager):
        """Test heartbeat monitoring functionality."""
        manager.connection_state = ConnectionState.CONNECTED
        
        # Test heartbeat update
        initial_time = manager._last_heartbeat
        time.sleep(0.1)
        manager.update_heartbeat()
        
        assert manager._last_heartbeat > initial_time

    @pytest.mark.asyncio
    async def test_connection_info(self, manager):
        """Test getting connection information."""
        manager.connection_state = ConnectionState.CONNECTED
        manager.subscriptions = {"BTCUSDT", "ETHUSDT"}
        manager.reconnect_manager.reconnect_attempts = 2
        
        info = manager.get_connection_info()
        
        assert info["state"] == "connected"
        assert info["subscriptions"] == 2
        assert info["reconnect_attempts"] == 2
        assert "last_heartbeat" in info
        assert "uptime" in info

    @pytest.mark.asyncio
    async def test_is_connected(self, manager):
        """Test connection state checking."""
        # Initially disconnected
        assert not manager.is_connected()
        
        # Set to connected
        manager.connection_state = ConnectionState.CONNECTED
        assert manager.is_connected()
        
        # Other states
        manager.connection_state = ConnectionState.CONNECTING
        assert not manager.is_connected()
        
        manager.connection_state = ConnectionState.ERROR
        assert not manager.is_connected()

    @pytest.mark.asyncio
    async def test_cancel_subscription_tasks(self, manager):
        """Test cancelling subscription tasks."""
        # Create some mock tasks
        task1 = asyncio.create_task(asyncio.sleep(10))
        task2 = asyncio.create_task(asyncio.sleep(10))
        
        manager._subscription_tasks = {
            "BTCUSDT": task1,
            "ETHUSDT": task2
        }
        
        await manager._cancel_all_subscriptions()
        
        assert task1.cancelled()
        assert task2.cancelled()
        assert len(manager._subscription_tasks) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_timeout_detection(self, manager):
        """Test detection of stale connection via heartbeat."""
        manager.connection_state = ConnectionState.CONNECTED
        manager._heartbeat_interval = 0.1  # Short interval for testing
        
        # Set last heartbeat to old time
        manager._last_heartbeat = time.time() - 1.0
        
        # Start heartbeat monitor
        manager._start_heartbeat_monitor()
        
        # Wait for heartbeat check
        await asyncio.sleep(0.2)
        
        # Should detect stale connection
        assert manager.connection_state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_remove_subscription_with_task(self, manager):
        """Test removing subscription that has an active task."""
        # Create a mock task
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_task.cancel = MagicMock()
        
        manager.subscriptions.add("BTCUSDT")
        manager._subscription_tasks["BTCUSDT"] = mock_task
        
        await manager.remove_subscription("BTCUSDT")
        
        assert "BTCUSDT" not in manager.subscriptions
        assert "BTCUSDT" not in manager._subscription_tasks
        mock_task.cancel.assert_called_once()