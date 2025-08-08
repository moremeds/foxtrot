"""
Unit tests for FutuApiClient.

This module tests the central API client coordination functionality.
"""

import unittest
from unittest.mock import MagicMock, patch
import pytest

from foxtrot.adapter.futu.api_client import FutuApiClient
from foxtrot.core.event_engine import EventEngine

from .mock_futu_sdk import (
    MockFutuTestCase,
)


class TestFutuApiClient(unittest.TestCase, MockFutuTestCase):
    """Test cases for FutuApiClient."""

    def setUp(self) -> None:
        """Set up test environment."""
        MockFutuTestCase.setUp(self)

        self.event_engine = EventEngine()
        self.event_engine.start()

        self.api_client = FutuApiClient(self.event_engine, "FUTU")

        # Mock settings
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
        }

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.api_client.close()
        self.event_engine.stop()
        MockFutuTestCase.tearDown(self)

    @pytest.mark.timeout(10)
    def test_initialization(self) -> None:
        """Test API client initialization."""
        self.assertEqual(self.api_client.adapter_name, "FUTU")
        self.assertFalse(self.api_client.connected)
        self.assertIsNone(self.api_client.quote_ctx)
        self.assertIsNone(self.api_client.trade_ctx_hk)
        self.assertIsNone(self.api_client.trade_ctx_us)

    @patch('foxtrot.adapter.futu.components.context.context_manager.FutuContextManager.initialize_contexts')
    @patch('foxtrot.adapter.futu.components.health.health_monitor.FutuHealthMonitor.start_monitoring')
    @patch('foxtrot.adapter.futu.components.connection.connection_validator.FutuConnectionValidator.validate_settings')
    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_successful_connection(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx, mock_validator, mock_health_start, mock_context_init):
        """Test successful connection and manager initialization."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_validator.return_value = (True, "Settings validation successful")
        mock_context_init.return_value = True
        mock_health_start.return_value = None
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Test connection
        success = self.api_client.connect(self.test_settings)

        self.assertTrue(success)
        self.assertTrue(self.api_client.connected)
        self.assertIsNotNone(self.api_client.quote_ctx)
        self.assertIsNotNone(self.api_client.trade_ctx_hk)
        self.assertIsNotNone(self.api_client.trade_ctx_us)

        # Check managers are initialized
        self.assertIsNotNone(self.api_client.order_manager)
        self.assertIsNotNone(self.api_client.market_data)
        self.assertIsNotNone(self.api_client.account_manager)
        self.assertIsNotNone(self.api_client.historical_data)
        self.assertIsNotNone(self.api_client.contract_manager)

    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_connection_failure_missing_key(self, mock_exists):
        """Test connection failure due to missing RSA key."""
        mock_exists.return_value = False

        success = self.api_client.connect(self.test_settings)

        self.assertFalse(success)
        self.assertFalse(self.api_client.connected)

    @patch('futu.OpenQuoteContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_connection_failure_quote_context(self, mock_exists, mock_rsa, mock_quote_ctx):
        """Test connection failure due to quote context failure."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True

        # Mock quote context failure
        mock_ctx = MagicMock()
        mock_ctx.start.return_value = (-1, "Connection failed")
        mock_quote_ctx.return_value = mock_ctx

        success = self.api_client.connect(self.test_settings)

        self.assertFalse(success)
        self.assertFalse(self.api_client.connected)

    @patch('foxtrot.adapter.futu.components.context.context_manager.FutuContextManager.initialize_contexts')
    @patch('foxtrot.adapter.futu.components.health.health_monitor.FutuHealthMonitor.start_monitoring')
    @patch('foxtrot.adapter.futu.components.connection.connection_validator.FutuConnectionValidator.validate_settings')
    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_health_monitoring(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx, mock_validator, mock_health_start, mock_context_init):
        """Test health monitoring functionality."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_validator.return_value = (True, "Settings validation successful")
        mock_context_init.return_value = True
        mock_health_start.return_value = None  # start_monitoring doesn't return anything
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect
        success = self.api_client.connect(self.test_settings)
        self.assertTrue(success)

        # Verify connection is established
        self.assertTrue(self.api_client.connected)
        
        # Get health status to verify monitoring is working
        health = self.api_client.get_connection_health()
        self.assertIsInstance(health, dict)
        
        # Health status should contain connection information
        # (The exact keys depend on the status provider implementation)
        self.assertTrue(len(health) > 0, "Health status should contain information")

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_trade_context_selection(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test trade context selection based on market."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Connect
        success = self.api_client.connect(self.test_settings)
        self.assertTrue(success)

        # Test context selection
        hk_ctx = self.api_client.get_trade_context("HK")
        us_ctx = self.api_client.get_trade_context("US")
        cn_ctx = self.api_client.get_trade_context("CN")  # Should be None

        self.assertIsNotNone(hk_ctx)
        self.assertIsNotNone(us_ctx)
        self.assertIsNone(cn_ctx)  # CN access disabled in test settings

    @patch('futu.OpenQuoteContext')
    @patch('futu.OpenHKTradeContext')
    @patch('futu.OpenUSTradeContext')
    @patch('futu.SysConfig.set_init_rsa_file')
    @patch('os.path.exists')
    @pytest.mark.timeout(10)
    def test_opend_status(self, mock_exists, mock_rsa, mock_us_ctx, mock_hk_ctx, mock_quote_ctx):
        """Test OpenD status reporting."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rsa.return_value = True
        mock_quote_ctx.return_value = self.mock_quote_ctx
        mock_hk_ctx.return_value = self.mock_hk_trade_ctx
        mock_us_ctx.return_value = self.mock_us_trade_ctx

        # Test status before connection
        status = self.api_client.get_opend_status()
        self.assertIsInstance(status, dict)
        self.assertFalse(status["connected"])

        # Connect and test status
        success = self.api_client.connect(self.test_settings)
        self.assertTrue(success)

        status = self.api_client.get_opend_status()
        self.assertTrue(status["connected"])
        self.assertIn("quote_context", status)
        self.assertIn("hk_trade_context", status)
        self.assertIn("us_trade_context", status)

    @pytest.mark.timeout(10)
    def test_logging_integration(self) -> None:
        """Test logging functionality."""
        # Create a mock adapter for logging
        mock_adapter = MagicMock()
        self.api_client.set_adapter(mock_adapter)

        # Test info logging
        self.api_client._log_info("Test info message")
        mock_adapter.write_log.assert_called_with("Test info message")

        # Test error logging
        self.api_client._log_error("Test error message")
        mock_adapter.write_log.assert_called_with("ERROR: Test error message")


if __name__ == '__main__':
    unittest.main()
