"""
Mock setup for CCXT library to enable testing without the actual ccxt package.
This module must be imported before any foxtrot.adapter.binance modules.
"""

import sys
from unittest.mock import Mock

# Create mock ccxt module
mock_ccxt = Mock()

# Mock exchange classes
mock_binance = Mock()
mock_binance_instance = Mock()

# Mock exchange methods
mock_binance_instance.load_markets = Mock(return_value={})
mock_binance_instance.create_order = Mock(return_value={"id": "12345", "status": "open"})
mock_binance_instance.cancel_order = Mock(return_value={"id": "12345", "status": "canceled"})
mock_binance_instance.fetch_balance = Mock(
    return_value={"BTC": {"free": 1.0, "used": 0.0, "total": 1.0}}
)
mock_binance_instance.fetch_positions = Mock(return_value=[])
mock_binance_instance.fetch_trades = Mock(return_value=[])
mock_binance_instance.fetch_orders = Mock(return_value=[])
mock_binance_instance.fetch_open_orders = Mock(return_value=[])
mock_binance_instance.fetch_closed_orders = Mock(return_value=[])
mock_binance_instance.fetch_ohlcv = Mock(return_value=[])
mock_binance_instance.fetch_ticker = Mock(return_value={"symbol": "BTC/USDT", "last": 50000})
mock_binance_instance.fetch_order_book = Mock(return_value={"bids": [], "asks": []})

# Mock WebSocket functionality
mock_binance_instance.watch_ticker = Mock()
mock_binance_instance.watch_trades = Mock()
mock_binance_instance.watch_order_book = Mock()

# Mock connection status
mock_binance_instance.has = {
    "ws": True,
    "watchTicker": True,
    "watchTrades": True,
    "watchOrderBook": True,
    "fetchOHLCV": True,
    "createOrder": True,
    "cancelOrder": True,
}

# Setup mock binance class
mock_binance.return_value = mock_binance_instance

# Mock ccxt module structure
mock_ccxt.binance = mock_binance
mock_ccxt.Exchange = Mock()
mock_ccxt.BaseError = Exception
mock_ccxt.NetworkError = Exception
mock_ccxt.ExchangeError = Exception
mock_ccxt.OrderNotFound = Exception
mock_ccxt.InvalidOrder = Exception


# Mock exchange errors
class MockBaseError(Exception):
    pass


class MockNetworkError(MockBaseError):
    pass


class MockExchangeError(MockBaseError):
    pass


class MockOrderNotFound(MockExchangeError):
    pass


class MockInvalidOrder(MockExchangeError):
    pass


mock_ccxt.BaseError = MockBaseError
mock_ccxt.NetworkError = MockNetworkError
mock_ccxt.ExchangeError = MockExchangeError
mock_ccxt.OrderNotFound = MockOrderNotFound
mock_ccxt.InvalidOrder = MockInvalidOrder

# Install mock in sys.modules
sys.modules["ccxt"] = mock_ccxt
