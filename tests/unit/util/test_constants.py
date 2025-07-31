"""
Unit tests for utility constants module.

Tests all enum classes and their values to ensure comprehensive coverage
of trading platform constants and proper enum functionality.
"""

from enum import Enum

import pytest

from foxtrot.util.constants import (
    Currency,
    Direction,
    Exchange,
    Interval,
    Offset,
    OptionType,
    OrderType,
    Product,
    Status,
)


class TestDirection:
    """Test Direction enum functionality."""

    @pytest.mark.timeout(10)
    def test_direction_enum_values(self):
        """Test all Direction enum values."""
        assert Direction.LONG.value == "LONG"
        assert Direction.SHORT.value == "SHORT"
        assert Direction.NET.value == "NET"

    @pytest.mark.timeout(10)
    def test_direction_enum_membership(self):
        """Test Direction enum membership."""
        assert Direction.LONG in Direction
        assert Direction.SHORT in Direction
        assert Direction.NET in Direction

        # Test non-member
        assert "INVALID" not in [d.value for d in Direction]

    @pytest.mark.timeout(10)
    def test_direction_enum_count(self):
        """Test Direction enum has expected number of values."""
        assert len(Direction) == 3

    @pytest.mark.timeout(10)
    def test_direction_enum_iteration(self):
        """Test Direction enum iteration."""
        directions = list(Direction)
        assert len(directions) == 3
        assert Direction.LONG in directions
        assert Direction.SHORT in directions
        assert Direction.NET in directions

    @pytest.mark.timeout(10)
    def test_direction_enum_inheritance(self):
        """Test Direction inherits from Enum."""
        assert issubclass(Direction, Enum)
        assert isinstance(Direction.LONG, Direction)


class TestOffset:
    """Test Offset enum functionality."""

    @pytest.mark.timeout(10)
    def test_offset_enum_values(self):
        """Test all Offset enum values."""
        assert Offset.NONE.value == ""
        assert Offset.OPEN.value == "OPEN"
        assert Offset.CLOSE.value == "CLOSE"
        assert Offset.CLOSETODAY.value == "CLOSETODAY"
        assert Offset.CLOSEYESTERDAY.value == "CLOSEYESTERDAY"

    @pytest.mark.timeout(10)
    def test_offset_enum_empty_string_value(self):
        """Test Offset.NONE has empty string value."""
        assert Offset.NONE.value == ""
        assert str(Offset.NONE.value) == ""

    @pytest.mark.timeout(10)
    def test_offset_enum_count(self):
        """Test Offset enum has expected number of values."""
        assert len(Offset) == 5

    @pytest.mark.timeout(10)
    def test_offset_enum_trading_operations(self):
        """Test Offset values for trading operations."""
        trading_offsets = [Offset.OPEN, Offset.CLOSE, Offset.CLOSETODAY, Offset.CLOSEYESTERDAY]
        for offset in trading_offsets:
            assert offset.value != ""
            assert isinstance(offset.value, str)


class TestStatus:
    """Test Status enum functionality."""

    @pytest.mark.timeout(10)
    def test_status_enum_values(self):
        """Test all Status enum values."""
        assert Status.SUBMITTING.value == "SUBMITTING"
        assert Status.NOTTRADED.value == "NOTTRADED"
        assert Status.PARTTRADED.value == "PARTTRADED"
        assert Status.ALLTRADED.value == "ALLTRADED"
        assert Status.CANCELLED.value == "CANCELLED"
        assert Status.REJECTED.value == "REJECTED"

    @pytest.mark.timeout(10)
    def test_status_enum_count(self):
        """Test Status enum has expected number of values."""
        assert len(Status) == 6

    @pytest.mark.timeout(10)
    def test_status_active_vs_inactive(self):
        """Test Status values categorization."""
        active_statuses = [Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED]
        inactive_statuses = [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]

        all_statuses = active_statuses + inactive_statuses
        assert len(all_statuses) == len(Status)

        for status in Status:
            assert status in all_statuses


class TestProduct:
    """Test Product enum functionality."""

    @pytest.mark.timeout(10)
    def test_product_enum_values(self):
        """Test key Product enum values."""
        assert Product.EQUITY.value == "EQUITY"
        assert Product.FUTURES.value == "FUTURES"
        assert Product.OPTION.value == "OPTION"
        assert Product.FOREX.value == "FOREX"
        assert Product.SPOT.value == "SPOT"
        assert Product.ETF.value == "ETF"
        assert Product.BOND.value == "BOND"
        assert Product.CFD.value == "CFD"

    @pytest.mark.timeout(10)
    def test_product_enum_count(self):
        """Test Product enum has expected number of values."""
        assert len(Product) == 13

    @pytest.mark.timeout(10)
    def test_product_equity_types(self):
        """Test equity-related product types."""
        equity_types = [Product.EQUITY, Product.ETF, Product.WARRANT]
        for product in equity_types:
            assert product in Product

    @pytest.mark.timeout(10)
    def test_product_derivative_types(self):
        """Test derivative product types."""
        derivative_types = [Product.FUTURES, Product.OPTION, Product.SWAP, Product.CFD]
        for product in derivative_types:
            assert product in Product


