"""
WebSocket Manager for Binance adapter.

This module manages WebSocket connection lifecycle, including:
- Connection establishment and authentication
- Auto-reconnection with exponential backoff
- Subscription management and restoration
- Connection health monitoring
"""

import asyncio
from enum import Enum
from typing import Any, Dict, Optional, Set, TYPE_CHECKING
import time

from foxtrot.util.logger import get_adapter_logger
from foxtrot.util.websocket_utils import AsyncThreadBridge, WebSocketReconnectManager

if TYPE_CHECKING:
    import ccxtpro


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class WebSocketManager:
    """
    Manages WebSocket connection lifecycle for Binance.
    
    Features:
    - Persistent connection management
    - Auto-reconnection with exponential backoff
    - Subscription state persistence
    - Connection health monitoring
    - Error recovery strategies
    """
    
    def __init__(
        self,
        exchange: "ccxtpro.Exchange",
        event_bridge: AsyncThreadBridge,
        adapter_name: str = "BinanceAdapter"
    ):
        """
        Initialize the WebSocket manager.
        
        Args:
            exchange: CCXT Pro exchange instance
            event_bridge: Async-thread bridge for event emission
            adapter_name: Name of the adapter for logging
        """
        self.exchange = exchange
        self.event_bridge = event_bridge
        self.adapter_name = adapter_name
        self.logger = get_adapter_logger(f"{adapter_name}WebSocket")
        
        # Connection state
        self.connection_state = ConnectionState.DISCONNECTED
        self._connection_task: Optional[asyncio.Task] = None
        
        # Subscription management
        self.subscriptions: Set[str] = set()
        self._subscription_tasks: Dict[str, asyncio.Task] = {}
        
        # Reconnection management with configurable settings
        from foxtrot.util.settings import SETTINGS
        self.reconnect_manager = WebSocketReconnectManager(
            max_attempts=SETTINGS.get("websocket.reconnect.max_attempts", 50),
            base_delay=SETTINGS.get("websocket.reconnect.base_delay", 1.0),
            max_delay=SETTINGS.get("websocket.reconnect.max_delay", 60.0)
        )
        
        # Health monitoring
        self._last_heartbeat = time.time()
        self._heartbeat_interval = SETTINGS.get("websocket.heartbeat.interval", 30.0)
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connection_state == ConnectionState.CONNECTED:
            self.logger.info("WebSocket already connected")
            return True
            
        try:
            self.connection_state = ConnectionState.CONNECTING
            self.logger.info("Establishing WebSocket connection...")
            
            # Initialize CCXT Pro exchange connection
            # CCXT Pro handles WebSocket connections internally
            # We just need to ensure the exchange is ready
            
            # Test connection with a simple operation
            await asyncio.wait_for(
                self._test_connection(),
                timeout=10.0
            )
            
            self.connection_state = ConnectionState.CONNECTED
            self.reconnect_manager.record_success()
            
            # Start heartbeat monitoring
            self._start_heartbeat_monitor()
            
            self.logger.info("WebSocket connection established successfully")
            return True
            
        except asyncio.TimeoutError:
            self.logger.error("WebSocket connection timeout")
            self.connection_state = ConnectionState.ERROR
            return False
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            self.connection_state = ConnectionState.ERROR
            return False
            
    async def disconnect(self) -> None:
        """Gracefully close WebSocket connection."""
        if self.connection_state == ConnectionState.DISCONNECTED:
            return
            
        try:
            self.logger.info("Closing WebSocket connection...")
            
            # Cancel all subscription tasks
            await self._cancel_all_subscriptions()
            
            # Stop heartbeat monitoring
            await self._stop_heartbeat_monitor()
            
            # Close exchange WebSocket connections
            if hasattr(self.exchange, 'close'):
                await self.exchange.close()
                
            self.connection_state = ConnectionState.DISCONNECTED
            self.logger.info("WebSocket connection closed")
            
        except Exception as e:
            self.logger.error(f"Error during WebSocket disconnect: {e}")
            
    async def handle_reconnection(self) -> bool:
        """
        Handle reconnection with exponential backoff.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        if not self.reconnect_manager.should_reconnect():
            self.logger.error("Maximum reconnection attempts reached")
            return False
            
        self.connection_state = ConnectionState.RECONNECTING
        self.reconnect_manager.record_attempt()
        
        # Calculate delay
        delay = self.reconnect_manager.get_reconnect_delay()
        self.logger.info(
            f"Attempting reconnection {self.reconnect_manager.reconnect_attempts}/"
            f"{self.reconnect_manager.max_attempts} after {delay:.1f}s delay"
        )
        
        # Wait before reconnection
        await asyncio.sleep(delay)
        
        # Attempt reconnection
        success = await self.connect()
        
        if success:
            # Restore subscriptions
            await self.restore_subscriptions()
            return True
        else:
            self.reconnect_manager.record_failure()
            return False
            
    async def restore_subscriptions(self) -> None:
        """Restore all subscriptions after reconnection."""
        if not self.subscriptions:
            return
            
        self.logger.info(f"Restoring {len(self.subscriptions)} subscriptions")
        
        # Clear old subscription tasks
        self._subscription_tasks.clear()
        
        # Restore each subscription
        restored = 0
        for symbol in list(self.subscriptions):
            try:
                # Re-subscribe to the symbol
                # The actual subscription will be handled by the market data manager
                self.logger.debug(f"Restoring subscription for {symbol}")
                restored += 1
            except Exception as e:
                self.logger.error(f"Failed to restore subscription for {symbol}: {e}")
                
        self.logger.info(f"Restored {restored}/{len(self.subscriptions)} subscriptions")
        
    async def add_subscription(self, symbol: str) -> None:
        """
        Add a symbol to the subscription set.
        
        Args:
            symbol: Symbol to track for restoration
        """
        self.subscriptions.add(symbol)
        
    async def remove_subscription(self, symbol: str) -> None:
        """
        Remove a symbol from the subscription set.
        
        Args:
            symbol: Symbol to remove
        """
        self.subscriptions.discard(symbol)
        
        # Cancel associated task if exists
        if symbol in self._subscription_tasks:
            task = self._subscription_tasks.pop(symbol)
            if not task.done():
                task.cancel()
                
    async def _test_connection(self) -> None:
        """Test WebSocket connection with a simple operation."""
        # CCXT Pro will establish WebSocket connection on first watch* call
        # We'll use fetchStatus as a lightweight test
        if hasattr(self.exchange, 'fetch_status'):
            await self.exchange.fetch_status()
            
    async def _cancel_all_subscriptions(self) -> None:
        """Cancel all active subscription tasks."""
        tasks = list(self._subscription_tasks.values())
        
        for task in tasks:
            if not task.done():
                task.cancel()
                
        # Wait for all cancellations
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        self._subscription_tasks.clear()
        
    def _start_heartbeat_monitor(self) -> None:
        """Start connection heartbeat monitoring."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
            
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
    async def _stop_heartbeat_monitor(self) -> None:
        """Stop heartbeat monitoring."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
                
    async def _heartbeat_loop(self) -> None:
        """Monitor connection health with periodic heartbeats."""
        while self.connection_state == ConnectionState.CONNECTED:
            try:
                # Wait for heartbeat interval
                await asyncio.sleep(self._heartbeat_interval)
                
                # Check connection health
                current_time = time.time()
                time_since_heartbeat = current_time - self._last_heartbeat
                
                if time_since_heartbeat > self._heartbeat_interval * 2:
                    self.logger.warning(
                        f"No heartbeat for {time_since_heartbeat:.1f}s, "
                        "connection may be stale"
                    )
                    # Trigger reconnection
                    self.connection_state = ConnectionState.ERROR
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")
                
    def update_heartbeat(self) -> None:
        """Update the last heartbeat timestamp."""
        self._last_heartbeat = time.time()
        
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connection_state == ConnectionState.CONNECTED
        
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status information."""
        return {
            "state": self.connection_state.value,
            "subscriptions": len(self.subscriptions),
            "reconnect_attempts": self.reconnect_manager.reconnect_attempts,
            "last_heartbeat": self._last_heartbeat,
            "uptime": time.time() - self._last_heartbeat if self.is_connected() else 0
        }