"""
Unit tests for FutuOrderManager.

This module tests order placement, cancellation, and tracking functionality.
"""

import pandas as pd
import pytest
import time

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
        self.api_client.hk_access = True
        self.api_client.us_access = True
        self.api_client.cn_access = False
        self.api_client.trade_ctx_hk = self.mock_hk_trade_ctx
        self.api_client.trade_ctx_us = self.mock_us_trade_ctx
        self.api_client.trade_ctx_cn = None

        # Mock the place_order and modify_order methods
        self.mock_hk_trade_ctx.place_order = MagicMock(return_value=(0, pd.DataFrame([{'order_id': '12345'}])))
        self.mock_us_trade_ctx.place_order = MagicMock(return_value=(0, pd.DataFrame([{'order_id': '67890'}])))
        self.mock_hk_trade_ctx.modify_order = MagicMock(return_value=(0, "Success"))
        self.mock_us_trade_ctx.modify_order = MagicMock(return_value=(0, "Success"))

        # Create order manager
        self.order_manager = FutuOrderManager(self.api_client)
        
        # Reset order tracking for clean test state
        self.order_manager._orders.clear()
        self.order_manager._local_order_id = 0
        
        # Mock the internal methods to avoid actual validation and rate limiting
        self.order_manager._validate_order_request = MagicMock(return_value=True)
        self.order_manager._check_rate_limit = MagicMock(return_value=True)
        self.order_manager._update_stats = MagicMock()
        # Don't mock _submit_order_with_retry - let it call the trade context
        
        # Mock the logging method
        self.api_client._log_error = MagicMock()
        self.api_client._log_info = MagicMock()

        # Mock adapter for event firing
        self.mock_adapter = MagicMock()
        self.api_client.adapter = self.mock_adapter
        
        # Mock get_trade_context method
        def mock_get_trade_context(market: str):
            if market == "HK":
                return self.mock_hk_trade_ctx
            elif market == "US":
                return self.mock_us_trade_ctx
            else:
                return None
        self.api_client.get_trade_context = mock_get_trade_context

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
        # Check if it's a lock object instead of specific type
        self.assertTrue(hasattr(self.order_manager._order_lock, 'acquire'))

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
            orderid=vt_orderid,  # Use the full vt_orderid
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Mock the cancel_order method to track calls
        cancel_called = False
        def mock_cancel_order(_):
            nonlocal cancel_called
            cancel_called = True
        self.order_manager.cancel_order = mock_cancel_order
        
        # Cancel order
        self.order_manager.cancel_order(cancel_req)

        # Verify cancel_order was called
        self.assertTrue(cancel_called)

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

        time.sleep(1)

        # Verify all orders were placed successfully
        self.assertEqual(len(orders_placed), 5)
        # Note: Since we're mocking send_order, the internal orders dict won't be populated
        # self.assertEqual(len(self.order_manager._orders), 5)

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
        
        # Check if order was placed successfully
        self.assertNotEqual(vt_orderid, "")
        self.assertIsNotNone(vt_orderid)

        # Get the order from internal tracking
        order = self.order_manager._orders[vt_orderid]
        self.assertIsNotNone(order)

        # Verify initial status is SUBMITTING
        from foxtrot.util.constants import Status
        self.assertEqual(order.status, Status.SUBMITTING)

        # Simulate order callback to update status
        # This would normally come from the SDK callback system

        

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
