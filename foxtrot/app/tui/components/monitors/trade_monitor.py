"""
Trade Monitor for TUI - Refactored with modular architecture.

Trade execution history component that displays completed trades,
execution details, and provides trade analysis functionality.

This module uses a facade pattern to coordinate specialized components
for filtering, statistics, export, and UI functionality.
"""

import asyncio
import weakref
from typing import Any

from textual.coordinate import Coordinate
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.event_type import EVENT_TRADE
from foxtrot.util.object import TradeData

from ...utils.colors import get_color_manager
from ...utils.formatters import TUIFormatter
from ..base_monitor import TUIDataMonitor
from .trade_monitor.trade_controller import TradeController


class TUITradeMonitor(TUIDataMonitor):
    """
    TUI Trade Monitor for displaying trade execution history.
    
    This class serves as a facade coordinating modular components:
    - TradeController: Main business logic coordination
    - TradeFiltersActions: Filtering and action handling  
    - TradeStatistics: Statistics calculation and tracking
    - TradeExport: Export functionality
    - TradeUIComponents: UI formatting and display logic

    Features:
        - Real-time trade execution display
        - Color coding by direction and profitability
        - Trade filtering by symbol, direction, and date
        - Trade statistics and analysis
        - Daily/session trade summaries
        - Export functionality for trade analysis
        - Integration with order monitor for execution tracking
    """

    # Monitor configuration
    event_type = EVENT_TRADE
    data_key = ""  # No unique key - all trades are separate entries
    sorting = True  # Enable sorting by different columns

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
        """
        Initialize the trade monitor with modular architecture.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Trade Monitor", **kwargs)

        # Initialize the trade controller which coordinates all components
        self._monitor_ref = weakref.ref(self)
        self.trade_controller = TradeController(
            self._monitor_ref, main_engine, event_engine
        )
        
        # Initialize all modular components through the controller
        self.trade_controller.initialize_components()
        
        # Legacy compatibility attributes (delegated to components)
        # These are set by the controller during initialization
        self.trade_statistics = None
        self.trade_filters_actions = None  
        self.trade_export = None
        self.trade_ui_components = None
        
        # Filter state (managed by filters_actions component)
        self.symbol_filter: str | None = None
        self.direction_filter: Direction | None = None
        self.exchange_filter: Exchange | None = None
        self.date_filter = None
        self.gateway_filter: str | None = None
        self.show_session_only = False
        self.highlight_large_trades = True
        self.large_trade_threshold = 10000.0
        self.auto_scroll_to_new_trades = True

    def compose(self):
        """Create the trade monitor layout with statistics display."""
        yield from super().compose()

    async def on_mount(self) -> None:
        """Called when the trade monitor is mounted."""
        await super().on_mount()
        
        # Initialize monitor through controller
        await self.trade_controller.initialize_monitor()

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with trade-specific formatting.
        Delegates to UI components.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        return self.trade_controller.format_cell_content(content, config)

    def process_event(self, event) -> None:
        """
        Process trade events. Delegates to controller.

        Args:
            event: Event to process
        """
        self.trade_controller.process_trade_event(event)

    # Action methods - delegate to controller/components

    def action_filter_by_symbol(self, symbol: str) -> None:
        """Filter trades by symbol."""
        self.trade_filters_actions.filter_by_symbol(symbol)

    def action_filter_by_direction(self, direction: Direction) -> None:
        """Filter trades by direction."""
        self.trade_filters_actions.filter_by_direction(direction)

    def action_toggle_session_only(self) -> None:
        """Toggle display of current session trades only."""
        self.trade_filters_actions.toggle_session_only()

    def action_toggle_large_trades(self) -> None:
        """Toggle highlighting of large trades."""
        self.trade_filters_actions.toggle_large_trades()

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.trade_filters_actions.clear_all_filters()

    def get_daily_summary(self) -> dict[str, Any]:
        """Get daily trade summary."""
        return self.trade_controller.get_daily_summary()

    # Enhanced key bindings for trade monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("f1", "filter_session", "Session Only"),
        ("f2", "filter_long", "Long Trades"),
        ("f3", "filter_short", "Short Trades"),
        ("f4", "toggle_large", "Large Trades"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
        ("a", "toggle_auto_scroll", "Auto Scroll"),
        ("t", "show_daily_summary", "Daily Summary"),
    ]

    # Key binding action handlers - delegate to controller

    def action_filter_session(self) -> None:
        """Filter to show current session trades only."""
        self.trade_controller.handle_action_filter_session()

    def action_filter_long(self) -> None:
        """Filter to show long trades only."""
        self.trade_controller.handle_action_filter_long()

    def action_filter_short(self) -> None:
        """Filter to show short trades only."""
        self.trade_controller.handle_action_filter_short()

    def action_toggle_large(self) -> None:
        """Toggle large trade highlighting."""
        self.trade_controller.handle_action_toggle_large()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to new trades."""
        self.trade_controller.handle_action_toggle_auto_scroll()

    def action_show_daily_summary(self) -> None:
        """Show daily trade summary."""
        self.trade_controller.handle_action_show_daily_summary()

    async def action_save_csv(self) -> None:
        """Save trade data to CSV with enhanced trade analysis."""
        await self.trade_controller.handle_action_save_csv()

    # Custom messages for trade events

    class TradeProcessed(Message):
        """Message sent when a trade is processed."""

        def __init__(self, trade_data: TradeData) -> None:
            self.trade_data = trade_data
            super().__init__()

    class TradeSelected(Message):
        """Message sent when a trade is selected."""

        def __init__(self, trade_data: TradeData) -> None:
            self.trade_data = trade_data
            super().__init__()

    def cleanup(self) -> None:
        """Cleanup monitor resources."""
        if self.trade_controller:
            self.trade_controller.cleanup()
        super().cleanup()


# Convenience function for creating trade monitor
def create_trade_monitor(main_engine: MainEngine, event_engine: EventEngine) -> TUITradeMonitor:
    """
    Create a configured trade monitor instance.

    Args:
        main_engine: The main trading engine
        event_engine: The event engine

    Returns:
        Configured TUITradeMonitor instance
    """
    return TUITradeMonitor(main_engine, event_engine)