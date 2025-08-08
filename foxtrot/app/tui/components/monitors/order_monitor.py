"""
Order Monitor for TUI

Simplified facade that coordinates specialized order monitor functionality
through modular components. Each aspect is handled by dedicated components.
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

from foxtrot.app.tui.utils.colors import get_color_manager
from foxtrot.app.tui.utils.formatters import TUIFormatter
from ..base_monitor import TUIDataMonitor

# Import specialized components
from .order_monitor.ui.order_formatters import OrderFormatters
from .order_monitor.filters.order_filters import OrderFilters
from .order_monitor.actions.order_actions import OrderActions
from .statistics import OrderStatistics
from .messages import (
    OrderCancelRequested,
    AllOrdersCancelRequested,
    OrderSelected,
    OrderFilterChanged,
    OrderStatisticsUpdated
)


class TUIOrderMonitor(TUIDataMonitor):
    """
    TUI Order Monitor facade that coordinates order tracking functionality.
    
    Delegates to specialized components while maintaining backward compatibility.
    """

    # Monitor configuration
    event_type = EVENT_ORDER
    data_key = "vt_orderid"
    sorting = True  # Enable sorting by different columns

    # Column configuration
    headers = {
        "orderid": {"display": "Order ID", "cell": "default", "update": False, "width": 12, "precision": 0},
        "reference": {"display": "Reference", "cell": "default", "update": False, "width": 10, "precision": 0},
        "symbol": {"display": "Symbol", "cell": "default", "update": False, "width": 12, "precision": 0},
        "exchange": {"display": "Exchange", "cell": "enum", "update": False, "width": 8, "precision": 0},
        "type": {"display": "Type", "cell": "order_type", "update": False, "width": 6, "precision": 0},
        "direction": {"display": "Direction", "cell": "direction", "update": False, "width": 8, "precision": 0},
        "offset": {"display": "Offset", "cell": "enum", "update": False, "width": 6, "precision": 0},
        "price": {"display": "Price", "cell": "float", "update": False, "width": 10, "precision": 4},
        "volume": {"display": "Volume", "cell": "volume", "update": True, "width": 10, "precision": 0},
        "traded": {"display": "Traded", "cell": "volume", "update": True, "width": 10, "precision": 0},
        "status": {"display": "Status", "cell": "status", "update": True, "width": 10, "precision": 0},
        "datetime": {"display": "Time", "cell": "datetime", "update": True, "width": 12, "precision": 0},
        "gateway_name": {"display": "Gateway", "cell": "default", "update": False, "width": 10, "precision": 0},
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
        """Initialize the order monitor facade."""
        super().__init__(main_engine, event_engine, monitor_name="Order Monitor", **kwargs)

        # Color manager for styling
        self.color_manager = get_color_manager()

        # Display options
        self.highlight_recent_updates = True
        self.auto_scroll_to_updates = True

        # Initialize specialized components
        self._init_components()

    def _init_components(self) -> None:
        """Initialize all specialized components."""
        # UI formatting component
        self.order_formatters = OrderFormatters(self.color_manager)
        
        # Filtering component
        self.order_filters = OrderFilters()
        
        # Statistics tracking component
        self.order_statistics = OrderStatistics()
        
        # Actions handler component
        self.order_actions = OrderActions(self)

    def compose(self):
        """Create the order monitor layout."""
        yield from super().compose()

    async def on_mount(self) -> None:
        """Called when the order monitor is mounted."""
        await super().on_mount()
        await self._add_system_message("Order monitor ready for tracking orders")

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """Format cell content using specialized formatter."""
        return self.order_formatters.format_cell_content(content, config)

    async def _apply_row_styling(self, row_index: int, data: OrderData) -> None:
        """Apply row styling based on order status and direction."""
        try:
            style_class = self.order_formatters.get_row_style_class(data)
            
            # Apply highlighting for recent updates if enabled
            if self.highlight_recent_updates:
                # Check if this is a recent update (within last 5 seconds)
                now = datetime.now()
                if hasattr(data.datetime, 'timestamp'):
                    time_diff = now.timestamp() - data.datetime.timestamp()
                    if time_diff < 5.0:  # 5 seconds
                        style_class += " recent-update"
            
            # Apply styling to the row (implementation depends on UI framework)
            # This would be handled by the underlying TUIDataMonitor
            
        except Exception as e:
            # Log error but don't break the display
            pass

    async def _process_event(self, event) -> None:
        """Process order events with filtering and statistics."""
        await super()._process_event(event)
        
        if hasattr(event, 'data') and isinstance(event.data, OrderData):
            order_data = event.data
            
            # Update statistics
            self.order_statistics.update_order_statistics(order_data)
            
            # Auto-scroll to new updates if enabled
            if self.auto_scroll_to_updates and order_data.vt_orderid not in self.table_data:
                # Scroll to the new order (implementation depends on UI framework)
                pass

    def _passes_filters(self, order_data: OrderData) -> bool:
        """Check if order passes current filters using filter component."""
        return self.order_filters.passes_filters(order_data)

    async def _update_statistics_display(self) -> None:
        """Update statistics display."""
        stats = self.order_statistics.get_statistics()
        summary = self.order_statistics.get_statistics_summary()
        await self._add_system_message(f"Stats: {summary}")
        
        # Post statistics update message
        await self.post_message(OrderStatisticsUpdated(stats))

    async def _add_system_message(self, message: str) -> None:
        """Add system message to the monitor."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        # Implementation depends on the base monitor class
        # This would typically update a status area or log

    # Delegate action methods to the actions component
    async def cancel_selected_order(self) -> None:
        """Cancel the currently selected order."""
        await self.order_actions.cancel_selected_order()

    async def cancel_all_orders(self, symbol: str | None = None) -> None:
        """Cancel all orders."""
        await self.order_actions.cancel_all_orders(symbol)

    # Filter action methods
    def action_filter_by_status(self, status: Status) -> None:
        """Filter by order status."""
        self.order_actions.filter_by_status(status)

    def action_filter_by_symbol(self, symbol: str) -> None:
        """Filter by symbol."""
        self.order_actions.filter_by_symbol(symbol)

    def action_filter_by_direction(self, direction: Direction) -> None:
        """Filter by direction."""
        self.order_actions.filter_by_direction(direction)

    def action_toggle_active_only(self) -> None:
        """Toggle active orders only."""
        self.order_actions.toggle_active_only()

    def action_clear_filters(self) -> None:
        """Clear all filters."""
        self.order_actions.clear_filters()

    def _update_filter_display(self) -> None:
        """Update filter display."""
        asyncio.create_task(self.order_actions._update_filter_display())

    # Quick action methods
    def action_cancel_selected(self) -> None:
        """Cancel selected order action."""
        asyncio.create_task(self.cancel_selected_order())

    def action_cancel_all(self) -> None:
        """Cancel all orders action."""
        asyncio.create_task(self.cancel_all_orders())

    def action_filter_active(self) -> None:
        """Filter active orders action."""
        self.order_actions.filter_active()

    def action_filter_filled(self) -> None:
        """Filter filled orders action."""
        self.order_actions.filter_filled()

    def action_filter_cancelled(self) -> None:
        """Filter cancelled orders action."""
        self.order_actions.filter_cancelled()

    def action_filter_long(self) -> None:
        """Filter long orders action."""
        self.order_actions.filter_long()

    def action_filter_short(self) -> None:
        """Filter short orders action."""
        self.order_actions.filter_short()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll action."""
        self.order_actions.toggle_auto_scroll()

    # Export message classes for external use
    OrderCancelRequested = OrderCancelRequested
    AllOrdersCancelRequested = AllOrdersCancelRequested
    OrderSelected = OrderSelected


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