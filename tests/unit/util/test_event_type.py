"""
Unit tests for utility event_type module.

Tests all event type constants to ensure proper string values
and comprehensive coverage of trading platform event types.
"""

import pytest

from foxtrot.util.event_type import (
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_QUOTE,
    EVENT_TICK,
    EVENT_TIMER,
    EVENT_TRADE,
)


class TestEventTypeConstants:
    """Test event type constant values."""

    def test_event_tick_value(self):
        """Test EVENT_TICK constant value."""
        assert EVENT_TICK == "eTick."
        assert isinstance(EVENT_TICK, str)

    def test_event_trade_value(self):
        """Test EVENT_TRADE constant value."""
        assert EVENT_TRADE == "eTrade."
        assert isinstance(EVENT_TRADE, str)

    def test_event_order_value(self):
        """Test EVENT_ORDER constant value."""
        assert EVENT_ORDER == "eOrder."
        assert isinstance(EVENT_ORDER, str)

    def test_event_position_value(self):
        """Test EVENT_POSITION constant value."""
        assert EVENT_POSITION == "ePosition."
        assert isinstance(EVENT_POSITION, str)

    def test_event_account_value(self):
        """Test EVENT_ACCOUNT constant value."""
        assert EVENT_ACCOUNT == "eAccount."
        assert isinstance(EVENT_ACCOUNT, str)

    def test_event_quote_value(self):
        """Test EVENT_QUOTE constant value."""
        assert EVENT_QUOTE == "eQuote."
        assert isinstance(EVENT_QUOTE, str)

    def test_event_contract_value(self):
        """Test EVENT_CONTRACT constant value."""
        assert EVENT_CONTRACT == "eContract."
        assert isinstance(EVENT_CONTRACT, str)

    def test_event_log_value(self):
        """Test EVENT_LOG constant value."""
        assert EVENT_LOG == "eLog"
        assert isinstance(EVENT_LOG, str)

    def test_event_timer_value(self):
        """Test EVENT_TIMER constant value."""
        assert EVENT_TIMER == "eTimer"
        assert isinstance(EVENT_TIMER, str)


class TestEventTypeFormat:
    """Test event type format consistency."""

    def test_dotted_event_types(self):
        """Test event types that use dot notation."""
        dotted_events = [
            EVENT_TICK,
            EVENT_TRADE,
            EVENT_ORDER,
            EVENT_POSITION,
            EVENT_ACCOUNT,
            EVENT_QUOTE,
            EVENT_CONTRACT,
        ]

        for event_type in dotted_events:
            assert event_type.endswith(".")
            assert event_type.startswith("e")
            assert len(event_type) >= 3  # At least "eX."

    def test_non_dotted_event_types(self):
        """Test event types that don't use dot notation."""
        non_dotted_events = [EVENT_LOG, EVENT_TIMER]

        for event_type in non_dotted_events:
            assert not event_type.endswith(".")
            assert event_type.startswith("e")

    def test_event_type_prefix_consistency(self):
        """Test all event types start with 'e' prefix."""
        all_event_types = [
            EVENT_TICK,
            EVENT_TRADE,
            EVENT_ORDER,
            EVENT_POSITION,
            EVENT_ACCOUNT,
            EVENT_QUOTE,
            EVENT_CONTRACT,
            EVENT_LOG,
            EVENT_TIMER,
        ]

        for event_type in all_event_types:
            assert event_type.startswith("e")
            assert len(event_type) >= 2  # At least "eX"


class TestEventTypeUsage:
    """Test event type usage patterns."""

    def test_trading_data_event_types(self):
        """Test event types related to trading data."""
        trading_events = [EVENT_TICK, EVENT_TRADE, EVENT_ORDER, EVENT_POSITION, EVENT_ACCOUNT]

        for event_type in trading_events:
            assert event_type.endswith(".")
            # These can be extended with symbol/identifier
            extended_event = event_type + "AAPL.NYSE"
            assert extended_event.startswith(event_type)

    def test_market_data_event_types(self):
        """Test event types related to market data."""
        market_events = [EVENT_TICK, EVENT_QUOTE, EVENT_CONTRACT]

        for event_type in market_events:
            assert event_type.endswith(".")
            # These typically include symbol information

    def test_system_event_types(self):
        """Test system-level event types."""
        system_events = [EVENT_LOG, EVENT_TIMER]

        for event_type in system_events:
            assert not event_type.endswith(".")
            # These are typically used as-is without extension

    def test_event_type_uniqueness(self):
        """Test all event types are unique."""
        all_event_types = [
            EVENT_TICK,
            EVENT_TRADE,
            EVENT_ORDER,
            EVENT_POSITION,
            EVENT_ACCOUNT,
            EVENT_QUOTE,
            EVENT_CONTRACT,
            EVENT_LOG,
            EVENT_TIMER,
        ]

        unique_event_types = set(all_event_types)
        assert len(unique_event_types) == len(all_event_types)

    def test_event_type_string_operations(self):
        """Test string operations on event types."""
        # Test concatenation
        tick_symbol = EVENT_TICK + "BTCUSDT.BINANCE"
        assert tick_symbol == "eTick.BTCUSDT.BINANCE"

        # Test contains
        assert "Tick" in EVENT_TICK
        assert "Timer" in EVENT_TIMER

        # Test case sensitivity
        assert EVENT_TICK.lower() != EVENT_TICK
        assert EVENT_TICK.upper() != EVENT_TICK


