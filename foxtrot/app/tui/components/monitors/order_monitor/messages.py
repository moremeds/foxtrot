"""
Order monitor message classes.

Defines message types used for communication between order monitor
and other TUI components.
"""

from textual.message import Message
from foxtrot.util.object import OrderData


class OrderCancelRequested(Message):
    """Message sent when an order cancel is requested."""

    def __init__(self, order_data: OrderData) -> None:
        """Initialize the order cancel request message."""
        self.order_data = order_data
        super().__init__()


class AllOrdersCancelRequested(Message):
    """Message sent when cancel all orders is requested."""

    def __init__(self, symbol_filter: str | None = None) -> None:
        """Initialize the cancel all orders request message."""
        self.symbol_filter = symbol_filter
        super().__init__()


class OrderSelected(Message):
    """Message sent when an order is selected for trading panel update."""

    def __init__(self, order_data: OrderData) -> None:
        """Initialize the order selected message."""
        self.order_data = order_data
        super().__init__()


class OrderFilterChanged(Message):
    """Message sent when order filters are changed."""

    def __init__(self, filter_summary: str) -> None:
        """Initialize the filter changed message."""
        self.filter_summary = filter_summary
        super().__init__()


class OrderStatisticsUpdated(Message):
    """Message sent when order statistics are updated."""

    def __init__(self, statistics: dict) -> None:
        """Initialize the statistics updated message."""
        self.statistics = statistics
        super().__init__()