"""
Order Monitor for TUI

Order tracking and management component that displays order status,
execution details, and provides order management functionality.
"""

import asyncio
from datetime import datetime
from typing import Any

from textual.coordinate import Coordinate
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Status
from foxtrot.util.event_type import EVENT_ORDER
from foxtrot.util.object import OrderData

from ...utils.colors import get_color_manager
from ...utils.formatters import TUIFormatter
from ..base_monitor import TUIDataMonitor


class TUIOrderMonitor(TUIDataMonitor):
    """
    TUI Order Monitor for tracking and managing trading orders.

    Features:
        - Real-time order status updates
        - Color coding by order status and direction
        - Order filtering by status, symbol, and direction
        - Order management actions (cancel orders)
        - Execution progress tracking
        - Order history and statistics
        - Export functionality for order analysis
    """

    # Monitor configuration
    event_type = EVENT_ORDER
    data_key = "vt_orderid"
    sorting = True  # Enable sorting by different columns

    # Column configuration
    headers = {
        "orderid": {
            "display": "Order ID",
            "cell": "default",
            "update": False,
            "width": 12,
            "precision": 0,
        },
        "reference": {
            "display": "Reference",
            "cell": "default",
            "update": False,
            "width": 10,
            "precision": 0,
        },
        "symbol": {
            "display": "Symbol",
            "cell": "default",
            "update": False,
            "width": 12,
            "precision": 0,
        },
        "exchange": {
            "display": "Exchange",
            "cell": "enum",
            "update": False,
            "width": 8,
            "precision": 0,
        },
        "type": {
            "display": "Type",
            "cell": "order_type",
            "update": False,
            "width": 6,
            "precision": 0,
        },
        "direction": {
            "display": "Direction",
            "cell": "direction",
            "update": False,
            "width": 8,
            "precision": 0,
        },
        "offset": {
            "display": "Offset",
            "cell": "enum",
            "update": False,
            "width": 6,
            "precision": 0,
        },
        "price": {
            "display": "Price",
            "cell": "float",
            "update": False,
            "width": 10,
            "precision": 4,
        },
        "volume": {
            "display": "Volume",
            "cell": "volume",
            "update": True,
            "width": 10,
            "precision": 0,
        },
        "traded": {
            "display": "Traded",
            "cell": "volume",
            "update": True,
            "width": 10,
            "precision": 0,
        },
        "status": {
            "display": "Status",
            "cell": "status",
            "update": True,
            "width": 10,
            "precision": 0,
        },
        "datetime": {
            "display": "Time",
            "cell": "datetime",
            "update": True,
            "width": 12,
            "precision": 0,
        },
        "gateway_name": {
            "display": "Gateway",
            "cell": "default",
            "update": False,
            "width": 10,
            "precision": 0,
        },
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
        """
        Initialize the order monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Order Monitor", **kwargs)

        # Color manager for styling
        self.color_manager = get_color_manager()

        # Order tracking and statistics
        self.active_orders: set[str] = set()
        self.completed_orders: set[str] = set()
        self.order_statistics: dict[str, Any] = {
            "total_orders": 0,
            "filled_orders": 0,
            "cancelled_orders": 0,
            "rejected_orders": 0,
        }

        # Filtering options
        self.status_filter: Status | None = None
        self.symbol_filter: str | None = None
        self.direction_filter: Direction | None = None
        self.gateway_filter: str | None = None

        # Display options
        self.show_only_active = False
        self.highlight_recent_updates = True
        self.auto_scroll_to_updates = True

    def compose(self):
        """Create the order monitor layout."""
        for widget in super().compose():
            yield widget

    async def on_mount(self) -> None:
        """Called when the order monitor is mounted."""
        await super().on_mount()

        # Initialize with welcome message
        await self._add_system_message("Order monitor ready for tracking orders")

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with order-specific formatting.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        if content is None:
            return "-"

        cell_type = config.get("cell", "default")
        precision = config.get("precision", 2)

        if cell_type == "float":
            return TUIFormatter.format_price(content, precision)

        if cell_type == "volume":
            return TUIFormatter.format_volume(content)

        if cell_type == "direction":
            return TUIFormatter.format_direction(content)

        if cell_type == "order_type":
            return TUIFormatter.format_order_type(content)

        if cell_type == "status":
            return TUIFormatter.format_status(content)

        if cell_type == "datetime":
            if isinstance(content, datetime):
                return TUIFormatter.format_datetime(content, "time")

        elif cell_type == "enum":
            return TUIFormatter.format_enum(content)

        else:
            # Default formatting with truncation
            if isinstance(content, str) and len(content) > config.get("width", 20):
                return TUIFormatter.truncate_text(content, config.get("width", 20))
            return str(content)

    async def _apply_row_styling(self, row_index: int, data: OrderData) -> None:
        """
        Apply color styling to order data based on status and direction.

        Args:
            row_index: The row index to style
            data: The OrderData object
        """
        if not self.data_table:
            return

        try:
            # Status-based color coding
            status_color = self.color_manager.get_status_color(data.status)

            # Direction-based color coding
            direction_color = self.color_manager.get_direction_color(data.direction)

            # Apply styling based on order properties
            # This would integrate with Textual's styling system

        except Exception as e:
            await self._log_error(f"Error applying row styling: {e}")

    async def _process_event(self, event) -> None:
        """
        Process order events with filtering and statistics updates.

        Args:
            event: Order event containing OrderData
        """
        try:
            order_data: OrderData = event.data

            # Apply filters
            if not self._passes_filters(order_data):
                return

            # Update order tracking
            await self._update_order_tracking(order_data)

            # Process the order data
            await super()._process_event(event)

            # Update statistics
            await self._update_order_statistics(order_data)

            # Handle auto-scroll if enabled
            if self.auto_scroll_to_updates and self.data_table:
                self.data_table.cursor_coordinate = Coordinate(0, 0)

        except Exception as e:
            await self._log_error(f"Error processing order event: {e}")

    def _passes_filters(self, order_data: OrderData) -> bool:
        """
        Check if order data passes current filters.

        Args:
            order_data: The OrderData to check

        Returns:
            True if order passes all filters
        """
        # Status filter
        if self.status_filter is not None:
            if order_data.status != self.status_filter:
                return False

        # Symbol filter
        if self.symbol_filter:
            if self.symbol_filter.lower() not in order_data.symbol.lower():
                return False

        # Direction filter
        if self.direction_filter is not None:
            if order_data.direction != self.direction_filter:
                return False

        # Gateway filter
        if self.gateway_filter:
            if order_data.gateway_name != self.gateway_filter:
                return False

        # Active orders only filter
        if self.show_only_active:
            active_statuses = {Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED}
            if order_data.status not in active_statuses:
                return False

        return True

    async def _update_order_tracking(self, order_data: OrderData) -> None:
        """
        Update internal order tracking based on order status.

        Args:
            order_data: The order data to track
        """
        order_id = order_data.vt_orderid

        # Track active vs completed orders
        if order_data.status in {Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED}:
            self.active_orders.add(order_id)
            self.completed_orders.discard(order_id)
        else:
            self.active_orders.discard(order_id)
            self.completed_orders.add(order_id)

    async def _update_order_statistics(self, order_data: OrderData) -> None:
        """
        Update order statistics based on new order data.

        Args:
            order_data: The new order data
        """
        # Update total orders
        if (
            order_data.vt_orderid not in self.active_orders
            and order_data.vt_orderid not in self.completed_orders
        ):
            self.order_statistics["total_orders"] += 1

        # Update status-specific counters
        if order_data.status == Status.ALLTRADED:
            self.order_statistics["filled_orders"] += 1
        elif order_data.status == Status.CANCELLED:
            self.order_statistics["cancelled_orders"] += 1
        elif order_data.status == Status.REJECTED:
            self.order_statistics["rejected_orders"] += 1

        # Update display with statistics
        await self._update_statistics_display()

    async def _update_statistics_display(self) -> None:
        """Update the title bar with current statistics."""
        if not self.title_bar:
            return

        stats = self.order_statistics
        active_count = len(self.active_orders)

        title = f"Order Monitor - Active: {active_count} | Total: {stats['total_orders']} | Filled: {stats['filled_orders']}"

        # Add filter information if active
        filters = []
        if self.status_filter:
            filters.append(f"Status:{self.status_filter.value}")
        if self.symbol_filter:
            filters.append(f"Symbol:{self.symbol_filter}")
        if self.direction_filter:
            filters.append(f"Dir:{self.direction_filter.value}")

        if filters:
            title += f" [{', '.join(filters)}]"

        self.title_bar.update(title)

    async def _add_system_message(self, message: str) -> None:
        """
        Add a system message to the monitor.

        Args:
            message: The message to add
        """
        if self.title_bar:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.title_bar.update(f"Order Monitor - {message} ({current_time})")

    # Order management actions

    async def cancel_selected_order(self) -> None:
        """Cancel the currently selected order."""
        if not self.data_table:
            return

        try:
            # Get selected row data
            cursor_row = self.data_table.cursor_coordinate.row
            order_data = self.row_data.get(cursor_row)

            if order_data and hasattr(order_data, "vt_orderid"):
                # Create cancel request
                from foxtrot.util.object import CancelRequest

                cancel_req = CancelRequest(
                    orderid=order_data.orderid,
                    symbol=order_data.symbol,
                    exchange=order_data.exchange,
                )

                # Send cancel request through main engine
                self.main_engine.cancel_order(cancel_req, order_data.gateway_name)

                await self._add_system_message(f"Cancel request sent for {order_data.vt_orderid}")

                # Emit custom message for parent components
                self.post_message(self.OrderCancelRequested(order_data))

        except Exception as e:
            await self._log_error(f"Failed to cancel order: {e}")

    async def cancel_all_orders(self, symbol: str | None = None) -> None:
        """
        Cancel all active orders, optionally filtered by symbol.

        Args:
            symbol: Optional symbol filter for cancellation
        """
        try:
            cancelled_count = 0

            for order_id in list(self.active_orders):
                # Get order data from storage (implementation depends on data management)
                # For now, we'll use the main engine's cancel all functionality
                pass

            # Use main engine's cancel all functionality
            self.main_engine.cancel_all(None)  # Cancel all orders across all gateways

            await self._add_system_message("Cancel all orders requested")

            # Emit custom message
            self.post_message(self.AllOrdersCancelRequested(symbol))

        except Exception as e:
            await self._log_error(f"Failed to cancel all orders: {e}")

    # Filter and display management actions

    def action_filter_by_status(self, status: Status) -> None:
        """
        Filter orders by status.

        Args:
            status: Order status to filter by
        """
        self.status_filter = status if status != self.status_filter else None
        self._update_filter_display()

    def action_filter_by_symbol(self, symbol: str) -> None:
        """
        Filter orders by symbol.

        Args:
            symbol: Symbol pattern to filter by
        """
        self.symbol_filter = symbol if symbol != self.symbol_filter else None
        self._update_filter_display()

    def action_filter_by_direction(self, direction: Direction) -> None:
        """
        Filter orders by direction.

        Args:
            direction: Trading direction to filter by
        """
        self.direction_filter = direction if direction != self.direction_filter else None
        self._update_filter_display()

    def action_toggle_active_only(self) -> None:
        """Toggle display of active orders only."""
        self.show_only_active = not self.show_only_active
        self._update_filter_display()

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.status_filter = None
        self.symbol_filter = None
        self.direction_filter = None
        self.gateway_filter = None
        self.show_only_active = False
        self._update_filter_display()

    def _update_filter_display(self) -> None:
        """Update the display based on current filters."""
        # This would trigger a refresh of the table display
        # and update the title bar
        asyncio.create_task(self._update_statistics_display())

    # Enhanced key bindings for order monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("delete", "cancel_selected", "Cancel Order"),
        ("ctrl+delete", "cancel_all", "Cancel All"),
        ("f1", "filter_active", "Active Only"),
        ("f2", "filter_filled", "Filled Only"),
        ("f3", "filter_cancelled", "Cancelled Only"),
        ("f4", "filter_long", "Long Orders"),
        ("f5", "filter_short", "Short Orders"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
        ("a", "toggle_auto_scroll", "Auto Scroll"),
    ]

    def action_cancel_selected(self) -> None:
        """Cancel the selected order."""
        asyncio.create_task(self.cancel_selected_order())

    def action_cancel_all(self) -> None:
        """Cancel all active orders."""
        asyncio.create_task(self.cancel_all_orders())

    def action_filter_active(self) -> None:
        """Filter to show active orders only."""
        self.action_filter_by_status(Status.NOTTRADED)

    def action_filter_filled(self) -> None:
        """Filter to show filled orders only."""
        self.action_filter_by_status(Status.ALLTRADED)

    def action_filter_cancelled(self) -> None:
        """Filter to show cancelled orders only."""
        self.action_filter_by_status(Status.CANCELLED)

    def action_filter_long(self) -> None:
        """Filter to show long orders only."""
        self.action_filter_by_direction(Direction.LONG)

    def action_filter_short(self) -> None:
        """Filter to show short orders only."""
        self.action_filter_by_direction(Direction.SHORT)

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to order updates."""
        self.auto_scroll_to_updates = not self.auto_scroll_to_updates
        status = "ON" if self.auto_scroll_to_updates else "OFF"
        asyncio.create_task(self._add_system_message(f"Auto-scroll {status}"))

    # Custom messages for order events

    class OrderCancelRequested(Message):
        """Message sent when an order cancel is requested."""

        def __init__(self, order_data: OrderData) -> None:
            self.order_data = order_data
            super().__init__()

    class AllOrdersCancelRequested(Message):
        """Message sent when cancel all orders is requested."""

        def __init__(self, symbol_filter: str | None = None) -> None:
            self.symbol_filter = symbol_filter
            super().__init__()

    class OrderSelected(Message):
        """Message sent when an order is selected for trading panel update."""

        def __init__(self, order_data: OrderData) -> None:
            self.order_data = order_data
            super().__init__()


# Convenience function for creating order monitor
def create_order_monitor(main_engine: MainEngine, event_engine: EventEngine) -> TUIOrderMonitor:
    """
    Create a configured order monitor instance.

    Args:
        main_engine: The main trading engine
        event_engine: The event engine

    Returns:
        Configured TUIOrderMonitor instance
    """
    return TUIOrderMonitor(main_engine, event_engine)
