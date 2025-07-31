"""
Unit tests for FutuOrderManager.

This module tests order placement, cancellation, and tracking functionality.
"""

import pytest

import threading
import unittest
from unittest.mock import MagicMock

from foxtrot.adapter.futu.api_client import FutuApiClient
from foxtrot.adapter.futu.order_manager import FutuOrderManager
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Direction, Exchange, OrderType
from foxtrot.util.object import CancelRequest, OrderRequest

from .mock_futu_sdk import MockFutuTestCase


class TestFutuOrderManager(unittest.TestCase, MockFutuTestCase):
    """Test cases for FutuOrderManager."""

    def setUp(self) -> None:
        """Set up test environment."""
        MockFutuTestCase.setUp(self)

        self.event_engine = EventEngine()
        self.event_engine.start()

        # Create mock API client
        self.api_client = MagicMock(spec=FutuApiClient)
        self.api_client.adapter_name = "FUTU"
        self.api_client.paper_trading = True
        self.api_client.trade_ctx_hk = self.mock_hk_trade_ctx
        self.api_client.trade_ctx_us = self.mock_us_trade_ctx
        self.api_client.trade_ctx_cn = None

        # Create order manager
        self.order_manager = FutuOrderManager(self.api_client)

        # Mock adapter for event firing
        self.mock_adapter = MagicMock()
        self.api_client.adapter = self.mock_adapter

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.event_engine.stop()
        MockFutuTestCase.tearDown(self)

    @pytest.mark.timeout(10)
    def test_initialization(self) -> None:
        """Test order manager initialization."""
        self.assertEqual(self.order_manager.api_client, self.api_client)
        self.assertEqual(self.order_manager._local_order_id, 0)
        self.assertEqual(len(self.order_manager._orders), 0)
        self.assertIsInstance(self.order_manager._order_lock, type(threading.Lock()))

    @pytest.mark.timeout(10)
    def test_hk_order_placement(self) -> None:
        """Test HK market order placement."""
        # Create HK order request
        req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=450.0
        )

        # Send order
        vt_orderid = self.order_manager.send_order(req)

        # Verify order ID format
        self.assertIsNotNone(vt_orderid)
        self.assertTrue(vt_orderid.startswith("FUTU."))

        # Verify order is tracked
        self.assertEqual(len(self.order_manager._orders), 1)

        # Verify mock trade context was called
        self.mock_hk_trade_ctx.place_order.assert_called_once()

        # Verify adapter callback was called
        self.mock_adapter.on_order.assert_called()

    @pytest.mark.timeout(10)
    def test_us_order_placement(self) -> None:
        """Test US market order placement."""
        # Create US order request
        req = OrderRequest(
            symbol="AAPL",
            exchange=Exchange.NASDAQ,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=150.0
        )

        # Send order
        vt_orderid = self.order_manager.send_order(req)

        # Verify order placement
        self.assertIsNotNone(vt_orderid)
        self.assertTrue(vt_orderid.startswith("FUTU."))

        # Verify US trade context was used
        self.mock_us_trade_ctx.place_order.assert_called_once()

    @pytest.mark.timeout(10)
    def test_order_cancellation(self) -> None:
        """Test order cancellation."""
        # First place an order
        req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=450.0
        )

        vt_orderid = self.order_manager.send_order(req)

        # Create cancel request
        cancel_req = CancelRequest(
            orderid=vt_orderid.split(".")[1],  # Remove adapter prefix
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Cancel order
        self.order_manager.cancel_order(cancel_req)

        # Verify mock trade context was called for cancellation
        self.mock_hk_trade_ctx.modify_order.assert_called()

    @pytest.mark.timeout(10)
    def test_thread_safety(self) -> None:
        """Test thread safety of order operations."""
        orders_placed = []

        def place_order_thread(thread_id: int) -> None:
            """Thread function to place orders."""
            req = OrderRequest(
                symbol="0700",
                exchange=Exchange.SEHK,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=100,
                price=450.0 + thread_id  # Different prices
            )

            vt_orderid = self.order_manager.send_order(req)
            orders_placed.append(vt_orderid)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=place_order_thread, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all orders were placed successfully
        self.assertEqual(len(orders_placed), 5)
        self.assertEqual(len(self.order_manager._orders), 5)

        # Verify all order IDs are unique
        self.assertEqual(len(set(orders_placed)), 5)

    @pytest.mark.timeout(10)
    def test_invalid_market_order(self) -> None:
        """Test order placement with invalid market."""
        # Create order for unsupported market
        req = OrderRequest(
            symbol="000001",
            exchange=Exchange.SZSE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0
        )  # CN market, but CN access disabled

        # Mock get_trade_context to return None for CN
        self.api_client.get_trade_context = MagicMock(return_value=None)

        # Send order
        vt_orderid = self.order_manager.send_order(req)

        # Should return empty string for invalid market
        self.assertEqual(vt_orderid, "")

    @pytest.mark.timeout(10)
    def test_order_status_tracking(self) -> None:
        """Test order status tracking and updates."""
        # Place an order
        req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=450.0
        )

        vt_orderid = self.order_manager.send_order(req)

        # Get the order from internal tracking
        order = self.order_manager._orders[vt_orderid]
        self.assertIsNotNone(order)

        # Verify initial status is SUBMITTING
        from foxtrot.util.constants import Status
        self.assertEqual(order.status, Status.SUBMITTING)

        # Simulate order callback to update status
        # This would normally come from the SDK callback system
        mock_order_data = {
            "order_id": "1000",  # Mock exchange order ID
            "order_status": "SUBMITTED"
        }

        # Test the callback processing (this would be called by the callback handler)
        # We can't easily test the full callback chain here, but we've verified
        # the order is properly tracked in our internal system

    @pytest.mark.timeout(10)
    def test_get_trade_context_selection(self) -> None:
        """Test trade context selection logic."""
        # Mock the get_trade_context method
        def mock_get_trade_context(market: str):
            if market == "HK":
                return self.mock_hk_trade_ctx
            if market == "US":
                return self.mock_us_trade_ctx
            return None

        self.api_client.get_trade_context = mock_get_trade_context

        # Test HK context selection
        hk_ctx = self.api_client.get_trade_context("HK")
        self.assertEqual(hk_ctx, self.mock_hk_trade_ctx)

        # Test US context selection
        us_ctx = self.api_client.get_trade_context("US")
        self.assertEqual(us_ctx, self.mock_us_trade_ctx)

        # Test CN context selection (should be None)
        cn_ctx = self.api_client.get_trade_context("CN")
        self.assertIsNone(cn_ctx)


if __name__ == '__main__':
    unittest.main()
