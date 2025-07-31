"""
Unit tests for FutuAdapter facade.

This module tests the main adapter interface using mock SDK classes.
"""

import pytest

import unittest
from unittest.mock import patch

from foxtrot.adapter.futu import FutuAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Direction, Exchange, Interval, OrderType
from foxtrot.util.object import HistoryRequest, OrderRequest, SubscribeRequest

from .mock_futu_sdk import (
    MockFutuTestCase,
)


class TestFutuAdapter(unittest.TestCase, MockFutuTestCase):
    """Test cases for FutuAdapter."""

    def setUp(self) -> None:
        """Set up test environment."""
        MockFutuTestCase.setUp(self)

        self.event_engine = EventEngine()
        self.event_engine.start()

        self.adapter = FutuAdapter(self.event_engine, "FUTU")

        # Mock settings for connection
        self.test_settings = {
            "Host": "127.0.0.1",
            "Port": 11111,
            "RSA Key File": "test_key.txt",
            "Connection ID": "test_conn",
            "Environment": "SIMULATE",
            "Trading Password": "test_password",
            "Paper Trading": True,
            "HK Market Access": True,
            "US Market Access": True,
            "CN Market Access": False,
            "Connect Timeout": 30,
            "Reconnect Interval": 10,
            "Max Reconnect Attempts": 5,
            "Keep Alive Interval": 30,
            "Market Data Level": "L1",
            "Max Subscriptions": 200,
            "Enable Push": True,
        }

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.adapter.close()
        self.event_engine.stop()
        MockFutuTestCase.tearDown(self)

    @pytest.mark.timeout(10)
    def test_adapter_initialization(self) -> None:
        """Test adapter initialization."""
        self.assertEqual(self.adapter.adapter_name, "FUTU")
        self.assertEqual(self.adapter.default_name, "FUTU")
        self.assertFalse(self.adapter.connected)

        # Check supported exchanges
        expected_exchanges = [Exchange.SEHK, Exchange.NASDAQ, Exchange.NYSE, Exchange.SZSE, Exchange.SSE]
        self.assertEqual(self.adapter.exchanges, expected_exchanges)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_connection_success(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test successful connection."""
        # Mock file existence
        mock_exists.return_value = True
        mock_rsa.return_value = True

        # Mock context creation
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Test connection
        self.adapter.connect(self.test_settings)
        self.assertTrue(self.adapter.connected)

    @patch('futu.OpenQuoteContext')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_connection_failure_missing_key(self, mock_exists, mock_quote_ctx):
        """Test connection failure due to missing RSA key."""
        # Mock missing key file
        mock_exists.return_value = False

        # Test connection
        self.adapter.connect(self.test_settings)
        self.assertFalse(self.adapter.connected)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_subscription(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test market data subscription."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect first
        self.adapter.connect(self.test_settings)

        # Test subscription
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        self.adapter.subscribe(req)

        # Verify subscription was made
        self.assertIn("HK.00700", self.mock_quote_ctx.subscriptions)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_order_placement(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test order placement."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect first
        self.adapter.connect(self.test_settings)

        # Test order placement
        req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=450.0
        )

        vt_orderid = self.adapter.send_order(req)
        self.assertIsNotNone(vt_orderid)
        self.assertNotEqual(vt_orderid, "")
        self.assertTrue(vt_orderid.startswith("FUTU."))

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_account_query(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test account information query."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect first
        self.adapter.connect(self.test_settings)

        # Test account query (should not raise exception)
        self.adapter.query_account()
        self.adapter.query_position()

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_historical_data_query(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test historical data query."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect first
        self.adapter.connect(self.test_settings)

        # Test historical data query
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,  # Will use default
            end=None,    # Will use default
            interval=Interval.DAILY
        )

        bars = self.adapter.query_history(req)
        self.assertIsInstance(bars, list)
        # Should get some mock data
        self.assertGreater(len(bars), 0)

    @pytest.mark.timeout(10)
    def test_connection_status(self) -> None:
        """Test connection status reporting."""
        status = self.adapter.get_connection_status()

        self.assertIsInstance(status, dict)
        self.assertIn("adapter_connected", status)
        self.assertIn("api_client_status", status)
        self.assertIn("connection_health", status)

        # Initially should be disconnected
        self.assertFalse(status["adapter_connected"])

    @pytest.mark.timeout(10)
    def test_default_settings(self) -> None:
        """Test default settings structure."""
        settings = self.adapter.get_default_setting()

        self.assertIsInstance(settings, dict)

        # Check required settings exist
        required_keys = [
            "Host", "Port", "RSA Key File", "Connection ID",
            "Environment", "Trading Password", "Paper Trading",
            "HK Market Access", "US Market Access", "CN Market Access",
            "Connect Timeout", "Reconnect Interval", "Max Reconnect Attempts"
        ]

        for key in required_keys:
            self.assertIn(key, settings)


if __name__ == '__main__':
    unittest.main()
