"""
Binance Market Data Manager - Handles real-time market data streaming.

This module manages real-time market data subscriptions and WebSocket connections
for tick data streaming.
"""

import asyncio
from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING, Optional

from foxtrot.core.event import Event
from foxtrot.util.constants import Exchange
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import SubscribeRequest, TickData
from foxtrot.util.websocket_utils import AsyncThreadBridge

if TYPE_CHECKING:
    from .api_client import BinanceApiClient
    from .websocket_manager import WebSocketManager


class BinanceMarketData:
    """
    Manager for Binance real-time market data.

    Handles WebSocket connections and market data subscriptions.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the market data manager."""
        self.api_client = api_client
        self._subscribed_symbols: set[str] = set()
        self._ws_thread: threading.Thread | None = None
        self._active = False
        self._shutdown_event = threading.Event()  # Added for proper shutdown signaling
        self._shutdown_timeout = 30.0  # 30 seconds timeout for WebSocket cleanup
        
        # WebSocket components
        self.async_bridge: Optional[AsyncThreadBridge] = None
        self.websocket_manager: Optional["WebSocketManager"] = None
        self._websocket_tasks: dict[str, asyncio.Task] = {}

    def subscribe(self, req: SubscribeRequest) -> bool:
        """
        Subscribe to market data for a symbol.

        Args:
            req: Subscription request

        Returns:
            True if subscription successful, False otherwise
        """
        try:
            if not self.api_client.exchange:
                return False

            symbol = req.symbol
            if symbol in self._subscribed_symbols:
                self.api_client._log_info(f"Already subscribed to {symbol}")
                return True

            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(symbol)
            if not ccxt_symbol:
                self.api_client._log_error(f"Invalid symbol: {symbol}")
                return False

            # Add to subscribed symbols
            self._subscribed_symbols.add(symbol)

            # Start WebSocket thread if not active
            if not self._active:
                self._start_websocket()

            self.api_client._log_info(f"Subscribed to {symbol}")
            return True

        except Exception as e:
            self.api_client._log_error(f"Failed to subscribe to {req.symbol}: {str(e)}")
            return False

    def unsubscribe(self, symbol: str) -> bool:
        """
        Unsubscribe from market data for a symbol.

        Args:
            symbol: Symbol to unsubscribe from

        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                self.api_client._log_info(f"Unsubscribed from {symbol}")

                # Stop WebSocket if no more subscriptions
                if not self._subscribed_symbols and self._active:
                    self._stop_websocket()

                return True
            return False

        except Exception as e:
            self.api_client._log_error(f"Failed to unsubscribe from {symbol}: {str(e)}")
            return False

    def close(self) -> None:
        """Close all market data connections."""
        try:
            self._stop_websocket()
            self._subscribed_symbols.clear()
            self.api_client._log_info("Market data connections closed")

        except Exception as e:
            self.api_client._log_error(f"Error closing market data: {str(e)}")

    def _start_websocket(self) -> None:
        """Start WebSocket connection thread."""
        if self._active:
            return

        self._active = True
        self._shutdown_event.clear()  # Clear shutdown event for new session
        
        # Check if WebSocket is enabled for this adapter
        if self.api_client.is_websocket_enabled():
            # Initialize WebSocket components
            self._initialize_websocket_components()
            # Use async WebSocket implementation (non-daemon for proper cleanup)
            self._ws_thread = threading.Thread(
                target=self._run_websocket_async, 
                name="BinanceMarketData-WebSocket",
                daemon=False  # Changed from True for proper shutdown handling
            )
        else:
            # Fall back to HTTP polling (non-daemon for proper cleanup)
            self._ws_thread = threading.Thread(
                target=self._run_websocket, 
                name="BinanceMarketData-Polling",
                daemon=False  # Changed from True for proper shutdown handling
            )
            
        self._ws_thread.start()

    def _stop_websocket(self) -> None:
        """Stop WebSocket connection thread with improved cleanup and proper timeout."""
        if not self._active:
            return
            
        self.api_client._log_info("Initiating WebSocket shutdown")
        self._active = False
        self._shutdown_event.set()  # Signal shutdown to thread
        
        # Cancel any WebSocket tasks if using async implementation
        if self.async_bridge and self.api_client.is_websocket_enabled():
            # Cancel all WebSocket tasks
            for symbol, task in self._websocket_tasks.items():
                self.async_bridge.call_soon_threadsafe(task.cancel)
                
        if self._ws_thread and self._ws_thread.is_alive():
            # Wait for thread to finish with proper timeout
            self._ws_thread.join(timeout=self._shutdown_timeout)
            
            # If thread is still alive after timeout, log error
            if self._ws_thread.is_alive():
                self.api_client._log_error(
                    f"WebSocket thread did not terminate within {self._shutdown_timeout}s timeout"
                )

    def _run_websocket(self) -> None:
        """Run WebSocket connection (simplified implementation) with proper shutdown handling."""
        try:
            self.api_client._log_info("Starting HTTP polling mode")
            
            while self._active and not self._shutdown_event.is_set():
                # Simplified implementation - fetch ticker data periodically
                # In a full implementation, this would use WebSocket streaming
                for symbol in list(self._subscribed_symbols):
                    if not self._active or self._shutdown_event.is_set():
                        break
                    try:
                        tick_data = self._fetch_tick_data(symbol)
                        if tick_data:
                            self._on_tick_data(tick_data)
                    except Exception as e:
                        self.api_client._log_error(f"Error fetching data for {symbol}: {str(e)}")

                # Rate limiting with shutdown check
                if self._active and not self._shutdown_event.is_set():
                    # Use wait with timeout to be responsive to shutdown
                    self._shutdown_event.wait(timeout=1.0)

        except Exception as e:
            self.api_client._log_error(f"WebSocket error: {str(e)}")
        finally:
            self._active = False
            self.api_client._log_info("HTTP polling mode terminated")

    def _fetch_tick_data(self, symbol: str) -> TickData | None:
        """
        Fetch current tick data for a symbol.

        Args:
            symbol: Symbol to fetch data for

        Returns:
            TickData if successful, None otherwise
        """
        try:
            if not self.api_client.exchange:
                return None

            ccxt_symbol = self._convert_symbol_to_ccxt(symbol)
            if not ccxt_symbol:
                return None

            # Fetch ticker data
            ticker = self.api_client.exchange.fetch_ticker(ccxt_symbol)
            if not ticker:
                return None

            return TickData(
                adapter_name=self.api_client.adapter_name,
                symbol=symbol,
                exchange=Exchange.BINANCE,
                datetime=datetime.now(),
                name=ccxt_symbol,
                volume=ticker.get("baseVolume", 0),
                turnover=ticker.get("quoteVolume", 0),
                open_price=ticker.get("open", 0),
                high_price=ticker.get("high", 0),
                low_price=ticker.get("low", 0),
                last_price=ticker.get("last", 0),
                last_volume=0,  # Not available in ticker
                limit_up=0,  # Not available
                limit_down=0,  # Not available
                open_interest=0,  # Not available for spot
                pre_close=ticker.get("previousClose", 0),
                bid_price_1=ticker.get("bid", 0),
                bid_volume_1=0,  # Would need order book data
                ask_price_1=ticker.get("ask", 0),
                ask_volume_1=0,  # Would need order book data
            )

        except Exception as e:
            self.api_client._log_error(f"Failed to fetch tick data for {symbol}: {str(e)}")
            return None

    def _on_tick_data(self, tick: TickData) -> None:
        """Handle incoming tick data."""
        # Emit tick event to the event engine
        if self.api_client.event_engine:
            event = Event(EVENT_TICK, tick)
            self.api_client.event_engine.put(event)

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """
        Convert VT symbol format to CCXT format.

        Args:
            vt_symbol: Symbol in VT format (e.g., "BTCUSDT.BINANCE")

        Returns:
            Symbol in CCXT format (e.g., "BTC/USDT")
        """
        try:
            symbol = vt_symbol.split(".")[0]

            # Validate symbol format
            if len(symbol) < 4:
                return ""

            # Convert BTCUSDT to BTC/USDT format
            if symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            if symbol.endswith("BTC") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            if symbol.endswith("ETH") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            # Invalid symbol format
            return ""
        except Exception:
            return ""
            
    def _initialize_websocket_components(self) -> None:
        """Initialize WebSocket components."""
        if not self.async_bridge:
            self.async_bridge = AsyncThreadBridge(self.api_client.event_engine)
            
        if not self.websocket_manager:
            from .websocket_manager import WebSocketManager
            self.websocket_manager = WebSocketManager(
                self.api_client.exchange_pro,
                self.async_bridge,
                self.api_client.adapter_name
            )
            
    def _run_websocket_async(self) -> None:
        """Run WebSocket connection with async implementation and proper shutdown handling."""
        try:
            self.api_client._log_info("Starting async WebSocket mode")
            
            # Start the async bridge with proper timeout
            self.async_bridge.start()
            
            # Run the async WebSocket loop
            future = self.async_bridge.run_async_in_thread(self._async_websocket_loop())
            
            # Wait for completion or interruption
            while self._active and not self._shutdown_event.is_set():
                if future.done():
                    # Check if there was an exception
                    exc = future.exception()
                    if exc:
                        self.api_client._log_error(f"WebSocket loop error: {exc}")
                        # Attempt reconnection if not shutting down
                        if self._active and not self._shutdown_event.is_set():
                            # Wait with shutdown check
                            if self._shutdown_event.wait(timeout=5.0):
                                break  # Shutdown requested during wait
                            future = self.async_bridge.run_async_in_thread(self._async_websocket_loop())
                    else:
                        break
                        
                # Check for shutdown more frequently
                self._shutdown_event.wait(timeout=0.1)
                
        except Exception as e:
            self.api_client._log_error(f"WebSocket thread error: {str(e)}")
        finally:
            self.api_client._log_info("Stopping async WebSocket mode")
            
            # Cleanup with proper timeout
            if self.async_bridge:
                shutdown_success = self.async_bridge.stop(timeout=self._shutdown_timeout)
                if not shutdown_success:
                    self.api_client._log_error("AsyncThreadBridge shutdown timeout")
                    
            self._active = False
            self.api_client._log_info("Async WebSocket mode terminated")
            
    async def _async_websocket_loop(self) -> None:
        """Main WebSocket event loop with connection management."""
        if not self.websocket_manager:
            return
            
        try:
            # Establish WebSocket connection
            connected = await self.websocket_manager.connect()
            if not connected:
                self.api_client._log_error("Failed to establish WebSocket connection")
                return
                
            # Start watching subscribed symbols
            while self._active and not self._shutdown_event.is_set():
                try:
                    # Create watch tasks for all subscribed symbols
                    watch_tasks = []
                    for symbol in list(self._subscribed_symbols):
                        if not self.api_client.is_websocket_enabled(symbol):
                            continue
                            
                        # Add subscription to manager for restoration
                        await self.websocket_manager.add_subscription(symbol)
                        
                        # Create watch task
                        task = asyncio.create_task(self._watch_symbol(symbol))
                        watch_tasks.append(task)
                        self._websocket_tasks[symbol] = task
                        
                    if not watch_tasks:
                        # No symbols to watch, wait briefly
                        await asyncio.sleep(1)
                        continue
                        
                    # Wait for any task to complete or fail
                    done, pending = await asyncio.wait(
                        watch_tasks,
                        return_when=asyncio.FIRST_EXCEPTION
                    )
                    
                    # Check for exceptions
                    for task in done:
                        if task.exception():
                            self.api_client._log_error(f"Watch task error: {task.exception()}")
                            
                except Exception as e:
                    self.api_client._log_error(f"WebSocket loop error: {e}")
                    # Attempt reconnection
                    if self._active:
                        success = await self.websocket_manager.handle_reconnection()
                        if not success:
                            self.api_client._log_error("Failed to reconnect, falling back to HTTP polling")
                            self._active = False
                            break
                            
        except Exception as e:
            self.api_client._log_error(f"Fatal WebSocket error: {e}")
        finally:
            # Cleanup
            await self._cleanup_websocket_tasks()
            if self.websocket_manager:
                await self.websocket_manager.disconnect()
                
    async def _watch_symbol(self, symbol: str) -> None:
        """Watch individual symbol with real-time WebSocket updates."""
        ccxt_symbol = self._convert_symbol_to_ccxt(symbol)
        if not ccxt_symbol:
            self.api_client._log_error(f"Invalid symbol format: {symbol}")
            return
            
        try:
            while self._active and symbol in self._subscribed_symbols and not self._shutdown_event.is_set():
                # Use CCXT Pro's watchTicker method
                ticker = await self.api_client.exchange_pro.watchTicker(ccxt_symbol)
                
                # Update heartbeat
                if self.websocket_manager:
                    self.websocket_manager.update_heartbeat()
                
                # Convert to TickData
                tick_data = self._convert_ticker_to_tick(ticker, symbol)
                
                # Emit event through the bridge
                if tick_data:
                    event = Event(EVENT_TICK, tick_data)
                    self.async_bridge.emit_event_threadsafe(event)
                    
        except asyncio.CancelledError:
            # Task was cancelled, normal shutdown
            pass
        except Exception as e:
            self.api_client._log_error(f"Error watching {symbol}: {e}")
            # Remove from WebSocket tasks
            self._websocket_tasks.pop(symbol, None)
            
    def _convert_ticker_to_tick(self, ticker: dict, vt_symbol: str) -> Optional[TickData]:
        """Convert CCXT ticker data to TickData object."""
        try:
            return TickData(
                adapter_name=self.api_client.adapter_name,
                symbol=vt_symbol,
                exchange=Exchange.BINANCE,
                datetime=datetime.fromtimestamp(ticker.get("timestamp", 0) / 1000),
                name=ticker.get("symbol", ""),
                volume=ticker.get("baseVolume", 0) or 0,
                turnover=ticker.get("quoteVolume", 0) or 0,
                open_price=ticker.get("open", 0) or 0,
                high_price=ticker.get("high", 0) or 0,
                low_price=ticker.get("low", 0) or 0,
                last_price=ticker.get("last", 0) or 0,
                last_volume=0,  # Not available in ticker
                limit_up=0,  # Not available
                limit_down=0,  # Not available
                open_interest=0,  # Not available for spot
                pre_close=ticker.get("previousClose", 0) or 0,
                bid_price_1=ticker.get("bid", 0) or 0,
                bid_volume_1=ticker.get("bidVolume", 0) or 0,
                ask_price_1=ticker.get("ask", 0) or 0,
                ask_volume_1=ticker.get("askVolume", 0) or 0,
            )
        except Exception as e:
            self.api_client._log_error(f"Failed to convert ticker data: {e}")
            return None
            
    async def _cleanup_websocket_tasks(self) -> None:
        """Cancel and cleanup all WebSocket tasks."""
        tasks = list(self._websocket_tasks.values())
        for task in tasks:
            if not task.done():
                task.cancel()
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        self._websocket_tasks.clear()