class TestOrderType:
    """Test OrderType enum functionality."""

    @pytest.mark.timeout(10)
    def test_ordertype_enum_values(self):
        """Test all OrderType enum values."""
        assert OrderType.LIMIT.value == "LIMIT"
        assert OrderType.MARKET.value == "MARKET"
        assert OrderType.STOP.value == "STOP"
        assert OrderType.FAK.value == "FAK"
        assert OrderType.FOK.value == "FOK"
        assert OrderType.RFQ.value == "RFQ"
        assert OrderType.ETF.value == "ETF"

    @pytest.mark.timeout(10)
    def test_ordertype_enum_count(self):
        """Test OrderType enum has expected number of values."""
        assert len(OrderType) == 7

    @pytest.mark.timeout(10)
    def test_ordertype_execution_types(self):
        """Test order execution type categorization."""
        immediate_execution = [OrderType.MARKET, OrderType.FAK, OrderType.FOK]
        for order_type in immediate_execution:
            assert order_type in OrderType

        limit_based = [OrderType.LIMIT, OrderType.STOP]
        for order_type in limit_based:
            assert order_type in OrderType


class TestOptionType:
    """Test OptionType enum functionality."""

    @pytest.mark.timeout(10)
    def test_optiontype_enum_values(self):
        """Test all OptionType enum values."""
        assert OptionType.CALL.value == "CALL"
        assert OptionType.PUT.value == "PUT"

    @pytest.mark.timeout(10)
    def test_optiontype_enum_count(self):
        """Test OptionType enum has expected number of values."""
        assert len(OptionType) == 2

    @pytest.mark.timeout(10)
    def test_optiontype_completeness(self):
        """Test OptionType covers all option types."""
        option_types = list(OptionType)
        assert OptionType.CALL in option_types
        assert OptionType.PUT in option_types


class TestExchange:
    """Test Exchange enum functionality."""

    @pytest.mark.timeout(10)
    def test_exchange_chinese_markets(self):
        """Test Chinese exchange values."""
        chinese_exchanges = [
            Exchange.CFFEX,
            Exchange.SHFE,
            Exchange.CZCE,
            Exchange.DCE,
            Exchange.SSE,
            Exchange.SZSE,
            Exchange.BSE,
        ]

        for exchange in chinese_exchanges:
            assert exchange in Exchange
            assert isinstance(exchange.value, str)

    @pytest.mark.timeout(10)
    def test_exchange_global_markets(self):
        """Test global exchange values."""
        global_exchanges = [
            Exchange.NYSE,
            Exchange.NASDAQ,
            Exchange.SMART,
            Exchange.CME,
            Exchange.NYMEX,
            Exchange.GLOBEX,
        ]

        for exchange in global_exchanges:
            assert exchange in Exchange
            assert isinstance(exchange.value, str)

    @pytest.mark.timeout(10)
    def test_exchange_crypto_markets(self):
        """Test cryptocurrency exchange values."""
        crypto_exchanges = [
            Exchange.BINANCE,
            Exchange.BITMEX,
            Exchange.OKX,
            Exchange.COINBASE,
            Exchange.BYBIT,
        ]

        for exchange in crypto_exchanges:
            assert exchange in Exchange
            assert isinstance(exchange.value, str)

    @pytest.mark.timeout(10)
    def test_exchange_special_values(self):
        """Test special exchange values."""
        assert Exchange.LOCAL.value == "LOCAL"
        assert Exchange.GLOBAL.value == "GLOBAL"
        assert Exchange.OTC.value == "OTC"

    @pytest.mark.timeout(10)
    def test_exchange_enum_count(self):
        """Test Exchange enum has expected minimum number of values."""
        # Should have at least 40 exchanges based on the constants file
        assert len(Exchange) >= 40

    @pytest.mark.timeout(10)
    def test_exchange_value_uniqueness(self):
        """Test all exchange values are unique."""
        values = [exchange.value for exchange in Exchange]
        assert len(values) == len(set(values))


class TestCurrency:
    """Test Currency enum functionality."""

    @pytest.mark.timeout(10)
    def test_currency_enum_values(self):
        """Test all Currency enum values."""
        assert Currency.USD.value == "USD"
        assert Currency.HKD.value == "HKD"
        assert Currency.CNY.value == "CNY"
        assert Currency.CAD.value == "CAD"

    @pytest.mark.timeout(10)
    def test_currency_enum_count(self):
        """Test Currency enum has expected number of values."""
        assert len(Currency) == 4

    @pytest.mark.timeout(10)
    def test_currency_major_currencies(self):
        """Test major currency representation."""
        major_currencies = [Currency.USD, Currency.CNY]
        for currency in major_currencies:
            assert currency in Currency


