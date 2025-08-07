"""
Position monitor filters and actions for user interaction management.

This module handles filter operations, user actions, keybindings,
and interactive functionality for the position monitor.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import PositionData
from .position_business_logic import PositionBusinessLogic
from .position_ui_components import PositionUIComponents


class PositionFiltersActions:
    """
    Filters and actions for position monitor user interactions.
    
    This class manages all filter operations, user actions, keybindings,
    and interactive functionality without direct UI dependencies.
    """

    def __init__(
        self,
        business_logic: PositionBusinessLogic,
        ui_components: PositionUIComponents,
    ):
        self.business_logic = business_logic
        self.ui_components = ui_components

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
        self.auto_scroll_to_updates = True

        # Callback for UI updates (set by controller)
        self._update_display_callback: Optional[Callable] = None
        self._add_system_message_callback: Optional[Callable] = None

    def set_callbacks(
        self,
        update_display_callback: Callable,
        add_system_message_callback: Callable,
    ) -> None:
        """
        Set callbacks for UI updates.

        Args:
            update_display_callback: Callback to update display
            add_system_message_callback: Callback to add system messages
        """
        self._update_display_callback = update_display_callback
        self._add_system_message_callback = add_system_message_callback

    def filter_by_symbol(self, symbol: str) -> None:
        """
        Filter positions by symbol.

        Args:
            symbol: Symbol pattern to filter by
        """
        self.symbol_filter = symbol if symbol != self.symbol_filter else None
        self._update_filter_display()

    def filter_by_direction(self, direction: Direction) -> None:
        """
        Filter positions by direction.

        Args:
            direction: Trading direction to filter by
        """
        self.direction_filter = direction if direction != self.direction_filter else None
        self._update_filter_display()

    def filter_by_exchange(self, exchange: Exchange) -> None:
        """
        Filter positions by exchange.

        Args:
            exchange: Exchange to filter by
        """
        self.exchange_filter = exchange if exchange != self.exchange_filter else None
        self._update_filter_display()

    def filter_by_gateway(self, gateway: str) -> None:
        """
        Filter positions by gateway.

        Args:
            gateway: Gateway name to filter by
        """
        self.gateway_filter = gateway if gateway != self.gateway_filter else None
        self._update_filter_display()

    def filter_by_pnl(self, min_pnl: float) -> None:
        """
        Filter positions by minimum P&L.

        Args:
            min_pnl: Minimum P&L threshold
        """
        self.min_pnl_filter = min_pnl if min_pnl != self.min_pnl_filter else None
        self._update_filter_display()

    def filter_by_value(self, min_value: float) -> None:
        """
        Filter positions by minimum value.

        Args:
            min_value: Minimum position value threshold
        """
        self.min_value_filter = min_value if min_value != self.min_value_filter else None
        self._update_filter_display()

    def toggle_active_only(self) -> None:
        """Toggle display of active positions only."""
        self.show_only_active = not self.show_only_active
        self._update_filter_display()

    def toggle_percentage_display(self) -> None:
        """Toggle display of P&L percentages."""
        self.show_percentage = not self.show_percentage
        status = "ON" if self.show_percentage else "OFF"
        if self._add_system_message_callback:
            asyncio.create_task(
                self._add_system_message_callback(f"P&L percentage display {status}")
            )

    def toggle_large_positions(self) -> None:
        """Toggle highlighting of large positions."""
        self.highlight_large_positions = not self.highlight_large_positions
        status = "ON" if self.highlight_large_positions else "OFF"
        if self._add_system_message_callback:
            asyncio.create_task(
                self._add_system_message_callback(f"Large position highlighting {status}")
            )

    def toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to position updates."""
        self.auto_scroll_to_updates = not self.auto_scroll_to_updates
        status = "ON" if self.auto_scroll_to_updates else "OFF"
        if self._add_system_message_callback:
            asyncio.create_task(
                self._add_system_message_callback(f"Auto-scroll {status}")
            )

    def clear_filters(self) -> None:
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
        if self._update_display_callback:
            asyncio.create_task(self._update_display_callback())

    # Action handlers for keybindings

    def action_filter_active(self) -> None:
        """Filter to show active positions only."""
        self.toggle_active_only()

    def action_filter_long(self) -> None:
        """Filter to show long positions only."""
        self.filter_by_direction(Direction.LONG)

    def action_filter_short(self) -> None:
        """Filter to show short positions only."""
        self.filter_by_direction(Direction.SHORT)

    def action_filter_winners(self) -> None:
        """Filter to show winning positions only."""
        self.filter_by_pnl(0.01)  # Minimum profit

    def action_filter_losers(self) -> None:
        """Filter to show losing positions only."""
        self.min_pnl_filter = -999999.0  # Show all losses
        self._update_filter_display()

    def action_show_portfolio_summary(self, row_data: Dict[str, PositionData]) -> None:
        """Show portfolio summary statistics."""
        message = self.ui_components.format_portfolio_summary_message()
        if self._add_system_message_callback:
            asyncio.create_task(self._add_system_message_callback(message))

    def action_show_symbol_exposure(self, symbol: str, row_data: Dict[str, PositionData]) -> None:
        """Show symbol exposure summary."""
        message = self.ui_components.format_symbol_exposure_message(symbol, row_data)
        if self._add_system_message_callback:
            asyncio.create_task(self._add_system_message_callback(message))

    def apply_position_filter(self, position_data: PositionData) -> bool:
        """
        Apply all active filters to position data.

        Args:
            position_data: Position data to filter

        Returns:
            True if position passes all filters
        """
        return self.business_logic.passes_filters(
            position_data,
            self.symbol_filter,
            self.direction_filter,
            self.exchange_filter,
            self.gateway_filter,
            self.min_pnl_filter,
            self.min_value_filter,
            self.show_only_active,
        )

    def get_keybinding_definitions(self) -> List[Tuple[str, str, str]]:
        """
        Get keybinding definitions for the position monitor.

        Returns:
            List of (key, action, description) tuples
        """
        base_bindings = [
            # Base monitor bindings would be inherited
            ("r", "refresh", "Refresh Data"),
            ("s", "save_csv", "Export CSV"),
            ("q", "quit", "Quit Monitor"),
            ("?", "help", "Show Help"),
        ]

        position_specific_bindings = [
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

        return base_bindings + position_specific_bindings

    def get_filter_status(self) -> Dict[str, Any]:
        """
        Get current filter status.

        Returns:
            Dictionary with current filter settings
        """
        return {
            "symbol_filter": self.symbol_filter,
            "direction_filter": self.direction_filter.value if self.direction_filter else None,
            "exchange_filter": self.exchange_filter.value if self.exchange_filter else None,
            "gateway_filter": self.gateway_filter,
            "min_pnl_filter": self.min_pnl_filter,
            "min_value_filter": self.min_value_filter,
            "show_only_active": self.show_only_active,
            "show_percentage": self.show_percentage,
            "highlight_large_positions": self.highlight_large_positions,
            "auto_scroll_to_updates": self.auto_scroll_to_updates,
        }

    def get_filter_summary_for_export(self) -> str:
        """
        Get filter summary for export metadata.

        Returns:
            String describing active filters
        """
        filters = []

        if self.symbol_filter:
            filters.append(f"Symbol:{self.symbol_filter}")
        if self.direction_filter:
            filters.append(f"Direction:{self.direction_filter.value}")
        if self.exchange_filter:
            filters.append(f"Exchange:{self.exchange_filter.value}")
        if self.gateway_filter:
            filters.append(f"Gateway:{self.gateway_filter}")
        if self.min_pnl_filter:
            filters.append(f"MinPnL:{self.min_pnl_filter}")
        if self.min_value_filter:
            filters.append(f"MinValue:{self.min_value_filter}")
        if self.show_only_active:
            filters.append("ACTIVE")

        return ", ".join(filters) if filters else "No Filters"

    def validate_filter_input(self, filter_type: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate filter input values.

        Args:
            filter_type: Type of filter (symbol, direction, pnl, value)
            value: Filter value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if filter_type == "symbol":
            if not isinstance(value, str) or len(value.strip()) == 0:
                return False, "Symbol cannot be empty"

        elif filter_type == "pnl":
            try:
                float(value)
            except (ValueError, TypeError):
                return False, "P&L must be a valid number"

        elif filter_type == "value":
            try:
                val = float(value)
                if val < 0:
                    return False, "Position value must be non-negative"
            except (ValueError, TypeError):
                return False, "Position value must be a valid number"

        elif filter_type == "direction":
            if value not in [Direction.LONG, Direction.SHORT]:
                return False, "Direction must be LONG or SHORT"

        return True, None

    def reset_to_defaults(self) -> None:
        """Reset all filters and display options to defaults."""
        self.symbol_filter = None
        self.direction_filter = None
        self.exchange_filter = None
        self.gateway_filter = None
        self.min_pnl_filter = None
        self.min_value_filter = None
        self.show_only_active = True
        self.show_percentage = True
        self.highlight_large_positions = True
        self.auto_scroll_to_updates = True
        self._update_filter_display()