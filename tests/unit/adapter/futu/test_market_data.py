"""
Unit tests for FutuMarketData.

This module tests real-time market data subscriptions and management.
"""

import pytest

import unittest
from unittest.mock import MagicMock

from foxtrot.adapter.futu.api_client import FutuApiClient
from foxtrot.adapter.futu.market_data import FutuMarketData
from foxtrot.util.constants import Exchange
from foxtrot.util.object import SubscribeRequest

from .mock_futu_sdk import RET_ERROR, RET_OK, MockFutuTestCase, SubType


class TestFutuMarketData(unittest.TestCase, MockFutuTestCase):
    """Test cases for FutuMarketData."""

    def setUp(self) -> None:
        """Set up test environment."""
        MockFutuTestCase.setUp(self)

        # Create mock API client
        self.api_client = MagicMock(spec=FutuApiClient)
        self.api_client.adapter_name = "FUTU"
        self.api_client.quote_ctx = self.mock_quote_ctx
        self.mock_quote_ctx.subscribe = MagicMock()
        self.mock_quote_ctx.unsubscribe = MagicMock()

        # Create market data manager
        self.market_data = FutuMarketData(self.api_client)

    def tearDown(self) -> None:
        """Clean up test environment."""
        MockFutuTestCase.tearDown(self)

    @pytest.mark.timeout(10)
    def test_initialization(self) -> None:
        """Test market data manager initialization."""
        self.assertEqual(self.market_data.api_client, self.api_client)
        self.assertIsInstance(self.market_data.subscriptions, dict)
        self.assertEqual(len(self.market_data.subscriptions), 0)

    @pytest.mark.timeout(10)
    def test_hk_stock_subscription(self) -> None:
        """Test HK stock subscription."""
        # Create subscription request
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Mock successful subscription
        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify subscription
        self.assertTrue(result)
        self.assertIn("0700.SEHK", self.market_data.subscriptions)

        # Verify SDK was called correctly
        self.mock_quote_ctx.subscribe.assert_called_once_with(
            code_list=["HK.00700"],
            subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
        )

        # Verify subscription tracking
        subscription = self.market_data.subscriptions["0700.SEHK"]
        self.assertEqual(subscription["market"], "HK")
        self.assertEqual(subscription["code"], "HK.00700")
        self.assertEqual(len(subscription["subtypes"]), 3)

    @pytest.mark.timeout(10)
    def test_us_stock_subscription(self) -> None:
        """Test US stock subscription."""
        req = SubscribeRequest(
            symbol="AAPL",
            exchange=Exchange.NASDAQ
        )

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify subscription
        self.assertTrue(result)
        self.assertIn("AAPL.NASDAQ", self.market_data.subscriptions)

        # Verify SDK call with US format
        self.mock_quote_ctx.subscribe.assert_called_once_with(
            code_list=["US.AAPL"],
            subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
        )

    @pytest.mark.timeout(10)
    def test_cn_stock_subscription(self) -> None:
        """Test CN stock subscription."""
        req = SubscribeRequest(
            symbol="000001",
            exchange=Exchange.SZSE
        )

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify subscription
        self.assertTrue(result)
        self.assertIn("000001.SZSE", self.market_data.subscriptions)

        # Verify SDK call with CN format
        self.mock_quote_ctx.subscribe.assert_called_once_with(
            code_list=["CN.000001"],
            subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
        )

    @pytest.mark.timeout(10)
    def test_duplicate_subscription(self) -> None:
        """Test handling of duplicate subscriptions."""
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")

        # First subscription
        result1 = self.market_data.subscribe(req)
        self.assertTrue(result1)

        # Duplicate subscription
        result2 = self.market_data.subscribe(req)
        self.assertTrue(result2)

        # Verify SDK was only called once
        self.mock_quote_ctx.subscribe.assert_called_once()

        # Verify only one subscription tracked
        self.assertEqual(len(self.market_data.subscriptions), 1)

    @pytest.mark.timeout(10)
    def test_subscription_sdk_error(self) -> None:
        """Test subscription with SDK error."""
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Mock SDK error
        self.mock_quote_ctx.subscribe.return_value = (RET_ERROR, "Connection failed")

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify failure
        self.assertFalse(result)
        self.assertNotIn("0700.SEHK", self.market_data.subscriptions)

        # Verify error was logged
        self.api_client._log_error.assert_called()

    @pytest.mark.timeout(10)
    def test_subscription_invalid_symbol(self) -> None:
        """Test subscription with invalid symbol format."""
        req = SubscribeRequest(
            symbol="INVALID",
            exchange=Exchange.SEHK  # This will create INVALID.SEHK which is invalid
        )

        # Subscribe with invalid symbol
        result = self.market_data.subscribe(req)

        # Verify failure
        self.assertFalse(result)
        self.assertEqual(len(self.market_data.subscriptions), 0)

        # Verify error was logged
        self.api_client._log_error.assert_called()

        # Verify SDK was not called
        self.mock_quote_ctx.subscribe.assert_not_called()

    @pytest.mark.timeout(10)
    def test_subscription_no_quote_context(self) -> None:
        """Test subscription when quote context is not available."""
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Remove quote context
        self.api_client.quote_ctx = None

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify failure
        self.assertFalse(result)
        self.assertEqual(len(self.market_data.subscriptions), 0)

        # Verify error was logged
        self.api_client._log_error.assert_called()

    @pytest.mark.timeout(10)
    def test_unsubscription(self) -> None:
        """Test market data unsubscription."""
        # First subscribe
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")
        self.mock_quote_ctx.unsubscribe.return_value = (RET_OK, "Success")

        # Subscribe first
        self.market_data.subscribe(req)
        self.assertIn("0700.SEHK", self.market_data.subscriptions)

        # Then unsubscribe
        result = self.market_data.unsubscribe(req)

        # Verify unsubscription
        self.assertTrue(result)
        self.assertNotIn("0700.SEHK", self.market_data.subscriptions)

        # Verify SDK was called correctly
        self.mock_quote_ctx.unsubscribe.assert_called_once_with(
            code_list=["HK.00700"],
            subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
        )

    @pytest.mark.timeout(10)
    def test_unsubscription_not_subscribed(self) -> None:
        """Test unsubscription for non-subscribed symbol."""
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Unsubscribe without subscribing first
        result = self.market_data.unsubscribe(req)

        # Should succeed (already unsubscribed)
        self.assertTrue(result)

        # Verify SDK was not called
        self.mock_quote_ctx.unsubscribe.assert_not_called()

    @pytest.mark.timeout(10)
    def test_unsubscription_sdk_error(self) -> None:
        """Test unsubscription with SDK error."""
        # First subscribe
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")
        self.mock_quote_ctx.unsubscribe.return_value = (RET_ERROR, "Connection failed")

        # Subscribe first
        self.market_data.subscribe(req)

        # Then unsubscribe with error
        result = self.market_data.unsubscribe(req)

        # Verify failure
        self.assertFalse(result)

        # Subscription should still be tracked (since unsubscribe failed)
        self.assertIn("0700.SEHK", self.market_data.subscriptions)

        # Verify error was logged
        self.api_client._log_error.assert_called()

    @pytest.mark.timeout(10)
    def test_restore_subscriptions_empty(self) -> None:
        """Test restore subscriptions with no active subscriptions."""
        # Restore with no subscriptions
        self.market_data.restore_subscriptions()

        # Should not call SDK
        self.mock_quote_ctx.subscribe.assert_not_called()

    @pytest.mark.timeout(10)
    def test_restore_subscriptions_with_data(self) -> None:
        """Test restore subscriptions with existing data."""
        # Setup existing subscriptions manually
        self.market_data.subscriptions = {
            "0700.SEHK": {
                "market": "HK",
                "code": "HK.00700",
                "subtypes": [SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
            },
            "AAPL.NASDAQ": {
                "market": "US",
                "code": "US.AAPL",
                "subtypes": [SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
            }
        }

        self.mock_quote_ctx.subscribe.return_value = (RET_OK, "Success")

        # Restore subscriptions
        self.market_data.restore_subscriptions()

        # Verify batch subscription was called
        self.mock_quote_ctx.subscribe.assert_called_once_with(
            code_list=["HK.00700", "US.AAPL"],
            subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
        )

    @pytest.mark.timeout(10)
    def test_restore_subscriptions_sdk_error(self) -> None:
        """Test restore subscriptions with SDK error."""
        # Setup existing subscriptions
        self.market_data.subscriptions = {
            "0700.SEHK": {
                "market": "HK",
                "code": "HK.00700",
                "subtypes": [SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
            }
        }

        self.mock_quote_ctx.subscribe.return_value = (RET_ERROR, "Connection failed")

        # Restore subscriptions
        self.market_data.restore_subscriptions()

        # Verify error was logged
        self.api_client._log_error.assert_called()

    @pytest.mark.timeout(10)
    def test_restore_subscriptions_no_quote_context(self) -> None:
        """Test restore subscriptions without quote context."""
        # Setup existing subscriptions
        self.market_data.subscriptions = {
            "0700.SEHK": {
                "market": "HK",
                "code": "HK.00700",
                "subtypes": [SubType.QUOTE, SubType.ORDER_BOOK, SubType.TICKER]
            }
        }

        # Remove quote context
        self.api_client.quote_ctx = None

        # Restore subscriptions (should not crash)
        self.market_data.restore_subscriptions()

        # Should not raise exception and should log info
        self.api_client._log_info.assert_called()

    @pytest.mark.timeout(10)
    def test_get_subscription_count(self) -> None:
        """Test getting subscription count."""
        # Initially empty
        self.assertEqual(self.market_data.get_subscription_count(), 0)

        # Add some subscriptions manually
        self.market_data.subscriptions = {
            "0700.SEHK": {"code": "HK.00700"},
            "AAPL.NASDAQ": {"code": "US.AAPL"},
            "000001.SZSE": {"code": "CN.000001"}
        }

        # Verify count
        self.assertEqual(self.market_data.get_subscription_count(), 3)

    @pytest.mark.timeout(10)
    def test_get_subscribed_symbols(self) -> None:
        """Test getting list of subscribed symbols."""
        # Initially empty
        self.assertEqual(self.market_data.get_subscribed_symbols(), [])

        # Add some subscriptions manually
        symbols = ["0700.SEHK", "AAPL.NASDAQ", "000001.SZSE"]
        for symbol in symbols:
            self.market_data.subscriptions[symbol] = {"code": f"test_{symbol}"}

        # Verify symbols list
        subscribed_symbols = self.market_data.get_subscribed_symbols()
        self.assertEqual(len(subscribed_symbols), 3)
        for symbol in symbols:
            self.assertIn(symbol, subscribed_symbols)

    @pytest.mark.timeout(10)
    def test_subscription_exception_handling(self) -> None:
        """Test exception handling in subscription methods."""
        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Mock SDK to raise exception
        self.mock_quote_ctx.subscribe.side_effect = Exception("Connection error")

        # Subscribe
        result = self.market_data.subscribe(req)

        # Verify failure and error logging
        self.assertFalse(result)
        self.api_client._log_error.assert_called()
        self.assertEqual(len(self.market_data.subscriptions), 0)

    @pytest.mark.timeout(10)
    def test_unsubscription_exception_handling(self) -> None:
        """Test exception handling in unsubscription methods."""
        # Setup existing subscription
        self.market_data.subscriptions["0700.SEHK"] = {
            "code": "HK.00700",
            "subtypes": [SubType.QUOTE]
        }

        req = SubscribeRequest(
            symbol="0700",
            exchange=Exchange.SEHK
        )

        # Mock SDK to raise exception
        self.mock_quote_ctx.unsubscribe.side_effect = Exception("Connection error")

        # Unsubscribe
        result = self.market_data.unsubscribe(req)

        # Verify failure and error logging
        self.assertFalse(result)
        self.api_client._log_error.assert_called()


if __name__ == '__main__':
    unittest.main()
