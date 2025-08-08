"""
Position monitor UI components for formatting and visual presentation.

This module handles all visual formatting, styling, color management,
and display presentation logic without business logic dependencies.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from textual.coordinate import Coordinate

from foxtrot.util.object import PositionData
from foxtrot.util.constants import Direction
from foxtrot.app.tui.utils.colors import get_color_manager
from foxtrot.app.tui.utils.formatters import TUIFormatter
from .position_business_logic import PositionBusinessLogic


class PositionUIComponents:
    """
    UI components for position monitor visual presentation.
    
    This class handles all formatting, styling, color management, and
    display presentation logic for the position monitor interface.
    """

    def __init__(self, business_logic: PositionBusinessLogic):
        self.business_logic = business_logic
        self.color_manager = get_color_manager()

    def format_cell_content(self, content: Any, config: Dict[str, Any]) -> str:
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

        return "-"

    def apply_row_styling(
        self,
        row_index: int,
        data: PositionData,
        data_table,
        highlight_large_positions: bool = True,
    ) -> None:
        """
        Apply color styling to position data based on P&L and direction.

        Args:
            row_index: The row index to style
            data: The PositionData object
            data_table: The data table widget
            highlight_large_positions: Whether to highlight large positions
        """
        if not data_table:
            return

        try:
            # P&L-based color coding
            self.color_manager.get_pnl_color(data.pnl)

            # Direction-based color coding
            self.color_manager.get_direction_color(data.direction)

            # Highlight large positions if enabled
            if highlight_large_positions:
                position_value = self.business_logic.calculate_position_value(data)
                if position_value >= self.business_logic.large_position_threshold:
                    # Apply special highlighting for large positions
                    pass

            # Risk-based highlighting
            if data.pnl < self.business_logic.pnl_warning_threshold:
                # Highlight positions with significant losses
                pass

            # Apply styling based on position properties
            # This would integrate with Textual's styling system in a real implementation

        except Exception:
            # Error in styling should not break the display
            pass

    def get_statistics_title(
        self,
        symbol_filter: Optional[str] = None,
        direction_filter: Optional[Direction] = None,
        show_only_active: bool = True,
    ) -> str:
        """
        Generate title bar text with current statistics.

        Args:
            symbol_filter: Active symbol filter
            direction_filter: Active direction filter
            show_only_active: Whether showing only active positions

        Returns:
            Formatted title string
        """
        stats = self.business_logic.position_statistics
        active_count = len(self.business_logic.active_positions)

        title = f"Position Monitor - Active: {active_count} | P&L: {TUIFormatter.format_pnl(stats['total_pnl'])}"

        # Add filter information if active
        filters = []
        if symbol_filter:
            filters.append(f"Symbol:{symbol_filter}")
        if direction_filter:
            filters.append(f"Dir:{direction_filter.value}")
        if show_only_active:
            filters.append("ACTIVE")

        if filters:
            title += f" [{', '.join(filters)}]"

        return title

    def format_portfolio_summary_message(self) -> str:
        """
        Format portfolio summary for display messages.

        Returns:
            Formatted portfolio summary string
        """
        summary = self.business_logic.get_portfolio_summary()
        return f"Portfolio: {summary['active_positions']} positions, P&L: {TUIFormatter.format_pnl(summary['total_pnl'])}, Win Rate: {summary['win_rate']:.1f}%"

    def format_symbol_exposure_message(self, symbol: str, row_data: Dict[str, PositionData]) -> str:
        """
        Format symbol exposure for display messages.

        Args:
            symbol: Symbol to analyze
            row_data: Dictionary of position data

        Returns:
            Formatted symbol exposure string
        """
        exposure = self.business_logic.get_symbol_exposure(symbol, row_data)
        if exposure["positions"] == 0:
            return f"No positions found for {symbol}"
        
        return f"{symbol}: {exposure['positions']} pos, Value: {TUIFormatter.format_currency(exposure['total_value'])}, P&L: {TUIFormatter.format_pnl(exposure['total_pnl'])}"

    def get_display_toggles_status(
        self,
        show_percentage: bool,
        highlight_large_positions: bool,
        auto_scroll_to_updates: bool,
    ) -> Dict[str, str]:
        """
        Get status of display toggle options.

        Args:
            show_percentage: Whether percentage changes are shown
            highlight_large_positions: Whether large positions are highlighted
            auto_scroll_to_updates: Whether auto-scroll is enabled

        Returns:
            Dictionary with toggle statuses
        """
        return {
            "percentage_display": "ON" if show_percentage else "OFF",
            "large_positions": "ON" if highlight_large_positions else "OFF",
            "auto_scroll": "ON" if auto_scroll_to_updates else "OFF",
        }

    def handle_auto_scroll(self, data_table, auto_scroll_to_updates: bool) -> None:
        """
        Handle auto-scroll behavior for position updates.

        Args:
            data_table: The data table widget
            auto_scroll_to_updates: Whether auto-scroll is enabled
        """
        if auto_scroll_to_updates and data_table:
            data_table.cursor_coordinate = Coordinate(0, 0)

    def get_export_headers(self, base_headers: Dict[str, Dict[str, Any]]) -> list[str]:
        """
        Get headers for CSV export including portfolio analysis context.

        Args:
            base_headers: Base column headers configuration

        Returns:
            List of export headers
        """
        headers = [config["display"] for config in base_headers.values()]
        headers.extend([
            "Position Value",
            "Risk Level",
            "Export Date",
            "Filter Applied",
            "Total Positions",
            "Portfolio P&L",
            "Win Rate",
        ])
        return headers

    def format_export_metadata(
        self,
        symbol_filter: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Format metadata for export operations.

        Args:
            symbol_filter: Active symbol filter

        Returns:
            Dictionary with formatted metadata
        """
        export_time = datetime.now().isoformat()
        filter_info = f"Symbol:{symbol_filter or 'All'}"
        summary = self.business_logic.get_portfolio_summary()

        return {
            "export_time": export_time,
            "filter_info": filter_info,
            "total_positions": str(summary["active_positions"]),
            "portfolio_pnl": TUIFormatter.format_pnl(summary["total_pnl"]),
            "win_rate": f"{summary['win_rate']:.1f}%",
            "risk_level": "MEDIUM",  # Would be calculated based on portfolio risk metrics
        }

    def get_warning_display_style(self, warning_type: str) -> Dict[str, Any]:
        """
        Get display style for different warning types.

        Args:
            warning_type: Type of warning (position, pnl, risk)

        Returns:
            Dictionary with style properties
        """
        styles = {
            "position": {"color": "yellow", "prefix": "⚠️"},
            "pnl": {"color": "red", "prefix": "📉"},
            "risk": {"color": "red", "prefix": "🚨"},
            "default": {"color": "white", "prefix": "ℹ️"},
        }
        return styles.get(warning_type, styles["default"])

    def format_risk_level_display(self, position_data: PositionData) -> str:
        """
        Format risk level for display.

        Args:
            position_data: Position data

        Returns:
            Formatted risk level string
        """
        risk_level = self.business_logic.get_risk_level(position_data)
        position_value = self.business_logic.calculate_position_value(position_data)
        return f"{risk_level} ({TUIFormatter.format_currency(position_value)})"