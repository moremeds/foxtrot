"""
Unit tests for core data objects.

These tests verify the basic functionality of trading data structures
without requiring external dependencies or complex mocking.
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from foxtrot.util.object import (
    TickData, OrderData, TradeData, PositionData, AccountData,
    SubscribeRequest, OrderRequest, BaseData
)
from foxtrot.util.constants import Exchange, Direction, OrderType, Status


class TestDataObjects(unittest.TestCase):
    """Test core data objects functionality."""

    def test_tick_data_creation(self):
        """Test TickData object creation and basic functionality."""
        tick = TickData(
            adapter_name="test_adapter",
            symbol="BTC.BINANCE",
            exchange=Exchange.BINANCE,
            datetime=datetime.now(timezone.utc),
            name="Bitcoin",
            last_price=45000.0,
            bid_price_1=44999.0,
            ask_price_1=45001.0,
            bid_volume_1=1.5,
            ask_volume_1=2.0
        )
        
        self.assertEqual(tick.symbol, "BTC.BINANCE")
        self.assertEqual(tick.exchange, Exchange.BINANCE)
        self.assertEqual(tick.last_price, 45000.0)
        self.assertIsInstance(tick.datetime, datetime)

    def test_order_data_creation(self):
        """Test OrderData object creation and basic functionality."""
        order = OrderData(
            adapter_name="test_adapter",
            symbol="ETH.BINANCE", 
            exchange=Exchange.BINANCE,
            orderid="test_order_123",
            type=OrderType.LIMIT,
            direction=Direction.LONG,
            volume=1.0,
            price=3000.0,
            status=Status.NOTTRADED,
            datetime=datetime.now(timezone.utc)
        )
        
        self.assertEqual(order.symbol, "ETH.BINANCE")
        self.assertEqual(order.orderid, "test_order_123")
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertEqual(order.direction, Direction.LONG)
        self.assertEqual(order.volume, 1.0)
        self.assertEqual(order.price, 3000.0)
        self.assertEqual(order.status, Status.NOTTRADED)

    def test_position_data_creation(self):
        """Test PositionData object creation."""
        position = PositionData(
            adapter_name="test_adapter",
            symbol="SPY.SMART",
            exchange=Exchange.SMART,
            direction=Direction.LONG,
            volume=100.0,
            price=400.0,
            pnl=1000.0,
            frozen=0.0
        )
        
        self.assertEqual(position.symbol, "SPY.SMART")
        self.assertEqual(position.direction, Direction.LONG)
        self.assertEqual(position.volume, 100.0)
        self.assertEqual(position.price, 400.0)

    def test_account_data_creation(self):
        """Test AccountData object creation."""
        account = AccountData(
            adapter_name="test_adapter",
            accountid="test_account",
            balance=10000.0,
            frozen=500.0
        )
        
        self.assertEqual(account.accountid, "test_account")
        self.assertEqual(account.balance, 10000.0)
        self.assertEqual(account.frozen, 500.0)
        # Available should be calculated automatically
        self.assertEqual(account.available, 9500.0)

    def test_subscribe_request_creation(self):
        """Test SubscribeRequest object creation."""
        request = SubscribeRequest(
            symbol="BTC.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        self.assertEqual(request.symbol, "BTC.BINANCE")
        self.assertEqual(request.exchange, Exchange.BINANCE)

    def test_order_request_creation(self):
        """Test OrderRequest object creation."""
        request = OrderRequest(
            symbol="ETH.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.MARKET,
            volume=2.0,
            price=0.0  # Market order
        )
        
        self.assertEqual(request.symbol, "ETH.BINANCE")
        self.assertEqual(request.direction, Direction.LONG)
        self.assertEqual(request.type, OrderType.MARKET)
        self.assertEqual(request.volume, 2.0)

    def test_base_data_inheritance(self):
        """Test that data objects properly inherit from BaseData."""
        tick = TickData(
            adapter_name="test_adapter",
            symbol="TEST.EXCHANGE",
            exchange=Exchange.BINANCE,
            datetime=datetime.now(timezone.utc)
        )
        
        self.assertIsInstance(tick, BaseData)
        self.assertTrue(hasattr(tick, 'datetime'))

    def test_data_object_string_representation(self):
        """Test string representation of data objects."""
        tick = TickData(
            adapter_name="test_adapter",
            symbol="BTC.TEST",
            exchange=Exchange.BINANCE,
            datetime=datetime.now(timezone.utc),
            last_price=50000.0
        )
        
        # Should have meaningful string representation
        tick_str = str(tick)
        self.assertIn("BTC.TEST", tick_str)
        self.assertIn("50000", tick_str)


if __name__ == '__main__':
    unittest.main()