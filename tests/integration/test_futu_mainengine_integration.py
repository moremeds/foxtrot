"""
Integration tests for FutuAdapter with MainEngine.

This module tests the integration between FutuAdapter and MainEngine,
verifying proper registration, event handling, and multi-adapter coexistence.
"""

import os
import sys
import unittest
from unittest.mock import patch
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from foxtrot.adapter.binance import BinanceAdapter
from foxtrot.adapter.futu import FutuAdapter
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Exchange, Interval, OrderType
from foxtrot.util.object import HistoryRequest, OrderRequest, SubscribeRequest

from ..unit.adapter.futu.mock_futu_sdk import (
    MockOpenHKTradeContext,
    MockOpenQuoteContext,
    MockOpenUSTradeContext,
)


class TestFutuMainEngineIntegration(unittest.TestCase):
    """Test cases for FutuAdapter MainEngine integration."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.main_engine = MainEngine()

        # Test settings for Futu adapter
        self.futu_settings = {
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
        }

        # Mock contexts for testing
        self.mock_quote_ctx = MockOpenQuoteContext()
        self.mock_hk_trade_ctx = MockOpenHKTradeContext()
        self.mock_us_trade_ctx = MockOpenUSTradeContext()

        # Start mock connections
        self.mock_quote_ctx.start()
        self.mock_hk_trade_ctx.start()
        self.mock_us_trade_ctx.start()
        self.mock_hk_trade_ctx.unlock_trade("test_password")
        self.mock_us_trade_ctx.unlock_trade("test_password")

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.mock_quote_ctx.close()
        self.mock_hk_trade_ctx.close()
        self.mock_us_trade_ctx.close()
        self.main_engine.close()

    @pytest.mark.timeout(30)
    def test_adapter_registration(self) -> None:
        """Test Futu adapter registration with MainEngine."""
        # Add adapter to MainEngine
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Verify adapter was registered
        self.assertIsInstance(adapter, FutuAdapter)
        self.assertEqual(adapter.adapter_name, "FUTU")
        self.assertIn("FUTU", self.main_engine.adapters)

        # Verify adapter is accessible
        retrieved_adapter = self.main_engine.get_adapter("FUTU")
        self.assertEqual(retrieved_adapter, adapter)

    @pytest.mark.timeout(30)
    def test_exchange_registration(self) -> None:
        """Test that Futu exchanges are registered with MainEngine."""
        # Add adapter
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Check that Futu exchanges are registered
        exchanges = self.main_engine.get_all_exchanges()

        futu_exchanges = [Exchange.SEHK, Exchange.NASDAQ, Exchange.NYSE, Exchange.SZSE, Exchange.SSE]
        for exchange in futu_exchanges:
            self.assertIn(exchange, exchanges)

    @pytest.mark.timeout(30)
    def test_multi_adapter_coexistence(self) -> None:
        """Test Futu adapter coexistence with other adapters."""
        # Add both Futu and Binance adapters
        futu_adapter = self.main_engine.add_adapter(FutuAdapter)
        binance_adapter = self.main_engine.add_adapter(BinanceAdapter)

        # Verify both adapters are registered
        self.assertEqual(len(self.main_engine.adapters), 2)
        self.assertIn("FUTU", self.main_engine.adapters)
        self.assertIn("BINANCE", self.main_engine.adapters)

        # Verify adapters are distinct
        self.assertNotEqual(futu_adapter, binance_adapter)

        # Verify exchanges from both adapters are registered
        exchanges = self.main_engine.get_all_exchanges()

        # Futu exchanges
        self.assertIn(Exchange.SEHK, exchanges)
        self.assertIn(Exchange.NASDAQ, exchanges)

        # Binance exchanges (assuming these are different)
        # This would depend on what exchanges Binance adapter supports
        # For now, just verify we have multiple exchanges
        self.assertGreater(len(exchanges), 5)

    @pytest.mark.timeout(30)
    def test_default_settings_retrieval(self) -> None:
        """Test default settings retrieval through MainEngine."""
        # Add adapter
        self.main_engine.add_adapter(FutuAdapter)

        # Get default settings through MainEngine
        settings = self.main_engine.get_default_setting("FUTU")

        self.assertIsNotNone(settings)
        self.assertIsInstance(settings, dict)

        # Check required settings exist
        required_keys = [
            "Host", "Port", "RSA Key File", "Connection ID",
            "Environment", "Trading Password", "Paper Trading",
            "HK Market Access", "US Market Access", "CN Market Access"
        ]

        for key in required_keys:
            self.assertIn(key, settings)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(30)
    def test_connection_through_mainengine(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test adapter connection through MainEngine."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Add adapter
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Connect through MainEngine
        self.main_engine.connect(self.futu_settings, "FUTU")

        # Verify connection
        self.assertTrue(adapter.connected)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(30)
    def test_subscription_through_mainengine(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test market data subscription through MainEngine."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Add and connect adapter
        self.main_engine.add_adapter(FutuAdapter)
        self.main_engine.connect(self.futu_settings, "FUTU")

        # Subscribe through MainEngine
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        self.main_engine.subscribe(req, "FUTU")

        # Verify subscription was made
        self.assertIn("HK.00700", self.mock_quote_ctx.subscriptions)

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(30)
    def test_order_placement_through_mainengine(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test order placement through MainEngine."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Add and connect adapter
        self.main_engine.add_adapter(FutuAdapter)
        self.main_engine.connect(self.futu_settings, "FUTU")

        # Send order through MainEngine
        req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=450.0
        )

        vt_orderid = self.main_engine.send_order(req, "FUTU")

        # Verify order was placed
        self.assertIsNotNone(vt_orderid)
        self.assertTrue(vt_orderid.startswith("FUTU."))

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(30)
    def test_historical_data_through_mainengine(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test historical data query through MainEngine."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Add and connect adapter
        self.main_engine.add_adapter(FutuAdapter)
        self.main_engine.connect(self.futu_settings, "FUTU")

        # Query historical data through MainEngine
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        bars = self.main_engine.query_history(req, "FUTU")

        # Verify data was returned
        self.assertIsInstance(bars, list)
        self.assertGreater(len(bars), 0)

    @pytest.mark.timeout(30)
    def test_event_system_integration(self) -> None:
        """Test integration with MainEngine event system."""
        # Add adapter
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Verify adapter uses the same event engine
        self.assertEqual(adapter.event_engine, self.main_engine.event_engine)

        # Test that adapter can fire events
        # This would normally trigger through real data callbacks
        # For now, just verify the event engine is connected
        self.assertTrue(adapter.event_engine._active)

    @pytest.mark.timeout(30)
    def test_oms_integration(self) -> None:
        """Test integration with Order Management System."""
        # Add adapter
        self.main_engine.add_adapter(FutuAdapter)

        # Verify OMS functions are accessible through MainEngine
        self.assertIsNotNone(self.main_engine.get_tick)
        self.assertIsNotNone(self.main_engine.get_order)
        self.assertIsNotNone(self.main_engine.get_trade)
        self.assertIsNotNone(self.main_engine.get_position)
        self.assertIsNotNone(self.main_engine.get_account)
        self.assertIsNotNone(self.main_engine.get_contract)

        # Verify OMS data access functions
        ticks = self.main_engine.get_all_ticks()
        orders = self.main_engine.get_all_orders()
        trades = self.main_engine.get_all_trades()
        positions = self.main_engine.get_all_positions()
        accounts = self.main_engine.get_all_accounts()
        contracts = self.main_engine.get_all_contracts()

        # Should all be empty lists initially
        self.assertIsInstance(ticks, list)
        self.assertIsInstance(orders, list)
        self.assertIsInstance(trades, list)
        self.assertIsInstance(positions, list)
        self.assertIsInstance(accounts, list)
        self.assertIsInstance(contracts, list)

    @pytest.mark.timeout(30)
    def test_adapter_cleanup(self) -> None:
        """Test proper adapter cleanup through MainEngine."""
        # Add adapter
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Verify adapter is registered
        self.assertIn("FUTU", self.main_engine.adapters)

        # Close MainEngine (should cleanup adapters)
        self.main_engine.close()

        # Verify adapter connection is closed
        self.assertFalse(adapter.connected)

    @pytest.mark.timeout(30)
    def test_baseadapter_interface_compliance(self) -> None:
        """Test that FutuAdapter properly implements BaseAdapter interface."""
        from foxtrot.adapter.base_adapter import BaseAdapter

        # Add adapter
        adapter = self.main_engine.add_adapter(FutuAdapter)

        # Verify inheritance
        self.assertIsInstance(adapter, BaseAdapter)

        # Verify required methods exist
        required_methods = [
            'connect', 'close', 'subscribe', 'send_order', 'cancel_order',
            'query_account', 'query_position', 'query_history', 'get_default_setting'
        ]

        for method_name in required_methods:
            self.assertTrue(hasattr(adapter, method_name))
            method = getattr(adapter, method_name)
            self.assertTrue(callable(method))

        # Verify required attributes exist
        required_attributes = [
            'adapter_name', 'exchanges', 'default_name'
        ]

        for attr_name in required_attributes:
            self.assertTrue(hasattr(adapter, attr_name))

    @pytest.mark.timeout(30)
    def test_adapter_name_uniqueness(self) -> None:
        """Test that adapter names are properly managed."""
        # Add first adapter with default name
        adapter1 = self.main_engine.add_adapter(FutuAdapter)
        self.assertEqual(adapter1.adapter_name, "FUTU")

        # Add second adapter with custom name
        adapter2 = self.main_engine.add_adapter(FutuAdapter, "FUTU_2")
        self.assertEqual(adapter2.adapter_name, "FUTU_2")

        # Verify both adapters are registered
        self.assertEqual(len(self.main_engine.adapters), 2)
        self.assertIn("FUTU", self.main_engine.adapters)
        self.assertIn("FUTU_2", self.main_engine.adapters)

        # Verify adapters are distinct
        self.assertNotEqual(adapter1, adapter2)


if __name__ == '__main__':
    print("Running Futu MainEngine Integration Tests")
    print("=" * 50)

    # Run the tests
    unittest.main(verbosity=2)
