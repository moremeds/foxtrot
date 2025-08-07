"""
Position monitor controller for orchestrating modular components.

This module provides the main TUIPositionMonitor class that coordinates
all modular components while maintaining the public interface.
"""

import asyncio
from datetime import datetime
from typing import Any

from textual.coordinate import Coordinate
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction
from foxtrot.util.event_type import EVENT_POSITION
from foxtrot.util.object import PositionData

from ...base_monitor import TUIDataMonitor
from .position_business_logic import PositionBusinessLogic
from .position_ui_components import PositionUIComponents
from .position_filters_actions import PositionFiltersActions
from .position_export import PositionExport


class TUIPositionMonitor(TUIDataMonitor):
    """
    TUI Position Monitor for tracking portfolio positions and P&L.

    Features:
        - Real-time position updates with P&L calculations
        - Color coding by profitability and position size
        - Position filtering by symbol, exchange, and direction
        - P&L tracking with unrealized and realized gains
        - Position risk analysis and exposure calculations
        - Portfolio summaries and statistics
        - Export functionality for position analysis
        - Integration with order placement for position management
    """

    # Monitor configuration
    event_type = EVENT_POSITION
    data_key = "vt_positionid"
    sorting = True  # Enable sorting by different columns

    # Column configuration
    headers = {
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
        "direction": {
            "display": "Direction",
            "cell": "direction",
            "update": True,
            "width": 8,
            "precision": 0,
        },
        "volume": {
            "display": "Volume",
            "cell": "volume",
            "update": True,
            "width": 10,
            "precision": 0,
        },
        "frozen": {
            "display": "Frozen",
            "cell": "volume",
            "update": True,
            "width": 8,
            "precision": 0,
        },
        "price": {
            "display": "Avg Price",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4,
        },
        "pnl": {"display": "P&L", "cell": "pnl", "update": True, "width": 12, "precision": 2},
        "percent": {
            "display": "P&L %",
            "cell": "percentage",
            "update": True,
            "width": 8,
            "precision": 2,
        },
        "datetime": {
            "display": "Updated",
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
        Initialize the position monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Position Monitor", **kwargs)

        # Initialize modular components
        self.business_logic = PositionBusinessLogic()
        self.ui_components = PositionUIComponents(self.business_logic)
        self.filters_actions = PositionFiltersActions(self.business_logic, self.ui_components)
        self.export_handler = PositionExport(self.business_logic, self.ui_components)

        # Set up component callbacks
        self.filters_actions.set_callbacks(
            self._update_statistics_display,
            self._add_system_message,
        )
        self.export_handler.set_callbacks(
            self._add_system_message,
            self._log_error,
        )

    def compose(self):
        """Create the position monitor layout with portfolio summary."""
        yield from super().compose()

    async def on_mount(self) -> None:
        """Called when the position monitor is mounted."""
        await super().on_mount()
        # Initialize with welcome message
        await self._add_system_message("Position monitor ready for portfolio tracking")

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with position-specific formatting.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        return self.ui_components.format_cell_content(content, config)

    async def _apply_row_styling(self, row_index: int, data: PositionData) -> None:
        """
        Apply color styling to position data based on P&L and direction.

        Args:
            row_index: The row index to style
            data: The PositionData object
        """
        if not self.data_table:
            return

        try:
            self.ui_components.apply_row_styling(
                row_index,
                data,
                self.data_table,
                self.filters_actions.highlight_large_positions,
            )
        except Exception as e:
            await self._log_error(f"Error applying row styling: {e}")

    async def _process_event(self, event) -> None:
        """
        Process position events with filtering and statistics updates.

        Args:
            event: Position event containing PositionData
        """
        try:
            position_data: PositionData = event.data

            # Apply filters
            if not self.filters_actions.apply_position_filter(position_data):
                return

            # Update position tracking
            self.business_logic.update_position_tracking(position_data)

            # Process the position data
            await super()._process_event(event)

            # Update statistics and portfolio metrics
            self.business_logic.update_position_statistics(position_data)
            self.business_logic.update_portfolio_metrics(self.row_data)

            # Handle auto-scroll if enabled
            self.ui_components.handle_auto_scroll(
                self.data_table, self.filters_actions.auto_scroll_to_updates
            )

            # Emit position processed message
            self.post_message(self.PositionProcessed(position_data))

            # Check for risk warnings
            await self._check_risk_warnings(position_data)

        except Exception as e:
            await self._log_error(f"Error processing position event: {e}")

    async def _check_risk_warnings(self, position_data: PositionData) -> None:
        """
        Check for risk warnings and alert if necessary.

        Args:
            position_data: Position data to check
        """
        warnings = self.business_logic.check_risk_warnings(position_data)
        
        # Emit warnings
        for warning in warnings:
            await self._add_system_message(f"⚠️ {warning}")
            self.post_message(self.PositionWarning(position_data, warning))

    async def _update_statistics_display(self) -> None:
        """Update the title bar with current statistics."""
        if not self.title_bar:
            return

        title = self.ui_components.get_statistics_title(
            self.filters_actions.symbol_filter,
            self.filters_actions.direction_filter,
            self.filters_actions.show_only_active,
        )
        self.title_bar.update(title)

    async def _add_system_message(self, message: str) -> None:
        """
        Add a system message to the monitor.

        Args:
            message: The message to add
        """
        if self.title_bar:
            datetime.now().strftime("%H:%M:%S")
            await self._update_statistics_display()

    # Enhanced key bindings for position monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("f1", "filter_active", "Active Only"),
        ("f2", "filter_long", "Long Positions"),
        ("f3", "filter_short", "Short Positions"),
        ("f4", "filter_winners", "Winning Positions"),
        ("f5", "filter_losers", "Losing Positions"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
        ("a", "toggle_auto_scroll", "Auto Scroll"),
        ("p", "toggle_percentage", "Show P&L %"),
        ("l", "toggle_large", "Large Positions"),
        ("s", "show_portfolio_summary", "Portfolio Summary"),
    ]

    # Action method delegations to filters_actions
    def action_filter_active(self) -> None:
        """Filter to show active positions only."""
        self.filters_actions.action_filter_active()

    def action_filter_long(self) -> None:
        """Filter to show long positions only."""
        self.filters_actions.action_filter_long()

    def action_filter_short(self) -> None:
        """Filter to show short positions only."""
        self.filters_actions.action_filter_short()

    def action_filter_winners(self) -> None:
        """Filter to show winning positions only."""
        self.filters_actions.action_filter_winners()

    def action_filter_losers(self) -> None:
        """Filter to show losing positions only."""
        self.filters_actions.action_filter_losers()

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.filters_actions.clear_filters()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to position updates."""
        self.filters_actions.toggle_auto_scroll()

    def action_toggle_percentage(self) -> None:
        """Toggle P&L percentage display."""
        self.filters_actions.toggle_percentage_display()

    def action_toggle_large(self) -> None:
        """Toggle large position highlighting."""
        self.filters_actions.toggle_large_positions()

    def action_show_portfolio_summary(self) -> None:
        """Show portfolio summary statistics."""
        self.filters_actions.action_show_portfolio_summary(self.row_data)

    async def action_save_csv(self) -> None:
        """Save position data to CSV with portfolio analysis."""
        await self.export_handler.save_csv(
            self.data_table,
            self.headers,
            self.filters_actions.symbol_filter,
        )

    # Public API methods that delegate to business logic
    def get_portfolio_summary(self) -> dict[str, Any]:
        """Get comprehensive portfolio summary."""
        return self.business_logic.get_portfolio_summary()

    def get_symbol_exposure(self, symbol: str) -> dict[str, Any]:
        """Get exposure details for a specific symbol."""
        return self.business_logic.get_symbol_exposure(symbol, self.row_data)

    # Custom messages for position events
    class PositionProcessed(Message):
        """Message sent when a position is processed."""

        def __init__(self, position_data: PositionData) -> None:
            self.position_data = position_data
            super().__init__()

    class PositionWarning(Message):
        """Message sent when a position warning is triggered."""

        def __init__(self, position_data: PositionData, warning: str) -> None:
            self.position_data = position_data
            self.warning = warning
            super().__init__()

    class PositionSelected(Message):
        """Message sent when a position is selected for trading panel update."""

        def __init__(self, position_data: PositionData) -> None:
            self.position_data = position_data
            super().__init__()


# Convenience function for creating position monitor
def create_position_monitor(
    main_engine: MainEngine, event_engine: EventEngine
) -> TUIPositionMonitor:
    """
    Create a configured position monitor instance.

    Args:
        main_engine: The main trading engine
        event_engine: The event engine

    Returns:
        Configured TUIPositionMonitor instance
    """
    return TUIPositionMonitor(main_engine, event_engine)