class TestInterval:
    """Test Interval enum functionality."""

    @pytest.mark.timeout(10)
    def test_interval_enum_values(self):
        """Test all Interval enum values."""
        assert Interval.MINUTE.value == "1m"
        assert Interval.HOUR.value == "1h"
        assert Interval.DAILY.value == "d"
        assert Interval.WEEKLY.value == "w"
        assert Interval.TICK.value == "tick"

    @pytest.mark.timeout(10)
    def test_interval_enum_count(self):
        """Test Interval enum has expected number of values."""
        assert len(Interval) == 5

    @pytest.mark.timeout(10)
    def test_interval_time_units(self):
        """Test interval time unit categorization."""
        time_based = [Interval.MINUTE, Interval.HOUR, Interval.DAILY, Interval.WEEKLY]
        for interval in time_based:
            assert interval in Interval

        # Tick is special case
        assert Interval.TICK.value == "tick"

    @pytest.mark.timeout(10)
    def test_interval_format_consistency(self):
        """Test interval value format consistency."""
        # Most intervals should be short format
        for interval in Interval:
            assert len(interval.value) <= 4
            assert isinstance(interval.value, str)


class TestEnumEdgeCases:
    """Test edge cases and error conditions for all enums."""

    @pytest.mark.timeout(10)
    def test_enum_string_conversion(self):
        """Test enum string conversion."""
        assert str(Direction.LONG) == "Direction.LONG"
        assert Direction.LONG.value == "LONG"

        assert str(Exchange.NYSE) == "Exchange.NYSE"
        assert Exchange.NYSE.value == "NYSE"

    @pytest.mark.timeout(10)
    def test_enum_equality_comparison(self):
        """Test enum equality comparisons."""
        assert Direction.LONG == Direction.LONG
        assert Direction.LONG != Direction.SHORT

        assert Exchange.NYSE == Exchange.NYSE
        assert Exchange.NYSE != Exchange.NASDAQ

    @pytest.mark.timeout(10)
    def test_enum_hash_consistency(self):
        """Test enum values are hashable and consistent."""
        direction_set = {Direction.LONG, Direction.SHORT, Direction.LONG}
        assert len(direction_set) == 2  # Duplicate LONG should be deduplicated

        exchange_dict = {Exchange.NYSE: "New York", Exchange.NASDAQ: "NASDAQ"}
        assert len(exchange_dict) == 2

    @pytest.mark.timeout(10)
    def test_enum_invalid_access(self):
        """Test accessing invalid enum values raises appropriate errors."""
        with pytest.raises(ValueError):
            Direction("INVALID_DIRECTION")

        with pytest.raises(ValueError):
            Exchange("INVALID_EXCHANGE")

        with pytest.raises(AttributeError):
            Direction.INVALID_DIRECTION

    @pytest.mark.timeout(10)
    def test_enum_case_sensitivity(self):
        """Test enum case sensitivity."""
        # These should work
        assert Direction.LONG.value == "LONG"
        assert Direction("LONG") == Direction.LONG

        # These should fail
        with pytest.raises(ValueError):
            Direction("long")  # lowercase

        with pytest.raises(ValueError):
            Direction("Long")  # mixed case


class TestEnumComprehensiveValues:
    """Test comprehensive coverage of all enum values."""

    @pytest.mark.timeout(10)
    def test_all_direction_values_tested(self):
        """Ensure all Direction values are covered."""
        tested_directions = {Direction.LONG, Direction.SHORT, Direction.NET}
        all_directions = set(Direction)
        assert tested_directions == all_directions

    @pytest.mark.timeout(10)
    def test_all_status_values_tested(self):
        """Ensure all Status values are covered."""
        tested_statuses = {
            Status.SUBMITTING,
            Status.NOTTRADED,
            Status.PARTTRADED,
            Status.ALLTRADED,
            Status.CANCELLED,
            Status.REJECTED,
        }
        all_statuses = set(Status)
        assert tested_statuses == all_statuses

    @pytest.mark.timeout(10)
    def test_critical_exchange_values_present(self):
        """Test critical exchange values are present."""
        critical_exchanges = [
            Exchange.NYSE,
            Exchange.NASDAQ,
            Exchange.BINANCE,
            Exchange.SSE,
            Exchange.SZSE,
            Exchange.SMART,
        ]

        for exchange in critical_exchanges:
            assert exchange in Exchange

    @pytest.mark.timeout(10)
    def test_enum_docstrings_present(self):
        """Test that enums have proper docstrings."""
        assert Direction.__doc__ is not None
        assert "Direction of order/trade/position" in Direction.__doc__

        assert Exchange.__doc__ is not None
        assert "Exchange" in Exchange.__doc__

        assert Product.__doc__ is not None
        assert "Product class" in Product.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
