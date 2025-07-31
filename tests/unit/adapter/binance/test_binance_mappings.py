"""
Unit tests for Binance Mappings utilities.

Tests data transformation functions between CCXT and VT formats,
error classification, and retry logic.
"""

import pytest

from foxtrot.adapter.binance.binance_mappings import (
    classify_error,
    convert_direction_from_ccxt,
    convert_direction_to_ccxt,
    convert_order_type_from_ccxt,
    convert_order_type_to_ccxt,
    convert_status_from_ccxt,
    convert_status_to_ccxt,
    convert_symbol_from_ccxt,
    convert_symbol_to_ccxt,
    get_retry_delay,
    should_retry_error,
)
from foxtrot.util.constants import Direction, Exchange, OrderType, Status


class TestBinanceMappings:
    """Test cases for Binance mapping utilities."""

    @pytest.mark.timeout(10)
    def test_convert_symbol_to_ccxt_usdt(self):
        """Test symbol conversion to CCXT format for USDT pairs."""
        assert convert_symbol_to_ccxt("BTCUSDT.BINANCE") == "BTC/USDT"
        assert convert_symbol_to_ccxt("ETHUSDT.BINANCE") == "ETH/USDT"
        assert convert_symbol_to_ccxt("ADAUSDT.BINANCE") == "ADA/USDT"

    @pytest.mark.timeout(10)
    def test_convert_symbol_to_ccxt_other_stablecoins(self):
        """Test symbol conversion for other stablecoin pairs."""
        assert convert_symbol_to_ccxt("BTCBUSD.BINANCE") == "BTC/BUSD"
        assert convert_symbol_to_ccxt("ETHUSDC.BINANCE") == "ETH/USDC"

    @pytest.mark.timeout(10)
    def test_convert_symbol_to_ccxt_crypto_pairs(self):
        """Test symbol conversion for crypto-to-crypto pairs."""
        assert convert_symbol_to_ccxt("ETHBTC.BINANCE") == "ETH/BTC"
        assert convert_symbol_to_ccxt("ADABTC.BINANCE") == "ADA/BTC"
        assert convert_symbol_to_ccxt("ADAETH.BINANCE") == "ADA/ETH"
        assert convert_symbol_to_ccxt("ADABNB.BINANCE") == "ADA/BNB"

    @pytest.mark.timeout(10)
    def test_convert_symbol_to_ccxt_unknown_format(self):
        """Test symbol conversion for unknown format defaults to USDT."""
        assert convert_symbol_to_ccxt("UNKNOWN.BINANCE") == "UNKNOWN/USDT"
        assert convert_symbol_to_ccxt("XYZ.BINANCE") == "XYZ/USDT"

    @pytest.mark.timeout(10)
    def test_convert_symbol_to_ccxt_invalid_input(self):
        """Test symbol conversion with invalid input."""
        assert convert_symbol_to_ccxt("") == ""
        assert convert_symbol_to_ccxt("INVALID") == ""  # No dot - invalid VT format

    @pytest.mark.timeout(10)
    def test_convert_symbol_from_ccxt(self):
        """Test symbol conversion from CCXT to VT format."""
        assert convert_symbol_from_ccxt("BTC/USDT") == "BTCUSDT.BINANCE"
        assert convert_symbol_from_ccxt("ETH/BTC") == "ETHBTC.BINANCE"
        assert convert_symbol_from_ccxt("ADA/ETH", Exchange.BINANCE) == "ADAETH.BINANCE"

    @pytest.mark.timeout(10)
    def test_convert_symbol_from_ccxt_invalid(self):
        """Test symbol conversion from CCXT with invalid input."""
        assert convert_symbol_from_ccxt("INVALID") == "INVALID.BINANCE"

    @pytest.mark.timeout(10)
    def test_convert_direction_to_ccxt(self):
        """Test direction conversion to CCXT format."""
        assert convert_direction_to_ccxt(Direction.LONG) == "buy"
        assert convert_direction_to_ccxt(Direction.SHORT) == "sell"
        assert convert_direction_to_ccxt(None) == "buy"  # Default

    @pytest.mark.timeout(10)
    def test_convert_direction_from_ccxt(self):
        """Test direction conversion from CCXT format."""
        assert convert_direction_from_ccxt("buy") == Direction.LONG
        assert convert_direction_from_ccxt("sell") == Direction.SHORT
        assert convert_direction_from_ccxt("BUY") == Direction.LONG  # Case insensitive
        assert convert_direction_from_ccxt("SELL") == Direction.SHORT
        assert convert_direction_from_ccxt("unknown") == Direction.LONG  # Default

    @pytest.mark.timeout(10)
    def test_convert_order_type_to_ccxt(self):
        """Test order type conversion to CCXT format."""
        assert convert_order_type_to_ccxt(OrderType.MARKET) == "market"
        assert convert_order_type_to_ccxt(OrderType.LIMIT) == "limit"
        assert convert_order_type_to_ccxt(OrderType.STOP) == "stop_market"
        assert convert_order_type_to_ccxt(OrderType.FAK) == "immediate_or_cancel"
        assert convert_order_type_to_ccxt(OrderType.FOK) == "fill_or_kill"

    @pytest.mark.timeout(10)
    def test_convert_order_type_from_ccxt(self):
        """Test order type conversion from CCXT format."""
        assert convert_order_type_from_ccxt("market") == OrderType.MARKET
        assert convert_order_type_from_ccxt("limit") == OrderType.LIMIT
        assert convert_order_type_from_ccxt("stop_market") == OrderType.STOP
        assert convert_order_type_from_ccxt("stop_limit") == OrderType.STOP
        assert convert_order_type_from_ccxt("immediate_or_cancel") == OrderType.FAK
        assert convert_order_type_from_ccxt("fill_or_kill") == OrderType.FOK
        assert convert_order_type_from_ccxt("unknown") == OrderType.LIMIT  # Default

    @pytest.mark.timeout(10)
    def test_convert_status_from_ccxt(self):
        """Test status conversion from CCXT format."""
        assert convert_status_from_ccxt("open") == Status.NOTTRADED
        assert convert_status_from_ccxt("closed") == Status.ALLTRADED
        assert convert_status_from_ccxt("canceled") == Status.CANCELLED
        assert convert_status_from_ccxt("cancelled") == Status.CANCELLED
        assert convert_status_from_ccxt("partial") == Status.PARTTRADED
        assert convert_status_from_ccxt("partially_filled") == Status.PARTTRADED
        assert convert_status_from_ccxt("filled") == Status.ALLTRADED
        assert convert_status_from_ccxt("expired") == Status.CANCELLED
        assert convert_status_from_ccxt("rejected") == Status.REJECTED
        assert convert_status_from_ccxt("pending") == Status.SUBMITTING
        assert convert_status_from_ccxt("unknown") == Status.SUBMITTING  # Default

    @pytest.mark.timeout(10)
    def test_convert_status_to_ccxt(self):
        """Test status conversion to CCXT format."""
        assert convert_status_to_ccxt(Status.SUBMITTING) == "pending"
        assert convert_status_to_ccxt(Status.NOTTRADED) == "open"
        assert convert_status_to_ccxt(Status.PARTTRADED) == "partial"
        assert convert_status_to_ccxt(Status.ALLTRADED) == "closed"
        assert convert_status_to_ccxt(Status.CANCELLED) == "canceled"
        assert convert_status_to_ccxt(Status.REJECTED) == "rejected"

    @pytest.mark.timeout(10)
    def test_classify_error_network(self):
        """Test classification of network errors."""
        network_errors = [
            Exception("Network timeout"),
            Exception("Connection failed"),
            Exception("Service unavailable"),
            Exception("Network error occurred"),
        ]

        for error in network_errors:
            assert classify_error(error) == "network_error"

    @pytest.mark.timeout(10)
    def test_classify_error_auth(self):
        """Test classification of authentication errors."""
        auth_errors = [
            Exception("Authentication failed"),
            Exception("Invalid API key"),
            Exception("Signature verification failed"),
            Exception("Timestamp out of range"),
        ]

        for error in auth_errors:
            assert classify_error(error) == "auth_error"

    @pytest.mark.timeout(10)
    def test_classify_error_rate_limit(self):
        """Test classification of rate limit errors."""
        rate_limit_errors = [
            Exception("Rate limit exceeded"),
            Exception("Too many requests"),
            Exception("HTTP 429 error"),
        ]

        for error in rate_limit_errors:
            assert classify_error(error) == "rate_limit"

    @pytest.mark.timeout(10)
    def test_classify_error_invalid_request(self):
        """Test classification of invalid request errors."""
        invalid_errors = [
            Exception("Invalid order parameters"),
            Exception("Bad request format"),
            Exception("Insufficient balance"),
            Exception("Below minimum order size"),
        ]

        for error in invalid_errors:
            assert classify_error(error) == "invalid_request"

    @pytest.mark.timeout(10)
    def test_classify_error_market(self):
        """Test classification of market errors."""
        market_errors = [
            Exception("Market is closed"),
            Exception("Symbol not found"),
            Exception("Trading pair not available"),
        ]

        for error in market_errors:
            assert classify_error(error) == "market_error"

    @pytest.mark.timeout(10)
    def test_classify_error_unknown(self):
        """Test classification of unknown errors."""
        unknown_error = Exception("Some unexpected error")
        assert classify_error(unknown_error) == "unknown_error"

    @pytest.mark.timeout(10)
    def test_get_retry_delay_network_error(self):
        """Test retry delay calculation for network errors."""
        assert get_retry_delay("network_error", 1) == 2
        assert get_retry_delay("network_error", 2) == 4
        assert get_retry_delay("network_error", 3) == 8
        assert get_retry_delay("network_error", 10) == 30  # Max cap

    @pytest.mark.timeout(10)
    def test_get_retry_delay_rate_limit(self):
        """Test retry delay calculation for rate limit errors."""
        assert get_retry_delay("rate_limit", 1) == 10
        assert get_retry_delay("rate_limit", 2) == 20
        assert get_retry_delay("rate_limit", 3) == 40
        assert get_retry_delay("rate_limit", 10) == 60  # Max cap

    @pytest.mark.timeout(10)
    def test_get_retry_delay_no_retry_errors(self):
        """Test retry delay for errors that should not be retried."""
        no_retry_errors = ["auth_error", "invalid_request", "market_error"]

        for error_type in no_retry_errors:
            assert get_retry_delay(error_type, 1) == 0
            assert get_retry_delay(error_type, 2) == 0

    @pytest.mark.timeout(10)
    def test_get_retry_delay_unknown_error(self):
        """Test retry delay calculation for unknown errors."""
        assert get_retry_delay("unknown_error", 1) == 2
        assert get_retry_delay("unknown_error", 2) == 4
        assert get_retry_delay("unknown_error", 5) == 10  # Max cap

    @pytest.mark.timeout(10)
    def test_should_retry_error_retriable(self):
        """Test retry decision for retriable errors."""
        retriable_errors = ["network_error", "rate_limit", "unknown_error"]

        for error_type in retriable_errors:
            assert should_retry_error(error_type, 1) is True
            assert should_retry_error(error_type, 2) is True
            assert should_retry_error(error_type, 3) is False  # Max attempts reached

    @pytest.mark.timeout(10)
    def test_should_retry_error_non_retriable(self):
        """Test retry decision for non-retriable errors."""
        non_retriable_errors = ["auth_error", "invalid_request", "market_error"]

        for error_type in non_retriable_errors:
            assert should_retry_error(error_type, 1) is False
            assert should_retry_error(error_type, 2) is False

    @pytest.mark.timeout(10)
    def test_should_retry_error_max_attempts(self):
        """Test retry decision respects maximum attempts."""
        assert should_retry_error("network_error", 3, max_attempts=3) is False
        assert should_retry_error("network_error", 4, max_attempts=3) is False
        assert should_retry_error("network_error", 2, max_attempts=5) is True
