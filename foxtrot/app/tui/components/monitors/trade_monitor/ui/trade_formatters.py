"""
Trade formatting utilities for display.

Handles cell formatting, data conversion, and display utilities.
"""

from datetime import datetime
from typing import Any, Dict

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import TradeData
from foxtrot.app.tui.utils.formatters import TUIFormatter


class TradeFormatters:
    """Handles trade-specific formatting for display."""
    
    @staticmethod
    def format_cell_content(content: Any, config: Dict[str, Any]) -> str:
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
            if isinstance(content, (Direction, Exchange)):
                return content.value
            return str(content)
        
        return str(content)
    
    @staticmethod
    def format_trade_summary_line(trade: TradeData) -> str:
        """
        Format a single line summary of a trade for status messages.
        
        Args:
            trade: Trade data to format
            
        Returns:
            Formatted summary line
        """
        direction_str = "BUY" if trade.direction == Direction.LONG else "SELL"
        price_str = TUIFormatter.format_price(trade.price, 4)
        volume_str = TUIFormatter.format_volume(trade.volume)
        time_str = TUIFormatter.format_datetime(trade.datetime, "time")
        
        return f"{direction_str} {trade.symbol} {volume_str}@{price_str} [{time_str}]"
    
    @staticmethod
    def format_trade_value(trade: TradeData) -> str:
        """
        Format the total value of a trade.
        
        Args:
            trade: Trade data
            
        Returns:
            Formatted trade value
        """
        value = trade.price * trade.volume
        return TUIFormatter.format_price(value, 2)
    
    @staticmethod
    def format_trade_direction_indicator(trade: TradeData) -> str:
        """
        Get a visual indicator for trade direction.
        
        Args:
            trade: Trade data
            
        Returns:
            Direction indicator string
        """
        return "↗" if trade.direction == Direction.LONG else "↘"
    
    @staticmethod
    def format_percentage(value: float, precision: int = 2) -> str:
        """
        Format a decimal value as percentage.
        
        Args:
            value: Value to format (e.g., 0.15)
            precision: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        if value is None:
            return "-"
        return f"{value * 100:.{precision}f}%"
    
    @staticmethod
    def format_size_description(volume: float) -> str:
        """
        Provide a size description for volume.
        
        Args:
            volume: Trade volume
            
        Returns:
            Size description
        """
        if volume >= 10000:
            return "XL"
        elif volume >= 5000:
            return "L"
        elif volume >= 1000:
            return "M"
        elif volume >= 100:
            return "S"
        else:
            return "XS"