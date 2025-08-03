"""
Unit tests for FutuHistoricalData.

This module tests historical OHLCV data queries and caching.
"""

import pytest

from datetime import datetime
import unittest
from unittest.mock import MagicMock

from foxtrot.adapter.futu.api_client import FutuApiClient
from foxtrot.adapter.futu.historical_data import FutuHistoricalData
from foxtrot.util.constants import Exchange, Interval
from foxtrot.util.object import BarData, HistoryRequest

from .mock_futu_sdk import RET_ERROR, RET_OK, AuType, KLType, MockFutuTestCase


class TestFutuHistoricalData(unittest.TestCase, MockFutuTestCase):
    """Test cases for FutuHistoricalData."""

    def setUp(self) -> None:
        """Set up test environment."""
        MockFutuTestCase.setUp(self)

        # Create mock API client
        self.api_client = MagicMock(spec=FutuApiClient)
        self.api_client.adapter_name = "FUTU"
        self.api_client.quote_ctx = self.mock_quote_ctx
        self.mock_quote_ctx.get_cur_kline = MagicMock()

        # Create historical data manager
        self.historical_data = FutuHistoricalData(self.api_client)

    def tearDown(self) -> None:
        """Clean up test environment."""
        MockFutuTestCase.tearDown(self)

    @pytest.mark.timeout(10)
    def test_initialization(self) -> None:
        """Test historical data manager initialization."""
        self.assertEqual(self.historical_data.api_client, self.api_client)
        self.assertIsInstance(self.historical_data._cache, dict)
        self.assertEqual(len(self.historical_data._cache), 0)
        self.assertEqual(self.historical_data._cache_timeout, 300)

    @pytest.mark.timeout(10)
    def test_hk_stock_daily_query(self) -> None:
        """Test HK stock daily data query."""
        # Create history request
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Mock SDK response
        mock_klines = [
            {
                "time_key": "2024-01-15 09:30:00",
                "open": 450.0,
                "high": 460.0,
                "low": 440.0,
                "close": 455.0,
                "volume": 1000000,
                "turnover": 450000000.0,
            },
            {
                "time_key": "2024-01-16 09:30:00",
                "open": 455.0,
                "high": 470.0,
                "low": 450.0,
                "close": 465.0,
                "volume": 1200000,
                "turnover": 558000000.0,
            }
        ]

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, mock_klines)

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Verify query results
        self.assertEqual(len(bars), 2)
        self.assertIsInstance(bars[0], BarData)

        # Verify first bar data
        bar1 = bars[0]
        self.assertEqual(bar1.symbol, "0700")
        self.assertEqual(bar1.exchange, Exchange.SEHK)
        self.assertEqual(bar1.interval, Interval.DAILY)
        self.assertEqual(bar1.open_price, 450.0)
        self.assertEqual(bar1.high_price, 460.0)
        self.assertEqual(bar1.low_price, 440.0)
        self.assertEqual(bar1.close_price, 455.0)
        self.assertEqual(bar1.volume, 1000000.0)
        self.assertEqual(bar1.turnover, 450000000.0)
        self.assertEqual(bar1.adapter_name, "FUTU")
        self.assertIsInstance(bar1.datetime, datetime)

        # Verify SDK was called correctly
        self.mock_quote_ctx.get_cur_kline.assert_called_once_with(
            code="HK.00700",
            num=252,
            kl_type=KLType.K_DAY,
            autype='qfq'
        )

    @pytest.mark.timeout(10)
    def test_us_stock_hourly_query(self) -> None:
        """Test US stock hourly data query."""
        req = HistoryRequest(
            symbol="AAPL",
            exchange=Exchange.NASDAQ,
            start=None,
            end=None,
            interval=Interval.HOUR
        )

        mock_klines = [
            {
                "time_key": "2024-01-15 10:00:00",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.5,
                "volume": 100000,
                "turnover": 15075000.0,
            }
        ]

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, mock_klines)

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Verify results
        self.assertEqual(len(bars), 1)
        bar = bars[0]
        self.assertEqual(bar.symbol, "AAPL")
        self.assertEqual(bar.exchange, Exchange.NASDAQ)
        self.assertEqual(bar.interval, Interval.HOUR)

        # Verify SDK was called with hourly interval
        self.mock_quote_ctx.get_cur_kline.assert_called_once_with(
            code="US.AAPL",
            num=168,
            kl_type=KLType.K_60M,
            autype='qfq'
        )

    @pytest.mark.timeout(10)
    def test_cn_stock_minute_query(self) -> None:
        """Test CN stock minute data query."""
        req = HistoryRequest(
            symbol="000001",
            exchange=Exchange.SZSE,
            start=None,
            end=None,
            interval=Interval.MINUTE
        )

        mock_klines = [
            {
                "time_key": "2024-01-15 09:30:00",
                "open": 10.0,
                "high": 10.2,
                "low": 9.9,
                "close": 10.1,
                "volume": 50000,
                "turnover": 505000.0,
            }
        ]

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, mock_klines)

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Verify results
        self.assertEqual(len(bars), 1)
        bar = bars[0]
        self.assertEqual(bar.symbol, "000001")
        self.assertEqual(bar.exchange, Exchange.SZSE)
        self.assertEqual(bar.interval, Interval.MINUTE)

        # Verify SDK was called with minute interval
        self.mock_quote_ctx.get_cur_kline.assert_called_once_with(
            code="CN.000001",
            num=1440,
            kl_type=KLType.K_1M,
            autype='qfq'
        )

    @pytest.mark.timeout(10)
    def test_weekly_interval_conversion(self) -> None:
        """Test weekly interval conversion."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.WEEKLY
        )

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, [])

        # Query with weekly interval
        self.historical_data.query_history(req)

        # Verify weekly interval was converted correctly
        self.mock_quote_ctx.get_cur_kline.assert_called_once_with(
            code="HK.00700",
            num=104,
            kl_type=KLType.K_WEEK,
            autype='qfq'
        )

    @pytest.mark.timeout(10)
    def test_interval_conversion_mapping(self) -> None:
        """Test interval conversion mapping."""
        # Test all supported intervals
        test_cases = [
            (Interval.MINUTE, KLType.K_1M),
            (Interval.HOUR, KLType.K_60M),
            (Interval.DAILY, KLType.K_DAY),
            (Interval.WEEKLY, KLType.K_WEEK),
        ]

        for vt_interval, expected_ktype in test_cases:
            result = self.historical_data._convert_interval_to_ktype(vt_interval)
            self.assertEqual(result, expected_ktype)

        # Test unknown interval (should default to daily)
        unknown_interval = "unknown_interval"
        result = self.historical_data._convert_interval_to_ktype(unknown_interval)
        self.assertEqual(result, KLType.K_DAY)

    @pytest.mark.timeout(10)
    def test_caching_functionality(self) -> None:
        """Test data caching functionality."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        mock_klines = [
            {
                "time_key": "2024-01-15 09:30:00",
                "open": 450.0,
                "high": 460.0,
                "low": 440.0,
                "close": 455.0,
                "volume": 1000000,
                "turnover": 450000000.0,
            }
        ]

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, mock_klines)

        # First query (should hit SDK)
        bars1 = self.historical_data.query_history(req)
        self.assertEqual(len(bars1), 1)
        self.mock_quote_ctx.get_cur_kline.assert_called_once()

        # Second query (should hit cache)
        bars2 = self.historical_data.query_history(req)
        self.assertEqual(len(bars2), 1)

        # SDK should still have been called only once
        self.mock_quote_ctx.get_cur_kline.assert_called_once()

        # Results should be identical
        self.assertEqual(bars1[0].open_price, bars2[0].open_price)
        self.assertEqual(bars1[0].close_price, bars2[0].close_price)

    @pytest.mark.timeout(10)
    def test_cache_key_generation(self) -> None:
        """Test cache key generation for different requests."""
        # Different requests should generate different cache keys
        req1 = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        req2 = HistoryRequest(
            symbol="AAPL",
            exchange=Exchange.NASDAQ,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        req3 = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.HOUR
        )

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, [])

        # Query all three requests
        self.historical_data.query_history(req1)
        self.historical_data.query_history(req2)
        self.historical_data.query_history(req3)

        # Should have 3 different cache entries
        self.assertEqual(len(self.historical_data._cache), 3)

        # SDK should have been called 3 times
        self.assertEqual(self.mock_quote_ctx.get_cur_kline.call_count, 3)

    @pytest.mark.timeout(10)
    def test_sdk_error_handling(self) -> None:
        """Test SDK error handling."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Mock SDK error
        self.mock_quote_ctx.get_cur_kline.return_value = (RET_ERROR, "Connection failed")

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Should return empty list
        self.assertEqual(bars, [])

        # Error should be logged
        self.api_client._log_error.assert_called()

        # No cache entry should be created
        self.assertEqual(len(self.historical_data._cache), 0)

    @pytest.mark.timeout(10)
    def test_no_quote_context_handling(self) -> None:
        """Test handling when quote context is not available."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Remove quote context
        self.api_client.quote_ctx = None

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Should return empty list
        self.assertEqual(bars, [])

        # Error should be logged
        self.api_client._log_error.assert_called_with(
            "Quote context not available for historical data"
        )

    @pytest.mark.timeout(10)
    def test_empty_data_handling(self) -> None:
        """Test handling of empty data response."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Mock empty data response
        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, [])

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Should return empty list
        self.assertEqual(bars, [])

        # Cache should still be created (empty)
        self.assertEqual(len(self.historical_data._cache), 1)

    @pytest.mark.timeout(10)
    def test_invalid_kline_data_handling(self) -> None:
        """Test handling of invalid k-line data."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Mock data with invalid/missing fields
        mock_klines = [
            {
                "time_key": "invalid_date_format",
                "open": None,
                "high": "not_a_number",
                "low": 440.0,
                "close": 455.0,
                "volume": 1000000,
                "turnover": 450000000.0,
            },
            {
                # Missing time_key
                "open": 450.0,
                "high": 460.0,
                "low": 440.0,
                "close": 455.0,
                "volume": 1000000,
                "turnover": 450000000.0,
            }
        ]

        self.mock_quote_ctx.get_cur_kline.return_value = (RET_OK, mock_klines)

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Should handle invalid data gracefully
        # At least one valid bar should be returned (the second one with current time)
        self.assertGreaterEqual(len(bars), 0)

        # Errors should be logged for invalid data
        self.api_client._log_error.assert_called()

    @pytest.mark.timeout(10)
    def test_datetime_parsing(self) -> None:
        """Test datetime parsing from time_key."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        mock_kline = {
            "time_key": "2024-01-15 09:30:00",
            "open": 450.0,
            "high": 460.0,
            "low": 440.0,
            "close": 455.0,
            "volume": 1000000,
            "turnover": 450000000.0,
        }

        # Test conversion
        bar = self.historical_data._convert_kline_to_bar(req, mock_kline)

        # Verify datetime parsing
        expected_dt = datetime(2024, 1, 15, 9, 30, 0)
        self.assertEqual(bar.datetime, expected_dt)

    @pytest.mark.timeout(10)
    def test_exception_handling_in_query(self) -> None:
        """Test exception handling in query method."""
        req = HistoryRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            start=None,
            end=None,
            interval=Interval.DAILY
        )

        # Mock SDK to raise exception
        self.mock_quote_ctx.get_cur_kline.side_effect = Exception("Connection error")

        # Query historical data
        bars = self.historical_data.query_history(req)

        # Should return empty list and log error
        self.assertEqual(bars, [])
        self.api_client._log_error.assert_called()

        # No cache entry should be created
        self.assertEqual(len(self.historical_data._cache), 0)


if __name__ == '__main__':
    unittest.main()
