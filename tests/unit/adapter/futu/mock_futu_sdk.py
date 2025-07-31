"""
Mock Futu SDK for testing purposes.

This module provides mock implementations of the Futu SDK classes
to enable comprehensive testing without requiring actual OpenD gateway connection.
"""

from datetime import datetime
import time
from typing import Any


# Mock Futu SDK constants and enums
class RET_OK:
    pass

RET_OK = 0
RET_ERROR = -1


class Market:
    HK = "HK"
    US = "US"
    CN_SH = "CN_SH"
    CN_SZ = "CN_SZ"


class TrdEnv:
    REAL = "REAL"
    SIMULATE = "SIMULATE"


class TrdMarket:
    HK = "HK"
    US = "US"
    CN = "CN"


class OrderType:
    NORMAL = "NORMAL"  # Limit order
    MARKET = "MARKET"  # Market order
    STOP = "STOP"      # Stop order


class TrdSide:
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus:
    NONE = "NONE"
    UNSUBMITTED = "UNSUBMITTED"
    WAITING_SUBMIT = "WAITING_SUBMIT"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    FILLED_PART = "FILLED_PART"
    FILLED_ALL = "FILLED_ALL"
    CANCELLED_PART = "CANCELLED_PART"  # Match real Futu SDK spelling
    CANCELLED_ALL = "CANCELLED_ALL"    # Match real Futu SDK spelling
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


class SecurityType:
    STOCK = "STOCK"
    ETF = "ETF"
    WARRANT = "WARRANT"


class SubType:
    QUOTE = "QUOTE"
    ORDER_BOOK = "ORDER_BOOK"
    TICKER = "TICKER"


class KLType:
    K_1M = "K_1M"
    K_5M = "K_5M"
    K_15M = "K_15M"
    K_30M = "K_30M"
    K_60M = "K_60M"
    K_DAY = "K_DAY"
    K_WEEK = "K_WEEK"
    K_MON = "K_MON"


class AuType:
    QFQ = "QFQ"  # Forward adjusted
    HFQ = "HFQ"  # Backward adjusted
    NONE = "NONE"  # No adjustment


class SysConfig:
    @staticmethod
    def set_init_rsa_file(file_path: str) -> bool:
        """Mock RSA key file setting."""
        return True


# Mock callback handler base classes
class StockQuoteHandlerBase:
    """Base class for stock quote callbacks."""

    def on_recv_rsp(self, rsp_pb: Any) -> None:
        """Mock callback for quote data."""


class TradeOrderHandlerBase:
    """Base class for trade order callbacks."""

    def on_recv_rsp(self, rsp_pb: Any) -> None:
        """Mock callback for trade data."""


