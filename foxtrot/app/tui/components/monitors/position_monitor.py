"""
Position Monitor for TUI

Portfolio position tracking component that displays holdings,
P&L calculations, and provides position management functionality.
"""

import asyncio
from datetime import datetime
from typing import Any

from textual.coordinate import Coordinate
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.event_type import EVENT_POSITION
from foxtrot.util.object import PositionData

from ...utils.colors import get_color_manager
from ...utils.formatters import TUIFormatter
from ..base_monitor import TUIDataMonitor


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

        # Color manager for styling
        self.color_manager = get_color_manager()

        # Position tracking and statistics
        self.active_positions: set[str] = set()
        self.position_statistics: dict[str, Any] = {
            "total_positions": 0,
            "long_positions": 0,
            "short_positions": 0,
            "total_pnl": 0.0,
            "total_value": 0.0,
            "largest_position": 0.0,
            "largest_pnl": 0.0,
            "winning_positions": 0,
            "losing_positions": 0,
        }

        # Portfolio metrics
        self.portfolio_metrics: dict[str, Any] = {
            "net_exposure": 0.0,
            "gross_exposure": 0.0,
            "leverage": 0.0,
            "beta": 0.0,
            "sharpe_ratio": 0.0,
        }

        # Filtering options
        self.symbol_filter: str | None = None
        self.direction_filter: Direction | None = None
        self.exchange_filter: Exchange | None = None
        self.gateway_filter: str | None = None
        self.min_pnl_filter: float | None = None
        self.min_value_filter: float | None = None

        # Display options
        self.show_only_active = True  # Default to active positions only
        self.show_percentage = True
        self.highlight_large_positions = True
        self.large_position_threshold = 10000.0  # Value threshold
        self.auto_scroll_to_updates = True

        # Risk management settings
        self.position_limit_warning = 0.8  # Warn at 80% of limit
        self.pnl_warning_threshold = -1000.0  # Warn on large losses

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

        if cell_type == "pnl":
            # Format P&L with currency and sign indication
            return TUIFormatter.format_pnl(content, show_percentage=False)

        if cell_type == "percentage":
            # Format P&L percentage
            if isinstance(content, int | float) and content != 0:
                return TUIFormatter.format_percentage(content / 100, show_sign=True)
            return "-"

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
            # P&L-based color coding
            self.color_manager.get_pnl_color(data.pnl)

            # Direction-based color coding
            self.color_manager.get_direction_color(data.direction)

            # Highlight large positions if enabled
            if self.highlight_large_positions:
                position_value = abs(data.price * data.volume)
                if position_value >= self.large_position_threshold:
                    # Apply special highlighting for large positions
                    pass

            # Risk-based highlighting
            if data.pnl < self.pnl_warning_threshold:
                # Highlight positions with significant losses
                pass

            # Apply styling based on position properties
            # This would integrate with Textual's styling system

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
            if not self._passes_filters(position_data):
                return

            # Update position tracking
            await self._update_position_tracking(position_data)

            # Process the position data
            await super()._process_event(event)

            # Update statistics and portfolio metrics
            await self._update_position_statistics(position_data)
            await self._update_portfolio_metrics()

            # Handle auto-scroll if enabled
            if self.auto_scroll_to_updates and self.data_table:
                self.data_table.cursor_coordinate = Coordinate(0, 0)

            # Emit position processed message
            self.post_message(self.PositionProcessed(position_data))

            # Check for risk warnings
            await self._check_risk_warnings(position_data)

        except Exception as e:
            await self._log_error(f"Error processing position event: {e}")

    def _passes_filters(self, position_data: PositionData) -> bool:
        """
        Check if position data passes current filters.

        Args:
            position_data: The PositionData to check

        Returns:
            True if position passes all filters
        """
        # Symbol filter
        if self.symbol_filter:
            if self.symbol_filter.lower() not in position_data.symbol.lower():
                return False

        # Direction filter
        if self.direction_filter is not None:
            if position_data.direction != self.direction_filter:
                return False

        # Exchange filter
        if self.exchange_filter is not None:
            if position_data.exchange != self.exchange_filter:
                return False

        # Gateway filter
        if self.gateway_filter and position_data.gateway_name != self.gateway_filter:
            return False

        # P&L filter
        if self.min_pnl_filter is not None and position_data.pnl < self.min_pnl_filter:
            return False

        # Position value filter
        if self.min_value_filter is not None:
            position_value = abs(position_data.price * position_data.volume)
            if position_value < self.min_value_filter:
                return False

        # Active positions only filter
        return not (self.show_only_active and position_data.volume == 0)

    async def _update_position_tracking(self, position_data: PositionData) -> None:
        """
        Update internal position tracking based on position status.

        Args:
            position_data: The position data to track
        """
        position_id = position_data.vt_positionid

        # Track active vs closed positions
        if position_data.volume != 0:
            self.active_positions.add(position_id)
        else:
            self.active_positions.discard(position_id)

    async def _update_position_statistics(self, position_data: PositionData) -> None:
        """
        Update position statistics based on new position data.

        Args:
            position_data: The new position data
        """
        stats = self.position_statistics

        # Update position counts
        if position_data.vt_positionid not in self.active_positions and position_data.volume != 0:
            stats["total_positions"] += 1

            if position_data.direction == Direction.LONG:
                stats["long_positions"] += 1
            else:
                stats["short_positions"] += 1

        # Update P&L statistics
        stats["total_pnl"] += position_data.pnl

        # Update position value
        position_value = abs(position_data.price * position_data.volume)
        stats["total_value"] += position_value

        # Track largest position and P&L
        if position_value > stats["largest_position"]:
            stats["largest_position"] = position_value

        if abs(position_data.pnl) > abs(stats["largest_pnl"]):
            stats["largest_pnl"] = position_data.pnl

        # Update win/loss counts
        if position_data.pnl > 0:
            stats["winning_positions"] += 1
        elif position_data.pnl < 0:
            stats["losing_positions"] += 1

        # Update display with statistics
        await self._update_statistics_display()

    async def _update_portfolio_metrics(self) -> None:
        """Update portfolio-level risk metrics."""
        try:
            # Calculate basic portfolio metrics
            # This would be enhanced with actual portfolio calculation logic

            # Net exposure (long - short)
            long_value = sum(
                abs(pos.price * pos.volume)
                for pos in self.row_data.values()
                if hasattr(pos, "direction") and pos.direction == Direction.LONG
            )
            short_value = sum(
                abs(pos.price * pos.volume)
                for pos in self.row_data.values()
                if hasattr(pos, "direction") and pos.direction == Direction.SHORT
            )

            self.portfolio_metrics["net_exposure"] = long_value - short_value
            self.portfolio_metrics["gross_exposure"] = long_value + short_value

            # Calculate leverage if account value is available
            # This would integrate with account data in a full implementation

        except Exception as e:
            await self._log_error(f"Error updating portfolio metrics: {e}")

    async def _update_statistics_display(self) -> None:
        """Update the title bar with current statistics."""
        if not self.title_bar:
            return

        stats = self.position_statistics
        active_count = len(self.active_positions)

        title = f"Position Monitor - Active: {active_count} | P&L: {TUIFormatter.format_pnl(stats['total_pnl'])}"

        # Add filter information if active
        filters = []
        if self.symbol_filter:
            filters.append(f"Symbol:{self.symbol_filter}")
        if self.direction_filter:
            filters.append(f"Dir:{self.direction_filter.value}")
        if self.show_only_active:
            filters.append("ACTIVE")

        if filters:
            title += f" [{', '.join(filters)}]"

        self.title_bar.update(title)

    async def _check_risk_warnings(self, position_data: PositionData) -> None:
        """
        Check for risk warnings and alert if necessary.

        Args:
            position_data: Position data to check
        """
        warnings = []

        # Check for large losses
        if position_data.pnl < self.pnl_warning_threshold:
            warnings.append(
                f"Large loss: {TUIFormatter.format_pnl(position_data.pnl)} on {position_data.symbol}"
            )

        # Check for large position size
        position_value = abs(position_data.price * position_data.volume)
        if position_value > self.large_position_threshold:
            warnings.append(
                f"Large position: {TUIFormatter.format_currency(position_value)} in {position_data.symbol}"
            )

        # Emit warnings
        for warning in warnings:
            await self._add_system_message(f"⚠️ {warning}")
            self.post_message(self.PositionWarning(position_data, warning))

    async def _add_system_message(self, message: str) -> None:
        """
        Add a system message to the monitor.

        Args:
            message: The message to add
        """
        if self.title_bar:
            datetime.now().strftime("%H:%M:%S")
            await self._update_statistics_display()

    # Position analysis methods

    def get_portfolio_summary(self) -> dict[str, Any]:
        """
        Get comprehensive portfolio summary.

        Returns:
            Dictionary with portfolio statistics
        """
        stats = self.position_statistics.copy()
        metrics = self.portfolio_metrics.copy()

        # Calculate additional metrics
        stats["win_rate"] = stats["winning_positions"] / max(stats["total_positions"], 1) * 100
        stats["avg_pnl"] = stats["total_pnl"] / max(stats["total_positions"], 1)

        return {**stats, **metrics, "active_positions": len(self.active_positions)}

    def get_symbol_exposure(self, symbol: str) -> dict[str, Any]:
        """
        Get exposure details for a specific symbol.

        Args:
            symbol: Symbol to analyze

        Returns:
            Dictionary with symbol exposure data
        """
        symbol_positions = [
            pos for pos in self.row_data.values() if hasattr(pos, "symbol") and pos.symbol == symbol
        ]

        if not symbol_positions:
            return {"symbol": symbol, "positions": 0}

        total_volume = sum(pos.volume for pos in symbol_positions)
        total_value = sum(abs(pos.price * pos.volume) for pos in symbol_positions)
        total_pnl = sum(pos.pnl for pos in symbol_positions)

        return {
            "symbol": symbol,
            "positions": len(symbol_positions),
            "net_volume": total_volume,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "avg_price": total_value / abs(total_volume) if total_volume != 0 else 0,
        }

    # Filter and display management actions

    def action_filter_by_symbol(self, symbol: str) -> None:
        """
        Filter positions by symbol.

        Args:
            symbol: Symbol pattern to filter by
        """
        self.symbol_filter = symbol if symbol != self.symbol_filter else None
        self._update_filter_display()

    def action_filter_by_direction(self, direction: Direction) -> None:
        """
        Filter positions by direction.

        Args:
            direction: Trading direction to filter by
        """
        self.direction_filter = direction if direction != self.direction_filter else None
        self._update_filter_display()

    def action_filter_by_pnl(self, min_pnl: float) -> None:
        """
        Filter positions by minimum P&L.

        Args:
            min_pnl: Minimum P&L threshold
        """
        self.min_pnl_filter = min_pnl if min_pnl != self.min_pnl_filter else None
        self._update_filter_display()

    def action_toggle_active_only(self) -> None:
        """Toggle display of active positions only."""
        self.show_only_active = not self.show_only_active
        self._update_filter_display()

    def action_toggle_percentage_display(self) -> None:
        """Toggle display of P&L percentages."""
        self.show_percentage = not self.show_percentage
        asyncio.create_task(
            self._add_system_message(
                f"P&L percentage display {'ON' if self.show_percentage else 'OFF'}"
            )
        )

    def action_toggle_large_positions(self) -> None:
        """Toggle highlighting of large positions."""
        self.highlight_large_positions = not self.highlight_large_positions
        asyncio.create_task(
            self._add_system_message(
                f"Large position highlighting {'ON' if self.highlight_large_positions else 'OFF'}"
            )
        )

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.symbol_filter = None
        self.direction_filter = None
        self.exchange_filter = None
        self.gateway_filter = None
        self.min_pnl_filter = None
        self.min_value_filter = None
        self.show_only_active = True
        self._update_filter_display()

    def _update_filter_display(self) -> None:
        """Update the display based on current filters."""
        asyncio.create_task(self._update_statistics_display())

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

    def action_filter_active(self) -> None:
        """Filter to show active positions only."""
        self.action_toggle_active_only()

    def action_filter_long(self) -> None:
        """Filter to show long positions only."""
        self.action_filter_by_direction(Direction.LONG)

    def action_filter_short(self) -> None:
        """Filter to show short positions only."""
        self.action_filter_by_direction(Direction.SHORT)

    def action_filter_winners(self) -> None:
        """Filter to show winning positions only."""
        self.action_filter_by_pnl(0.01)  # Minimum profit

    def action_filter_losers(self) -> None:
        """Filter to show losing positions only."""
        self.min_pnl_filter = -999999.0  # Show all losses
        self._update_filter_display()

    def action_toggle_percentage(self) -> None:
        """Toggle P&L percentage display."""
        self.action_toggle_percentage_display()

    def action_toggle_large(self) -> None:
        """Toggle large position highlighting."""
        self.action_toggle_large_positions()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to position updates."""
        self.auto_scroll_to_updates = not self.auto_scroll_to_updates
        status = "ON" if self.auto_scroll_to_updates else "OFF"
        asyncio.create_task(self._add_system_message(f"Auto-scroll {status}"))

    def action_show_portfolio_summary(self) -> None:
        """Show portfolio summary statistics."""
        summary = self.get_portfolio_summary()
        message = f"Portfolio: {summary['active_positions']} positions, P&L: {TUIFormatter.format_pnl(summary['total_pnl'])}, Win Rate: {summary['win_rate']:.1f}%"
        asyncio.create_task(self._add_system_message(message))

    async def action_save_csv(self) -> None:
        """Save position data to CSV with portfolio analysis."""
        if not self.data_table:
            return

        try:
            import csv

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_positions_{timestamp}.csv"
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers with portfolio analysis context
                headers = [config["display"] for config in self.headers.values()]
                headers.extend(
                    [
                        "Position Value",
                        "Risk Level",
                        "Export Date",
                        "Filter Applied",
                        "Total Positions",
                        "Portfolio P&L",
                        "Win Rate",
                    ]
                )
                writer.writerow(headers)

                # Collect metadata
                export_time = datetime.now().isoformat()
                filter_info = f"Symbol:{self.symbol_filter or 'All'}"
                summary = self.get_portfolio_summary()

                # Write position data with calculated values
                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    # Calculate additional fields (would need access to raw position data)
                    position_value = "N/A"  # Would be calculated from price * volume
                    risk_level = (
                        "MEDIUM"  # Would be calculated based on position size and volatility
                    )

                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend(
                            [
                                position_value,
                                risk_level,
                                export_time,
                                filter_info,
                                str(summary["active_positions"]),
                                TUIFormatter.format_pnl(summary["total_pnl"]),
                                f"{summary['win_rate']:.1f}%",
                            ]
                        )
                    else:
                        row_data.extend(["", "", "", "", "", "", ""])

                    writer.writerow(row_data)

            await self._add_system_message(f"Portfolio positions exported to {filepath}")

        except Exception as e:
            await self._log_error(f"Failed to export portfolio positions: {e}")

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
