"""
Trade filtering and action handling for the trade monitor.

Contains all filtering logic, action handlers, and key binding implementations.
"""

import asyncio
from datetime import date
from typing import Any, TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import TradeData

if TYPE_CHECKING:
    from ..trade_monitor import TUITradeMonitor


class TradeFiltersActions:
    """Handles trade filtering and action processing."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    def initialize_filters(self) -> None:
        """Initialize filter state."""
        monitor = self.monitor
        monitor.symbol_filter = None
        monitor.direction_filter = None
        monitor.exchange_filter = None
        monitor.date_filter = None
        monitor.gateway_filter = None
        monitor.show_session_only = False
        monitor.highlight_large_trades = True
        monitor.large_trade_threshold = 10000.0
        monitor.auto_scroll_to_new_trades = True
    
    # Filter management methods
    
    def filter_by_symbol(self, symbol: str) -> None:
        """
        Filter trades by symbol.
        
        Args:
            symbol: Symbol pattern to filter by
        """
        monitor = self.monitor
        monitor.symbol_filter = symbol if symbol != monitor.symbol_filter else None
        self._update_filter_display()
    
    def filter_by_direction(self, direction: Direction) -> None:
        """
        Filter trades by direction.
        
        Args:
            direction: Trading direction to filter by
        """
        monitor = self.monitor
        monitor.direction_filter = direction if direction != monitor.direction_filter else None
        self._update_filter_display()
    
    def filter_by_exchange(self, exchange: Exchange) -> None:
        """
        Filter trades by exchange.
        
        Args:
            exchange: Exchange to filter by
        """
        monitor = self.monitor
        monitor.exchange_filter = exchange if exchange != monitor.exchange_filter else None
        self._update_filter_display()
    
    def filter_by_date(self, target_date: date) -> None:
        """
        Filter trades by date.
        
        Args:
            target_date: Date to filter by
        """
        monitor = self.monitor
        monitor.date_filter = target_date if target_date != monitor.date_filter else None
        self._update_filter_display()
    
    def toggle_session_only(self) -> None:
        """Toggle display of current session trades only."""
        monitor = self.monitor
        monitor.show_session_only = not monitor.show_session_only
        self._update_filter_display()
    
    def toggle_large_trades(self) -> None:
        """Toggle highlighting of large trades."""
        monitor = self.monitor
        monitor.highlight_large_trades = not monitor.highlight_large_trades
        asyncio.create_task(
            monitor._add_system_message(
                f"Large trade highlighting {'ON' if monitor.highlight_large_trades else 'OFF'}"
            )
        )
    
    def clear_all_filters(self) -> None:
        """Clear all active filters."""
        monitor = self.monitor
        monitor.symbol_filter = None
        monitor.direction_filter = None
        monitor.exchange_filter = None
        monitor.date_filter = None
        monitor.gateway_filter = None
        monitor.show_session_only = False
        self._update_filter_display()
    
    def toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to new trades."""
        monitor = self.monitor
        monitor.auto_scroll_to_new_trades = not monitor.auto_scroll_to_new_trades
        status = "ON" if monitor.auto_scroll_to_new_trades else "OFF"
        asyncio.create_task(monitor._add_system_message(f"Auto-scroll {status}"))
    
    # Action handlers for key bindings
    
    def handle_filter_session(self) -> None:
        """Handle session filter action."""
        self.toggle_session_only()
    
    def handle_filter_long(self) -> None:
        """Handle long trades filter action."""
        self.filter_by_direction(Direction.LONG)
    
    def handle_filter_short(self) -> None:
        """Handle short trades filter action."""
        self.filter_by_direction(Direction.SHORT)
    
    def handle_toggle_large(self) -> None:
        """Handle large trade highlighting toggle."""
        self.toggle_large_trades()
    
    def handle_toggle_auto_scroll(self) -> None:
        """Handle auto-scroll toggle."""
        self.toggle_auto_scroll()
    
    def handle_clear_filters(self) -> None:
        """Handle clear all filters action."""
        self.clear_all_filters()
    
    def _update_filter_display(self) -> None:
        """Update the display based on current filters."""
        monitor = self.monitor
        asyncio.create_task(monitor.trade_statistics.update_statistics_display())
    
    def should_show_trade(self, trade: TradeData) -> bool:
        """
        Check if a trade should be displayed based on current filters.
        
        Args:
            trade: Trade data to check
            
        Returns:
            True if trade should be displayed
        """
        monitor = self.monitor
        
        # Symbol filter
        if monitor.symbol_filter and monitor.symbol_filter not in trade.symbol:
            return False
        
        # Direction filter
        if monitor.direction_filter and trade.direction != monitor.direction_filter:
            return False
        
        # Exchange filter
        if monitor.exchange_filter and trade.exchange != monitor.exchange_filter:
            return False
        
        # Date filter
        if monitor.date_filter and trade.datetime.date() != monitor.date_filter:
            return False
        
        # Gateway filter
        if monitor.gateway_filter and trade.gateway_name != monitor.gateway_filter:
            return False
        
        # Session only filter
        if monitor.show_session_only:
            # Check if trade is from current session (implementation depends on session definition)
            # This is a placeholder - actual session logic would be implemented
            pass
        
        return True