class MockOpenQuoteContext:
    """Mock OpenQuoteContext for testing market data operations."""

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.connected = False
        self.subscriptions: dict[str, list[str]] = {}
        self.quote_handler: StockQuoteHandlerBase | None = None

    def start(self) -> tuple[int, str]:
        """Mock connection start."""
        self.connected = True
        return (RET_OK, "Success")

    def close(self) -> None:
        """Mock connection close."""
        self.connected = False

    def set_handler(self, handler: StockQuoteHandlerBase) -> None:
        """Mock handler setting."""
        self.quote_handler = handler

    def subscribe(self, code_list: list[str], subtype_list: list[str],
                  push: bool = True) -> tuple[int, str]:
        """Mock market data subscription."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        for code in code_list:
            if code not in self.subscriptions:
                self.subscriptions[code] = []
            self.subscriptions[code].extend(subtype_list)

        return (RET_OK, "Success")

    def unsubscribe(self, code_list: list[str], subtype_list: list[str]) -> tuple[int, str]:
        """Mock market data unsubscription."""
        for code in code_list:
            if code in self.subscriptions:
                for subtype in subtype_list:
                    if subtype in self.subscriptions[code]:
                        self.subscriptions[code].remove(subtype)
                if not self.subscriptions[code]:
                    del self.subscriptions[code]

        return (RET_OK, "Success")

    def get_stock_basicinfo(self, market: str, stock_type: str = SecurityType.STOCK) -> tuple[int, list[dict[str, Any]]]:
        """Mock stock basic info query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        # Mock stock data based on market
        mock_stocks = []
        if market == Market.HK:
            mock_stocks = [
                {"code": "HK.00700", "name": "Tencent Holdings", "stock_type": "STOCK"},
                {"code": "HK.00005", "name": "HSBC Holdings", "stock_type": "STOCK"},
                {"code": "HK.00941", "name": "China Mobile", "stock_type": "STOCK"},
            ]
        elif market == Market.US:
            mock_stocks = [
                {"code": "US.AAPL", "name": "Apple Inc", "stock_type": "STOCK"},
                {"code": "US.GOOGL", "name": "Alphabet Inc", "stock_type": "STOCK"},
                {"code": "US.TSLA", "name": "Tesla Inc", "stock_type": "STOCK"},
            ]
        elif market in [Market.CN_SH, Market.CN_SZ]:
            mock_stocks = [
                {"code": "CN.000001", "name": "Ping An Bank", "stock_type": "STOCK"},
                {"code": "CN.000002", "name": "China Vanke", "stock_type": "STOCK"},
            ]

        return (RET_OK, mock_stocks)

    def get_cur_kline(self, code: str, num: int = 100, kl_type: str = KLType.K_DAY,
                      autype: str = AuType.QFQ) -> tuple[int, list[dict[str, Any]]]:
        """Mock historical K-line data query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        # Generate mock K-line data
        mock_klines = []
        base_price = 100.0
        base_time = datetime.now()

        for i in range(num):
            price_variation = (i * 0.5) % 10 - 5  # Simple price movement
            open_price = base_price + price_variation
            high_price = open_price + abs(price_variation * 0.3)
            low_price = open_price - abs(price_variation * 0.2)
            close_price = open_price + price_variation * 0.1

            kline = {
                "time_key": (base_time.replace(hour=9, minute=30, second=0)).strftime("%Y-%m-%d %H:%M:%S"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": 1000000 + (i * 10000),
                "turnover": (open_price + close_price) / 2 * (1000000 + i * 10000),
            }
            mock_klines.append(kline)

        return (RET_OK, mock_klines)

    def simulate_quote_callback(self, code: str) -> None:
        """Simulate real-time quote callback for testing."""
        if self.quote_handler and code in self.subscriptions:
            # Create mock quote data
            mock_quote = {
                "code": code,
                "last_price": 100.0 + (time.time() % 10),
                "open_price": 99.5,
                "high_price": 101.2,
                "low_price": 98.8,
                "prev_close_price": 99.0,
                "volume": 1000000,
                "turnover": 100000000.0,
                "bid_price_1": 99.9,
                "ask_price_1": 100.1,
                "bid_vol_1": 10000,
                "ask_vol_1": 8000,
            }

            # Simulate callback
            self.quote_handler.on_recv_rsp(mock_quote)


class MockOpenHKTradeContext:
    """Mock OpenHKTradeContext for testing HK trading operations."""

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.connected = False
        self.unlocked = False
        self.orders: dict[str, dict[str, Any]] = {}
        self.order_counter = 1000
        self.trade_handler: TradeOrderHandlerBase | None = None

    def start(self) -> tuple[int, str]:
        """Mock connection start."""
        self.connected = True
        return (RET_OK, "Success")

    def close(self) -> None:
        """Mock connection close."""
        self.connected = False
        self.unlocked = False

    def set_handler(self, handler: TradeOrderHandlerBase) -> None:
        """Mock handler setting."""
        self.trade_handler = handler

    def unlock_trade(self, password: str, password_md5: str = "") -> tuple[int, str]:
        """Mock trading unlock."""
        if not self.connected:
            return (RET_ERROR, "Not connected")
        self.unlocked = True
        return (RET_OK, "Success")

    def place_order(self, price: float, qty: int, code: str, trd_side: str,
                    order_type: str = OrderType.NORMAL, trd_env: str = TrdEnv.SIMULATE) -> tuple[int, dict[str, Any]]:
        """Mock order placement."""
        if not self.connected:
            return (RET_ERROR, "Not connected")
        if not self.unlocked and trd_env == TrdEnv.REAL:
            return (RET_ERROR, "Trading not unlocked")

        order_id = str(self.order_counter)
        self.order_counter += 1

        order_data = {
            "order_id": order_id,
            "code": code,
            "trd_side": trd_side,
            "order_type": order_type,
            "price": price,
            "qty": qty,
            "dealt_qty": 0,
            "dealt_avg_price": 0.0,
            "order_status": OrderStatus.SUBMITTED,
            "trd_env": trd_env,
        }

        self.orders[order_id] = order_data
        return (RET_OK, order_data)

    def modify_order(self, modify_order_op: str, order_id: str, price: float = 0,
                     qty: int = 0, trd_env: str = TrdEnv.SIMULATE) -> tuple[int, dict[str, Any]]:
        """Mock order cancellation."""
        if not self.connected:
            return (RET_ERROR, "Not connected")
        if order_id not in self.orders:
            return (RET_ERROR, "Order not found")

        order = self.orders[order_id]
        order["order_status"] = OrderStatus.CANCELLED_ALL
        return (RET_OK, order)

    def accinfo_query(self, trd_env: str = TrdEnv.SIMULATE, trd_market: str = TrdMarket.HK) -> tuple[int, dict[str, Any]]:
        """Mock account info query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        mock_account = {
            "acc_id": "HK123456",
            "total_assets": 1000000.0,
            "frozen_cash": 50000.0,
            "avl_withdrawal_cash": 950000.0,
            "total_fee": 0.0,
            "margin_call_req": 0.0,
        }
        return (RET_OK, mock_account)

    def position_list_query(self, trd_env: str = TrdEnv.SIMULATE, trd_market: str = TrdMarket.HK) -> tuple[int, list[dict[str, Any]]]:
        """Mock position list query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        mock_positions = [
            {
                "code": "HK.00700",
                "qty": 1000,
                "frozen_qty": 0,
                "cost_price": 450.0,
                "unrealized_pl": 5000.0,
                "yesterday_qty": 1000,
            },
            {
                "code": "HK.00005",
                "qty": 500,
                "frozen_qty": 0,
                "cost_price": 65.0,
                "unrealized_pl": -1000.0,
                "yesterday_qty": 500,
            }
        ]
        return (RET_OK, mock_positions)

    def simulate_order_callback(self, order_id: str, status: str = OrderStatus.FILLED_ALL) -> None:
        """Simulate order status callback for testing."""
        if self.trade_handler and order_id in self.orders:
            order = self.orders[order_id].copy()
            order["order_status"] = status
            if status == OrderStatus.FILLED_ALL:
                order["dealt_qty"] = order["qty"]
                order["dealt_avg_price"] = order["price"]

            self.trade_handler.on_recv_rsp(order)


class MockOpenUSTradeContext(MockOpenHKTradeContext):
    """Mock OpenUSTradeContext for testing US trading operations."""

    def accinfo_query(self, trd_env: str = TrdEnv.SIMULATE, trd_market: str = TrdMarket.US) -> tuple[int, dict[str, Any]]:
        """Mock US account info query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        mock_account = {
            "acc_id": "US123456",
            "total_assets": 500000.0,
            "frozen_cash": 25000.0,
            "avl_withdrawal_cash": 475000.0,
            "total_fee": 0.0,
            "margin_call_req": 0.0,
        }
        return (RET_OK, mock_account)

    def position_list_query(self, trd_env: str = TrdEnv.SIMULATE, trd_market: str = TrdMarket.US) -> tuple[int, list[dict[str, Any]]]:
        """Mock US position list query."""
        if not self.connected:
            return (RET_ERROR, "Not connected")

        mock_positions = [
            {
                "code": "US.AAPL",
                "qty": 100,
                "frozen_qty": 0,
                "cost_price": 150.0,
                "unrealized_pl": 500.0,
                "yesterday_qty": 100,
            },
            {
                "code": "US.GOOGL",
                "qty": 50,
                "frozen_qty": 0,
                "cost_price": 2800.0,
                "unrealized_pl": 2000.0,
                "yesterday_qty": 50,
            }
        ]
        return (RET_OK, mock_positions)


