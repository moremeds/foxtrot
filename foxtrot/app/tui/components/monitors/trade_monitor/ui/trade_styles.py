"""
Trade styling and color management for display.

Handles row and cell styling, color coding, and visual themes.
"""

from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction
from foxtrot.util.object import TradeData
from foxtrot.app.tui.utils.colors import get_color_manager

if TYPE_CHECKING:
    from ...trade_monitor import TUITradeMonitor


class TradeStyles:
    """Handles styling and color coding for trade display."""
    
    def __init__(self, monitor_ref=None):
        """
        Initialize with optional monitor reference.
        
        Args:
            monitor_ref: Weak reference to the monitor (optional)
        """
        self._monitor_ref = monitor_ref
        self.color_manager = get_color_manager()
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        if self._monitor_ref is None:
            raise RuntimeError("No monitor reference set")
        
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    def get_row_style(self, trade: TradeData) -> str:
        """
        Get the appropriate style for a trade row.
        
        Args:
            trade: Trade data
            
        Returns:
            Style identifier for the row
        """
        # Check if we have monitor reference for large trade detection
        if self._monitor_ref is not None:
            monitor = self.monitor
            if (monitor.highlight_large_trades and 
                hasattr(monitor, 'trade_statistics') and
                monitor.trade_statistics and
                monitor.trade_statistics.is_large_trade(trade)):
                return "large_trade"
        
        # Color by direction
        if trade.direction == Direction.LONG:
            return "long_trade"
        elif trade.direction == Direction.SHORT:
            return "short_trade"
        
        return "default"
    
    def get_cell_style(self, content: any, column: str, trade: TradeData) -> str:
        """
        Get style for a specific cell.
        
        Args:
            content: Cell content
            column: Column identifier
            trade: Trade data for context
            
        Returns:
            Style identifier for the cell
        """
        # Direction-specific styling
        if column == "direction":
            if isinstance(content, Direction):
                return "long" if content == Direction.LONG else "short"
        
        # Price styling based on large trades
        if column == "price" and self._monitor_ref is not None:
            monitor = self.monitor
            if (monitor.highlight_large_trades and 
                hasattr(monitor, 'trade_statistics') and
                monitor.trade_statistics and
                monitor.trade_statistics.is_large_trade(trade)):
                return "highlight_price"
        
        # Volume styling
        if column == "volume":
            if isinstance(content, (int, float)) and content > 1000:
                return "large_volume"
        
        return "default"
    
    @staticmethod
    def get_direction_color(direction: Direction) -> str:
        """
        Get color identifier for direction.
        
        Args:
            direction: Trade direction
            
        Returns:
            Color identifier
        """
        return "green" if direction == Direction.LONG else "red"
    
    @staticmethod
    def get_size_color(volume: float) -> str:
        """
        Get color based on trade size.
        
        Args:
            volume: Trade volume
            
        Returns:
            Color identifier
        """
        if volume >= 10000:
            return "purple"  # Extra large
        elif volume >= 5000:
            return "orange"  # Large
        elif volume >= 1000:
            return "yellow"  # Medium
        else:
            return "default"  # Small
    
    @staticmethod
    def get_exchange_color(exchange: str) -> str:
        """
        Get color based on exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Color identifier
        """
        exchange_colors = {
            "NASDAQ": "blue",
            "NYSE": "cyan", 
            "BINANCE": "yellow",
            "SMART": "green",
        }
        return exchange_colors.get(exchange.upper(), "default")
    
    def get_style_classes(self) -> dict[str, str]:
        """
        Get CSS/styling classes for different trade elements.
        
        Returns:
            Dictionary mapping style names to CSS classes
        """
        return {
            "long_trade": "trade-long",
            "short_trade": "trade-short", 
            "large_trade": "trade-large",
            "highlight_price": "price-highlight",
            "large_volume": "volume-large",
            "default": "trade-default",
        }