class TestEventTypeConstants:
    """Test event type constants as module attributes."""

    def test_constants_are_strings(self):
        """Test all event type constants are strings."""
        import foxtrot.util.event_type as event_type_module

        for attr_name in dir(event_type_module):
            if attr_name.startswith("EVENT_"):
                attr_value = getattr(event_type_module, attr_name)
                assert isinstance(attr_value, str)

    def test_constants_count(self):
        """Test expected number of event type constants."""
        import foxtrot.util.event_type as event_type_module

        event_constants = [attr for attr in dir(event_type_module) if attr.startswith("EVENT_")]
        assert len(event_constants) == 9

    def test_constants_naming_convention(self):
        """Test event type constants follow naming convention."""
        import foxtrot.util.event_type as event_type_module

        for attr_name in dir(event_type_module):
            if attr_name.startswith("EVENT_"):
                # Should be all uppercase with underscores
                assert attr_name.isupper()
                assert attr_name.startswith("EVENT_")

                # Get the value and check it starts with 'e'
                attr_value = getattr(event_type_module, attr_name)
                assert attr_value.startswith("e")


class TestEventTypeDocumentation:
    """Test event type module documentation."""

    def test_module_docstring(self):
        """Test module has proper docstring."""
        import foxtrot.util.event_type as event_type_module

        assert event_type_module.__doc__ is not None
        assert "Event type string" in event_type_module.__doc__

    def test_event_type_semantic_meaning(self):
        """Test event types have clear semantic meaning."""
        # Test that event type names match their values semantically
        assert "Tick" in EVENT_TICK
        assert "Trade" in EVENT_TRADE
        assert "Order" in EVENT_ORDER
        assert "Position" in EVENT_POSITION
        assert "Account" in EVENT_ACCOUNT
        assert "Quote" in EVENT_QUOTE
        assert "Contract" in EVENT_CONTRACT
        assert "Log" in EVENT_LOG
        assert "Timer" in EVENT_TIMER


class TestEventTypeEdgeCases:
    """Test edge cases and error conditions."""

    def test_event_type_immutability(self):
        """Test event type constants are immutable strings."""
        original_tick = EVENT_TICK

        # Strings are immutable in Python, but test assignment doesn't change original
        modified_tick = EVENT_TICK + "test"
        assert original_tick == EVENT_TICK
        assert modified_tick != EVENT_TICK

    def test_event_type_comparison(self):
        """Test event type comparison operations."""
        assert EVENT_TICK == EVENT_TICK
        assert EVENT_TICK != EVENT_TRADE

        # Test lexicographic ordering
        assert EVENT_ACCOUNT < EVENT_TICK  # "eAccount." < "eTick."
        assert EVENT_LOG < EVENT_TIMER  # "eLog" < "eTimer"

    def test_event_type_boolean_context(self):
        """Test event types in boolean context."""
        # All event types should be truthy (non-empty strings)
        all_event_types = [
            EVENT_TICK,
            EVENT_TRADE,
            EVENT_ORDER,
            EVENT_POSITION,
            EVENT_ACCOUNT,
            EVENT_QUOTE,
            EVENT_CONTRACT,
            EVENT_LOG,
            EVENT_TIMER,
        ]

        for event_type in all_event_types:
            assert bool(event_type) is True
            assert len(event_type) > 0

    def test_event_type_hash_consistency(self):
        """Test event types are hashable and hash consistently."""
        event_set = {EVENT_TICK, EVENT_TRADE, EVENT_TICK}
        assert len(event_set) == 2  # Duplicate EVENT_TICK

        event_dict = {EVENT_TICK: "tick_data", EVENT_TRADE: "trade_data"}
        assert len(event_dict) == 2
        assert event_dict[EVENT_TICK] == "tick_data"


class TestEventTypeIntegration:
    """Test event types integration with other modules."""

    def test_event_type_imports(self):
        """Test event types can be imported correctly."""
        # Test individual imports
        from foxtrot.util.event_type import EVENT_TICK

        assert EVENT_TICK == "eTick."

        # Test wildcard import capability (though not recommended)
        exec("from foxtrot.util.event_type import *")

        # Verify all expected names are available in local scope
        local_vars = locals()
        expected_events = [
            "EVENT_TICK",
            "EVENT_TRADE",
            "EVENT_ORDER",
            "EVENT_POSITION",
            "EVENT_ACCOUNT",
            "EVENT_QUOTE",
            "EVENT_CONTRACT",
            "EVENT_LOG",
            "EVENT_TIMER",
        ]

        for event_name in expected_events:
            assert event_name in local_vars

    def test_event_type_module_attributes(self):
        """Test event type module has expected attributes."""
        import foxtrot.util.event_type as event_type_module

        # Test module has __file__ attribute
        assert hasattr(event_type_module, "__file__")

        # Test module has expected constants
        expected_constants = [
            "EVENT_TICK",
            "EVENT_TRADE",
            "EVENT_ORDER",
            "EVENT_POSITION",
            "EVENT_ACCOUNT",
            "EVENT_QUOTE",
            "EVENT_CONTRACT",
            "EVENT_LOG",
            "EVENT_TIMER",
        ]

        for constant in expected_constants:
            assert hasattr(event_type_module, constant)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
