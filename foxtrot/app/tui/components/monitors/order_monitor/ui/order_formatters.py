"""
Order monitor UI formatting functionality.

Handles cell content formatting, row styling, and display formatting
for order data in the TUI order monitor.
"""

from typing import Any
from foxtrot.util.constants import Direction, Offset, OrderType, Status
from foxtrot.util.object import OrderData
from ....utils.formatters import TUIFormatter


class OrderFormatters:
    """Handles formatting logic for order monitor display."""
    
    def __init__(self, color_manager):
        """Initialize order formatters."""
        self.color_manager = color_manager
    
    def format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with order-specific formatting.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        if content is None:
            return "-"

        cell_type = config.get("cell", "default")
        
        try:
            # Order-specific cell formatting
            if cell_type == "direction":
                return self._format_direction(content)
            elif cell_type == "order_type":
                return self._format_order_type(content)
            elif cell_type == "status":
                return self._format_status(content)
            elif cell_type == "volume":
                return self._format_volume(content, config.get("precision", 0))
            elif cell_type == "float":
                return self._format_price(content, config.get("precision", 4))
            elif cell_type == "datetime":
                return self._format_datetime(content)
            elif cell_type == "enum":
                return self._format_enum(content)
            else:
                return str(content)
        except Exception:
            return str(content)
    
    def _format_direction(self, direction: Direction) -> str:
        """Format direction with appropriate symbols."""
        if direction == Direction.LONG:
            return "LONG ↗"
        elif direction == Direction.SHORT:
            return "SHORT ↘"
        else:
            return str(direction)
    
    def _format_order_type(self, order_type: OrderType) -> str:
        """Format order type with abbreviations."""
        type_map = {
            OrderType.LIMIT: "LMT",
            OrderType.MARKET: "MKT",
            OrderType.STOP: "STP",
            OrderType.FAK: "FAK",
            OrderType.FOK: "FOK"
        }
        return type_map.get(order_type, str(order_type))
    
    def _format_status(self, status: Status) -> str:
        """Format order status with symbols."""
        status_map = {
            Status.SUBMITTING: "SUBMITTING ⏳",
            Status.NOTTRADED: "ACTIVE ●",
            Status.PARTTRADED: "PARTIAL ◐",
            Status.ALLTRADED: "FILLED ✓",
            Status.CANCELLED: "CANCELLED ✗",
            Status.REJECTED: "REJECTED ❌"
        }
        return status_map.get(status, str(status))
    
    def _format_volume(self, volume: float, precision: int = 0) -> str:
        """Format volume with appropriate precision."""
        if precision == 0:
            return f"{int(volume):,}" if volume else "0"
        else:
            return f"{volume:.{precision}f}" if volume else "0.00"
    
    def _format_price(self, price: float, precision: int = 4) -> str:
        """Format price with appropriate precision."""
        return f"{price:.{precision}f}" if price else "0.0000"
    
    def _format_datetime(self, dt) -> str:
        """Format datetime for display."""
        if hasattr(dt, 'strftime'):
            return dt.strftime("%H:%M:%S")
        return str(dt)
    
    def _format_enum(self, value) -> str:
        """Format enum values."""
        if hasattr(value, 'value'):
            return str(value.value)
        return str(value)
    
    def get_row_style_class(self, order_data: OrderData) -> str:
        """
        Get appropriate style class for order row based on status and direction.
        
        Args:
            order_data: The order data
            
        Returns:
            CSS class name for styling
        """
        # Status-based styling (primary)
        if order_data.status == Status.ALLTRADED:
            return "order-filled"
        elif order_data.status == Status.CANCELLED:
            return "order-cancelled"
        elif order_data.status == Status.REJECTED:
            return "order-rejected"
        elif order_data.status == Status.PARTTRADED:
            return "order-partial"
        elif order_data.status == Status.SUBMITTING:
            return "order-submitting"
        
        # Direction-based styling (secondary for active orders)
        elif order_data.status == Status.NOTTRADED:
            if order_data.direction == Direction.LONG:
                return "order-long-active"
            elif order_data.direction == Direction.SHORT:
                return "order-short-active"
        
        return "order-default"
    
    def get_status_color(self, status: Status) -> str:
        """Get color code for order status."""
        color_map = {
            Status.ALLTRADED: "green",
            Status.PARTTRADED: "yellow", 
            Status.NOTTRADED: "blue",
            Status.CANCELLED: "grey",
            Status.REJECTED: "red",
            Status.SUBMITTING: "cyan"
        }
        return color_map.get(status, "white")
    
    def get_direction_color(self, direction: Direction) -> str:
        """Get color code for order direction."""
        if direction == Direction.LONG:
            return "green"
        elif direction == Direction.SHORT:
            return "red"
        return "white"