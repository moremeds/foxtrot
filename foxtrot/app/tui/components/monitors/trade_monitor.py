"""
Trade Monitor for TUI

Trade execution history component that displays completed trades,
execution details, and provides trade analysis functionality.
"""

import asyncio
from datetime import date, datetime
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


class TUITradeMonitor(TUIDataMonitor):
    """
    TUI Trade Monitor for displaying trade execution history.

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

    # Column configuration
    headers = {
        "tradeid": {
            "display": "Trade ID",
            "cell": "default",
            "update": False,
            "width": 12,
            "precision": 0,
        },
        "orderid": {
            "display": "Order ID",
            "cell": "default",
            "update": False,
            "width": 12,
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
            "update": False,
            "width": 10,
            "precision": 0,
        },
        "datetime": {
            "display": "Time",
            "cell": "datetime",
            "update": False,
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
        Initialize the trade monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Trade Monitor", **kwargs)

        # Color manager for styling
        self.color_manager = get_color_manager()

        # Trade tracking and statistics
        self.daily_trades: dict[date, list[TradeData]] = {}
        self.trade_statistics: dict[str, Any] = {
            "total_trades": 0,
            "total_volume": 0.0,
            "total_value": 0.0,
            "long_trades": 0,
            "short_trades": 0,
            "avg_price": 0.0,
            "session_pnl": 0.0,
        }

        # Filtering options
        self.symbol_filter: str | None = None
        self.direction_filter: Direction | None = None
        self.exchange_filter: Exchange | None = None
        self.date_filter: date | None = None
        self.gateway_filter: str | None = None

        # Display options
        self.show_session_only = False
        self.highlight_large_trades = True
        self.large_trade_threshold = 10000.0  # Value threshold for highlighting
        self.auto_scroll_to_new_trades = True

    def compose(self):
        """Create the trade monitor layout with statistics display."""
        yield from super().compose()

    async def on_mount(self) -> None:
        """Called when the trade monitor is mounted."""
        await super().on_mount()

        # Initialize with welcome message
        await self._add_system_message("Trade monitor ready for execution data")

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with trade-specific formatting.

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
        return None

    async def _apply_row_styling(self, row_index: int, data: TradeData) -> None:
        """
        Apply color styling to trade data based on direction and size.

        Args:
            row_index: The row index to style
            data: The TradeData object
        """
        if not self.data_table:
            return

        try:
            # Direction-based color coding
            self.color_manager.get_direction_color(data.direction)

            # Highlight large trades if enabled
            if self.highlight_large_trades:
                trade_value = data.price * data.volume
                if trade_value >= self.large_trade_threshold:
                    # Apply special highlighting for large trades
                    pass

            # Apply styling based on trade properties
            # This would integrate with Textual's styling system

        except Exception as e:
            await self._log_error(f"Error applying row styling: {e}")

    async def _process_event(self, event) -> None:
        """
        Process trade events with filtering and statistics updates.

        Args:
            event: Trade event containing TradeData
        """
        try:
            trade_data: TradeData = event.data

            # Apply filters
            if not self._passes_filters(trade_data):
                return

            # Update trade tracking
            await self._update_trade_tracking(trade_data)

            # Process the trade data
            await super()._process_event(event)

            # Update statistics
            await self._update_trade_statistics(trade_data)

            # Handle auto-scroll if enabled
            if self.auto_scroll_to_new_trades and self.data_table:
                self.data_table.cursor_coordinate = Coordinate(0, 0)

            # Emit trade processed message
            self.post_message(self.TradeProcessed(trade_data))

        except Exception as e:
            await self._log_error(f"Error processing trade event: {e}")

    def _passes_filters(self, trade_data: TradeData) -> bool:
        """
        Check if trade data passes current filters.

        Args:
            trade_data: The TradeData to check

        Returns:
            True if trade passes all filters
        """
        # Symbol filter
        if self.symbol_filter:
            if self.symbol_filter.lower() not in trade_data.symbol.lower():
                return False

        # Direction filter
        if self.direction_filter is not None:
            if trade_data.direction != self.direction_filter:
                return False

        # Exchange filter
        if self.exchange_filter is not None and trade_data.exchange != self.exchange_filter:
            return False

        # Date filter
        if self.date_filter is not None and trade_data.datetime.date() != self.date_filter:
            return False

        # Gateway filter
        if self.gateway_filter and trade_data.gateway_name != self.gateway_filter:
            return False

        # Session filter
        if self.show_session_only:
            # Only show trades from current session (today)
            if trade_data.datetime.date() != date.today():
                return False

        return True

    async def _update_trade_tracking(self, trade_data: TradeData) -> None:
        """
        Update internal trade tracking by date.

        Args:
            trade_data: The trade data to track
        """
        trade_date = trade_data.datetime.date()

        if trade_date not in self.daily_trades:
            self.daily_trades[trade_date] = []

        self.daily_trades[trade_date].append(trade_data)

    async def _update_trade_statistics(self, trade_data: TradeData) -> None:
        """
        Update trade statistics based on new trade data.

        Args:
            trade_data: The new trade data
        """
        stats = self.trade_statistics

        # Update counters
        stats["total_trades"] += 1
        stats["total_volume"] += trade_data.volume

        # Calculate trade value
        trade_value = trade_data.price * trade_data.volume
        stats["total_value"] += trade_value

        # Update direction counters
        if trade_data.direction == Direction.LONG:
            stats["long_trades"] += 1
        else:
            stats["short_trades"] += 1

        # Update average price
        if stats["total_volume"] > 0:
            stats["avg_price"] = stats["total_value"] / stats["total_volume"]

        # Update display with statistics
        await self._update_statistics_display()

    async def _update_statistics_display(self) -> None:
        """Update the title bar with current statistics."""
        if not self.title_bar:
            return

        stats = self.trade_statistics

        title = f"Trade Monitor - Trades: {stats['total_trades']} | Volume: {TUIFormatter.format_volume(stats['total_volume'])}"

        if stats["avg_price"] > 0:
            title += f" | Avg: {TUIFormatter.format_price(stats['avg_price'])}"

        # Add filter information if active
        filters = []
        if self.symbol_filter:
            filters.append(f"Symbol:{self.symbol_filter}")
        if self.direction_filter:
            filters.append(f"Dir:{self.direction_filter.value}")
        if self.show_session_only:
            filters.append("TODAY")

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
            datetime.now().strftime("%H:%M:%S")
            await self._update_statistics_display()

    # Trade analysis methods

    def get_daily_summary(self, target_date: date | None = None) -> dict[str, Any]:
        """
        Get summary statistics for a specific date.

        Args:
            target_date: Date to analyze (defaults to today)

        Returns:
            Dictionary with daily statistics
        """
        if target_date is None:
            target_date = date.today()

        daily_trades = self.daily_trades.get(target_date, [])

        if not daily_trades:
            return {"date": target_date, "trades": 0}

        total_volume = sum(trade.volume for trade in daily_trades)
        total_value = sum(trade.price * trade.volume for trade in daily_trades)
        long_trades = sum(1 for trade in daily_trades if trade.direction == Direction.LONG)
        short_trades = len(daily_trades) - long_trades

        return {
            "date": target_date,
            "trades": len(daily_trades),
            "volume": total_volume,
            "value": total_value,
            "avg_price": total_value / total_volume if total_volume > 0 else 0,
            "long_trades": long_trades,
            "short_trades": short_trades,
        }

    def get_symbol_summary(self, symbol: str) -> dict[str, Any]:
        """
        Get summary statistics for a specific symbol.

        Args:
            symbol: Symbol to analyze

        Returns:
            Dictionary with symbol statistics
        """
        symbol_trades = []
        for daily_list in self.daily_trades.values():
            symbol_trades.extend([t for t in daily_list if t.symbol == symbol])

        if not symbol_trades:
            return {"symbol": symbol, "trades": 0}

        total_volume = sum(trade.volume for trade in symbol_trades)
        total_value = sum(trade.price * trade.volume for trade in symbol_trades)

        return {
            "symbol": symbol,
            "trades": len(symbol_trades),
            "volume": total_volume,
            "value": total_value,
            "avg_price": total_value / total_volume if total_volume > 0 else 0,
        }

    # Filter and display management actions

    def action_filter_by_symbol(self, symbol: str) -> None:
        """
        Filter trades by symbol.

        Args:
            symbol: Symbol pattern to filter by
        """
        self.symbol_filter = symbol if symbol != self.symbol_filter else None
        self._update_filter_display()

    def action_filter_by_direction(self, direction: Direction) -> None:
        """
        Filter trades by direction.

        Args:
            direction: Trading direction to filter by
        """
        self.direction_filter = direction if direction != self.direction_filter else None
        self._update_filter_display()

    def action_toggle_session_only(self) -> None:
        """Toggle display of current session trades only."""
        self.show_session_only = not self.show_session_only
        self._update_filter_display()

    def action_toggle_large_trades(self) -> None:
        """Toggle highlighting of large trades."""
        self.highlight_large_trades = not self.highlight_large_trades
        asyncio.create_task(
            self._add_system_message(
                f"Large trade highlighting {'ON' if self.highlight_large_trades else 'OFF'}"
            )
        )

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.symbol_filter = None
        self.direction_filter = None
        self.exchange_filter = None
        self.date_filter = None
        self.gateway_filter = None
        self.show_session_only = False
        self._update_filter_display()

    def _update_filter_display(self) -> None:
        """Update the display based on current filters."""
        asyncio.create_task(self._update_statistics_display())

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

    def action_filter_session(self) -> None:
        """Filter to show current session trades only."""
        self.action_toggle_session_only()

    def action_filter_long(self) -> None:
        """Filter to show long trades only."""
        self.action_filter_by_direction(Direction.LONG)

    def action_filter_short(self) -> None:
        """Filter to show short trades only."""
        self.action_filter_by_direction(Direction.SHORT)

    def action_toggle_large(self) -> None:
        """Toggle large trade highlighting."""
        self.action_toggle_large_trades()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to new trades."""
        self.auto_scroll_to_new_trades = not self.auto_scroll_to_new_trades
        status = "ON" if self.auto_scroll_to_new_trades else "OFF"
        asyncio.create_task(self._add_system_message(f"Auto-scroll {status}"))

    def action_show_daily_summary(self) -> None:
        """Show daily trade summary."""
        summary = self.get_daily_summary()
        message = f"Today: {summary['trades']} trades, Vol: {TUIFormatter.format_volume(summary['volume'])}"
        asyncio.create_task(self._add_system_message(message))

    async def action_save_csv(self) -> None:
        """Save trade data to CSV with enhanced trade analysis."""
        if not self.data_table:
            return

        try:
            import csv

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trade_history_{timestamp}.csv"
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers with trade analysis context
                headers = [config["display"] for config in self.headers.values()]
                headers.extend(
                    [
                        "Trade Value",
                        "Export Date",
                        "Filter Applied",
                        "Total Trades",
                        "Session Volume",
                        "Avg Price",
                    ]
                )
                writer.writerow(headers)

                # Collect metadata
                export_time = datetime.now().isoformat()
                filter_info = f"Symbol:{self.symbol_filter or 'All'}"
                stats = self.trade_statistics

                # Write trade data with calculated values
                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    # Calculate trade value (this would need access to raw trade data)
                    trade_value = "N/A"  # Would be calculated from price * volume

                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend(
                            [
                                trade_value,
                                export_time,
                                filter_info,
                                str(stats["total_trades"]),
                                TUIFormatter.format_volume(stats["total_volume"]),
                                TUIFormatter.format_price(stats["avg_price"]),
                            ]
                        )
                    else:
                        row_data.extend(["", "", "", "", "", ""])

                    writer.writerow(row_data)

            await self._add_system_message(f"Trade history exported to {filepath}")

        except Exception as e:
            await self._log_error(f"Failed to export trade history: {e}")

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
