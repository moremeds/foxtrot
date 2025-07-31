"""
Unit tests for Futu data mapping functions.

This module tests all data conversion functions between Futu SDK and VT formats.
"""

import pytest

import unittest

from foxtrot.adapter.futu.futu_mappings import (
    convert_direction_to_futu,
    convert_futu_market_to_exchange,
    convert_futu_order_status,
    convert_futu_to_vt_direction,
    convert_futu_to_vt_order_type,
    convert_futu_to_vt_symbol,
    convert_order_type_to_futu,
    convert_symbol_to_futu_market,
    get_futu_market_enum,
    get_futu_trd_market,
    get_market_from_vt_symbol,
    validate_symbol_format,
)
from foxtrot.util.constants import Direction, Exchange, OrderType, Status

from .mock_futu_sdk import Market, OrderStatus, TrdMarket, TrdSide
from .mock_futu_sdk import OrderType as FutuOrderType


class TestFutuMappings(unittest.TestCase):
    """Test cases for Futu data mapping functions."""

    @pytest.mark.timeout(10)
    def test_symbol_conversion_to_futu(self) -> None:
        """Test VT symbol to Futu format conversion."""
        # Test HK stocks
        market, code = convert_symbol_to_futu_market("0700.SEHK")
        self.assertEqual(market, "HK")
        self.assertEqual(code, "HK.00700")

        market, code = convert_symbol_to_futu_market("5.SEHK")
        self.assertEqual(market, "HK")
        self.assertEqual(code, "HK.00005")

        # Test US stocks
        market, code = convert_symbol_to_futu_market("AAPL.NASDAQ")
        self.assertEqual(market, "US")
        self.assertEqual(code, "US.AAPL")

        market, code = convert_symbol_to_futu_market("GOOGL.NYSE")
        self.assertEqual(market, "US")
        self.assertEqual(code, "US.GOOGL")

        # Test CN stocks
        market, code = convert_symbol_to_futu_market("000001.SZSE")
        self.assertEqual(market, "CN")
        self.assertEqual(code, "CN.000001")

        market, code = convert_symbol_to_futu_market("600000.SSE")
        self.assertEqual(market, "CN")
        self.assertEqual(code, "CN.600000")

    @pytest.mark.timeout(10)
    def test_symbol_conversion_to_futu_invalid(self) -> None:
        """Test invalid symbol conversion."""
        with self.assertRaises(ValueError):
            convert_symbol_to_futu_market("INVALID.UNKNOWN")

    @pytest.mark.timeout(10)
    def test_symbol_conversion_from_futu(self) -> None:
        """Test Futu format to VT symbol conversion."""
        # Test HK stocks
        vt_symbol = convert_futu_to_vt_symbol("HK", "HK.00700")
        self.assertEqual(vt_symbol, "0700.SEHK")

        vt_symbol = convert_futu_to_vt_symbol("HK", "HK.00005")
        self.assertEqual(vt_symbol, "5.SEHK")

        # Test US stocks
        vt_symbol = convert_futu_to_vt_symbol("US", "US.AAPL")
        self.assertEqual(vt_symbol, "AAPL.NASDAQ")  # Default to NASDAQ

        # Test CN stocks
        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.000001")
        self.assertEqual(vt_symbol, "000001.SZSE")  # Default to SZSE

        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.600000")
        self.assertEqual(vt_symbol, "600000.SSE")  # SSE for 6xxxxx codes

    @pytest.mark.timeout(10)
    def test_order_type_conversion_to_futu(self) -> None:
        """Test VT order type to Futu conversion."""
        # Test basic order types
        futu_type = convert_order_type_to_futu(OrderType.LIMIT)
        self.assertEqual(futu_type, FutuOrderType.NORMAL)

        futu_type = convert_order_type_to_futu(OrderType.MARKET)
        self.assertEqual(futu_type, FutuOrderType.MARKET)

        futu_type = convert_order_type_to_futu(OrderType.STOP)
        self.assertEqual(futu_type, FutuOrderType.STOP)

        # Test default case
        futu_type = convert_order_type_to_futu(OrderType.FAK)  # Not supported
        self.assertEqual(futu_type, FutuOrderType.NORMAL)  # Default to NORMAL

    @pytest.mark.timeout(10)
    def test_order_type_conversion_from_futu(self) -> None:
        """Test Futu order type to VT conversion."""
        vt_type = convert_futu_to_vt_order_type(FutuOrderType.NORMAL)
        self.assertEqual(vt_type, OrderType.LIMIT)

        vt_type = convert_futu_to_vt_order_type(FutuOrderType.MARKET)
        self.assertEqual(vt_type, OrderType.MARKET)

        vt_type = convert_futu_to_vt_order_type(FutuOrderType.STOP)
        self.assertEqual(vt_type, OrderType.STOP)

    @pytest.mark.timeout(10)
    def test_direction_conversion_to_futu(self) -> None:
        """Test VT direction to Futu conversion."""
        futu_side = convert_direction_to_futu(Direction.LONG)
        self.assertEqual(futu_side, TrdSide.BUY)

        futu_side = convert_direction_to_futu(Direction.SHORT)
        self.assertEqual(futu_side, TrdSide.SELL)

    @pytest.mark.timeout(10)
    def test_direction_conversion_from_futu(self) -> None:
        """Test Futu direction to VT conversion."""
        vt_direction = convert_futu_to_vt_direction(TrdSide.BUY)
        self.assertEqual(vt_direction, Direction.LONG)

        vt_direction = convert_futu_to_vt_direction(TrdSide.SELL)
        self.assertEqual(vt_direction, Direction.SHORT)

    @pytest.mark.timeout(10)
    def test_order_status_conversion(self) -> None:
        """Test Futu order status to VT status conversion."""
        # Test basic status mappings
        vt_status = convert_futu_order_status(OrderStatus.SUBMITTING)
        self.assertEqual(vt_status, Status.SUBMITTING)

        vt_status = convert_futu_order_status(OrderStatus.SUBMITTED)
        self.assertEqual(vt_status, Status.NOTTRADED)

        vt_status = convert_futu_order_status(OrderStatus.FILLED_PART)
        self.assertEqual(vt_status, Status.PARTTRADED)

        vt_status = convert_futu_order_status(OrderStatus.FILLED_ALL)
        self.assertEqual(vt_status, Status.ALLTRADED)

        vt_status = convert_futu_order_status(OrderStatus.CANCELLED_ALL)
        self.assertEqual(vt_status, Status.CANCELLED)

        vt_status = convert_futu_order_status(OrderStatus.FAILED)
        self.assertEqual(vt_status, Status.REJECTED)

    @pytest.mark.timeout(10)
    def test_market_to_exchange_conversion(self) -> None:
        """Test market string to Exchange enum conversion."""
        exchange = convert_futu_market_to_exchange("HK")
        self.assertEqual(exchange, Exchange.SEHK)

        exchange = convert_futu_market_to_exchange("US")
        self.assertEqual(exchange, Exchange.NASDAQ)  # Default US exchange

        exchange = convert_futu_market_to_exchange("CN")
        self.assertEqual(exchange, Exchange.SZSE)  # Default CN exchange

        # Test default case
        exchange = convert_futu_market_to_exchange("UNKNOWN")
        self.assertEqual(exchange, Exchange.SEHK)  # Default

    @pytest.mark.timeout(10)
    def test_get_futu_trd_market(self) -> None:
        """Test Futu trade market enum retrieval."""
        trd_market = get_futu_trd_market("HK")
        self.assertEqual(trd_market, TrdMarket.HK)

        trd_market = get_futu_trd_market("US")
        self.assertEqual(trd_market, TrdMarket.US)

        trd_market = get_futu_trd_market("CN")
        self.assertEqual(trd_market, TrdMarket.CN)

        # Test default case
        trd_market = get_futu_trd_market("UNKNOWN")
        self.assertEqual(trd_market, TrdMarket.HK)  # Default

    @pytest.mark.timeout(10)
    def test_get_futu_market_enum(self) -> None:
        """Test Futu market enum retrieval."""
        market = get_futu_market_enum("HK")
        self.assertEqual(market, Market.HK)

        market = get_futu_market_enum("US")
        self.assertEqual(market, Market.US)

        market = get_futu_market_enum("CN")
        # The function should return HK as fallback if CN_SH is not available
        # In tests with real futu module, CN_SH may not exist
        self.assertIn(market, [Market.CN_SH, Market.HK])  # Either CN_SH or HK fallback

        # Test default case
        market = get_futu_market_enum("UNKNOWN")
        self.assertEqual(market, Market.HK)  # Default

    @pytest.mark.timeout(10)
    def test_validate_symbol_format(self) -> None:
        """Test VT symbol format validation."""
        # Test valid symbols
        self.assertTrue(validate_symbol_format("0700.SEHK"))
        self.assertTrue(validate_symbol_format("AAPL.NASDAQ"))
        self.assertTrue(validate_symbol_format("GOOGL.NYSE"))
        self.assertTrue(validate_symbol_format("000001.SZSE"))
        self.assertTrue(validate_symbol_format("600000.SSE"))

        # Test invalid symbols
        self.assertFalse(validate_symbol_format("INVALID"))  # No dot
        self.assertFalse(validate_symbol_format(".SEHK"))     # No symbol
        self.assertFalse(validate_symbol_format("0700."))     # No exchange
        self.assertFalse(validate_symbol_format(""))          # Empty
        self.assertFalse(validate_symbol_format("0700.UNKNOWN"))  # Unknown exchange

    @pytest.mark.timeout(10)
    def test_get_market_from_vt_symbol(self) -> None:
        """Test market extraction from VT symbol."""
        # Test HK symbols
        market = get_market_from_vt_symbol("0700.SEHK")
        self.assertEqual(market, "HK")

        # Test US symbols
        market = get_market_from_vt_symbol("AAPL.NASDAQ")
        self.assertEqual(market, "US")

        market = get_market_from_vt_symbol("GOOGL.NYSE")
        self.assertEqual(market, "US")

        # Test CN symbols
        market = get_market_from_vt_symbol("000001.SZSE")
        self.assertEqual(market, "CN")

        market = get_market_from_vt_symbol("600000.SSE")
        self.assertEqual(market, "CN")

        # Test invalid symbol
        with self.assertRaises(ValueError):
            get_market_from_vt_symbol("INVALID.UNKNOWN")

    @pytest.mark.timeout(10)
    def test_bidirectional_symbol_conversion(self) -> None:
        """Test bidirectional symbol conversion consistency."""
        test_symbols = [
            "0700.SEHK",
            "5.SEHK",
            "AAPL.NASDAQ",
            "GOOGL.NYSE",
            "000001.SZSE",
            "600000.SSE",
        ]

        for original_symbol in test_symbols:
            # Convert to Futu format
            market, code = convert_symbol_to_futu_market(original_symbol)

            # Convert back to VT format
            converted_symbol = convert_futu_to_vt_symbol(market, code)

            # Should match original (with padding handled correctly)
            if original_symbol == "5.SEHK":
                # Special case: "5" gets padded to "00005" and back to "5"
                self.assertEqual(converted_symbol, "5.SEHK")
            else:
                # For most symbols, US exchange inference might change NYSE to NASDAQ
                if ".NYSE" in original_symbol:
                    expected = original_symbol.replace("NYSE", "NASDAQ")
                    self.assertEqual(converted_symbol, expected)
                else:
                    self.assertEqual(converted_symbol, original_symbol)

    @pytest.mark.timeout(10)
    def test_cn_exchange_inference(self) -> None:
        """Test CN stock exchange inference logic."""
        # Test Shanghai Stock Exchange (6xxxxx codes)
        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.600000")
        self.assertEqual(vt_symbol, "600000.SSE")

        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.601988")
        self.assertEqual(vt_symbol, "601988.SSE")

        # Test Shenzhen Stock Exchange (000xxx, 002xxx codes)
        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.000001")
        self.assertEqual(vt_symbol, "000001.SZSE")

        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.002415")
        self.assertEqual(vt_symbol, "002415.SZSE")

        # Test default case (other codes default to SZSE)
        vt_symbol = convert_futu_to_vt_symbol("CN", "CN.300001")
        self.assertEqual(vt_symbol, "300001.SZSE")


if __name__ == '__main__':
    unittest.main()