# Factory functions for creating mock contexts
def OpenQuoteContext(host: str = "127.0.0.1", port: int = 11111) -> MockOpenQuoteContext:
    """Factory function for mock quote context."""
    return MockOpenQuoteContext(host, port)


def OpenHKTradeContext(host: str = "127.0.0.1", port: int = 11111) -> MockOpenHKTradeContext:
    """Factory function for mock HK trade context."""
    return MockOpenHKTradeContext(host, port)


def OpenUSTradeContext(host: str = "127.0.0.1", port: int = 11111) -> MockOpenUSTradeContext:
    """Factory function for mock US trade context."""
    return MockOpenUSTradeContext(host, port)


# Test utilities
class MockFutuTestCase:
    """Base test case with Futu SDK mocking utilities."""

    def setUp(self) -> None:
        """Set up mock SDK environment."""
        self.mock_quote_ctx = MockOpenQuoteContext()
        self.mock_hk_trade_ctx = MockOpenHKTradeContext()
        self.mock_us_trade_ctx = MockOpenUSTradeContext()

        # Start connections by default
        self.mock_quote_ctx.start()
        self.mock_hk_trade_ctx.start()
        self.mock_us_trade_ctx.start()

        # Unlock trading by default
        self.mock_hk_trade_ctx.unlock_trade("test_password")
        self.mock_us_trade_ctx.unlock_trade("test_password")

    def tearDown(self) -> None:
        """Clean up mock SDK environment."""
        self.mock_quote_ctx.close()
        self.mock_hk_trade_ctx.close()
        self.mock_us_trade_ctx.close()

    def simulate_market_data(self, code: str) -> None:
        """Helper to simulate market data for testing."""
        self.mock_quote_ctx.simulate_quote_callback(code)

    def simulate_order_fill(self, order_id: str, context: str = "HK") -> None:
        """Helper to simulate order execution for testing."""
        ctx = self.mock_hk_trade_ctx if context == "HK" else self.mock_us_trade_ctx
        ctx.simulate_order_callback(order_id, OrderStatus.FILLED_ALL)
