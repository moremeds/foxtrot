"""
Crypto Market Data Manager - Handles real-time market data streaming.
"""

from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING

from foxtrot.util.constants import Exchange
from foxtrot.util.object import BarData, HistoryRequest, SubscribeRequest, TickData

if TYPE_CHECKING:
    from .crypto_adapter import CryptoAdapter


class MarketData:
    """
    Manager for Crypto real-time market data.
    """

    def __init__(self, adapter: "CryptoAdapter"):
        """Initialize the market data manager."""
        self.adapter = adapter
        self._subscribed_symbols: set[str] = set()
        self._ws_thread: threading.Thread | None = None
        self._active = False

    def subscribe(self, req: SubscribeRequest) -> bool:
        """
        Subscribe to market data for a symbol.
        """
        try:
            if not self.adapter.exchange:
                return False

            symbol = req.symbol
            if symbol in self._subscribed_symbols:
                print(f"Already subscribed to {symbol}")
                return True

            ccxt_symbol = self._convert_symbol_to_ccxt(symbol)
            if not ccxt_symbol:
                print(f"Invalid symbol: {symbol}")
                return False

            self._subscribed_symbols.add(symbol)

            if not self._active:
                self._start_websocket()

            print(f"Subscribed to {symbol}")
            return True

        except Exception as e:
            print(f"Failed to subscribe to {req.symbol}: {str(e)}")
            return False

    def unsubscribe(self, symbol: str) -> bool:
        """
        Unsubscribe from market data for a symbol.
        """
        try:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
                print(f"Unsubscribed from {symbol}")

                if not self._subscribed_symbols and self._active:
                    self._stop_websocket()

                return True
            return False

        except Exception as e:
            print(f"Failed to unsubscribe from {symbol}: {str(e)}")
            return False

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """
        Query historical data.
        """
        history = []
        try:
            if not self.adapter.exchange:
                return history

            ccxt_symbol = self._convert_symbol_to_ccxt(req.symbol)
            if not ccxt_symbol:
                return history

            # Implement logic to fetch historical data using ccxt

        except Exception as e:
            print(f"Failed to query history for {req.symbol}: {str(e)}")

        return history

    def close(self) -> None:
        """
        Close all market data connections.
        """
        try:
            self._stop_websocket()
            self._subscribed_symbols.clear()
            print("Market data connections closed")

        except Exception as e:
            print(f"Error closing market data: {str(e)}")

    def _start_websocket(self) -> None:
        """
        Start WebSocket connection thread.
        """
        if self._active:
            return

        self._active = True
        self._ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self._ws_thread.start()

    def _stop_websocket(self) -> None:
        """
        Stop WebSocket connection thread.
        """
        self._active = False
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5)

    def _run_websocket(self) -> None:
        """
        Run WebSocket connection.
        """
        try:
            while self._active:
                for symbol in list(self._subscribed_symbols):
                    try:
                        tick_data = self._fetch_tick_data(symbol)
                        if tick_data:
                            self.adapter.on_tick(tick_data)
                    except Exception as e:
                        print(f"Error fetching data for {symbol}: {str(e)}")

                time.sleep(1)

        except Exception as e:
            print(f"WebSocket error: {str(e)}")
        finally:
            self._active = False

    def _fetch_tick_data(self, symbol: str) -> TickData | None:
        """
        Fetch current tick data for a symbol.
        """
        try:
            if not self.adapter.exchange:
                return None

            ccxt_symbol = self._convert_symbol_to_ccxt(symbol)
            if not ccxt_symbol:
                return None

            ticker = self.adapter.exchange.fetch_ticker(ccxt_symbol)
            if not ticker:
                return None

            tick = TickData(
                adapter_name=self.adapter.adapter_name,
                symbol=symbol,
                exchange=Exchange(self.adapter.default_name),
                datetime=datetime.now(),
                name=ccxt_symbol,
                volume=ticker.get("baseVolume", 0),
                turnover=ticker.get("quoteVolume", 0),
                open_price=ticker.get("open", 0),
                high_price=ticker.get("high", 0),
                low_price=ticker.get("low", 0),
                last_price=ticker.get("last", 0),
                last_volume=0,
                limit_up=0,
                limit_down=0,
                open_interest=0,
                pre_close=ticker.get("previousClose", 0),
                bid_price_1=ticker.get("bid", 0),
                bid_volume_1=0,
                ask_price_1=ticker.get("ask", 0),
                ask_volume_1=0,
            )

            return tick

        except Exception as e:
            print(f"Failed to fetch tick data for {symbol}: {str(e)}")
            return None

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """
        Convert VT symbol format to CCXT format.
        """
        try:
            symbol = vt_symbol.split(".")[0]

            if len(symbol) < 4:
                return ""

            if symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            if symbol.endswith("BTC") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            if symbol.endswith("ETH") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            return ""
        except Exception:
            return ""
