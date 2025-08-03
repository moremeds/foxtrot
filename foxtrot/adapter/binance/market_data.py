"""
Binance Market Data Manager - Handles real-time market data streaming.

This module manages real-time market data subscriptions and WebSocket connections
for tick data streaming.
"""

from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING

from foxtrot.util.constants import Exchange
from foxtrot.util.object import SubscribeRequest, TickData

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


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
        self._ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self._ws_thread.start()

    def _stop_websocket(self) -> None:
        """Stop WebSocket connection thread with improved cleanup."""
        self._active = False
        if self._ws_thread and self._ws_thread.is_alive():
            # First attempt: normal join with timeout
            self._ws_thread.join(timeout=2.0)
            
            # If thread is still alive, log warning (thread cleanup issue)
            if self._ws_thread.is_alive():
                self.api_client._log_warning("WebSocket thread did not terminate cleanly")

    def _run_websocket(self) -> None:
        """Run WebSocket connection (simplified implementation)."""
        try:
            while self._active:
                # Simplified implementation - fetch ticker data periodically
                # In a full implementation, this would use WebSocket streaming
                for symbol in list(self._subscribed_symbols):
                    if not self._active:  # Check active status within loop
                        break
                    try:
                        tick_data = self._fetch_tick_data(symbol)
                        if tick_data:
                            self._on_tick_data(tick_data)
                    except Exception as e:
                        self.api_client._log_error(f"Error fetching data for {symbol}: {str(e)}")

                # Rate limiting with early exit check
                if self._active:
                    time.sleep(1)

        except Exception as e:
            self.api_client._log_error(f"WebSocket error: {str(e)}")
        finally:
            self._active = False

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
        # In a full implementation, this would publish the tick data
        # to the event engine or call a callback function

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
