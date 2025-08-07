"""
Trade UI components coordinator - Simplified facade.

Coordinates specialized UI components for trade display formatting.
"""

from typing import Any, Dict, TYPE_CHECKING

from foxtrot.util.object import TradeData
from .ui import TradeHeaders, TradeFormatters, TradeStyles, TradeMessages

if TYPE_CHECKING:
    from ..trade_monitor import TUITradeMonitor


class TradeUIComponents:
    """Coordinates UI components and formatting for trade display."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
        
        # Initialize UI component modules
        self.headers = TradeHeaders()
        self.formatters = TradeFormatters()
        self.styles = TradeStyles(monitor_ref)
        self.messages = TradeMessages(monitor_ref)
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    # Header management delegation
    
    def get_headers_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the headers configuration for trade display."""
        return self.headers.get_headers_config()
    
    # Formatting delegation
    
    def format_cell_content(self, content: Any, config: Dict[str, Any]) -> str:
        """Format cell content with trade-specific formatting."""
        return self.formatters.format_cell_content(content, config)
    
    def format_trade_summary_line(self, trade: TradeData) -> str:
        """Format a single line summary of a trade for status messages."""
        return self.formatters.format_trade_summary_line(trade)
    
    # Styling delegation
    
    def get_row_style(self, trade: TradeData) -> str:
        """Get the appropriate style for a trade row."""
        return self.styles.get_row_style(trade)
    
    def get_cell_style(self, content: Any, column: str, trade: TradeData) -> str:
        """Get style for a specific cell."""
        return self.styles.get_cell_style(content, column, trade)
    
    # Message formatting delegation
    
    def get_status_bar_info(self) -> str:
        """Get information for the status bar display."""
        return self.messages.get_status_bar_info()
    
    def create_welcome_message(self) -> str:
        """Create the welcome message for the trade monitor."""
        return self.messages.create_welcome_message()
    
    def format_filter_update_message(self) -> str:
        """Format a message describing current filter state."""
        return self.messages.format_filter_update_message()
    
    def get_export_filename_suggestion(self) -> str:
        """Get a suggested filename for trade export."""
        return self.messages.get_export_filename_suggestion()
    
    # Convenience methods for common operations
    
    def format_toggle_message(self, feature_name: str, enabled: bool) -> str:
        """Format a toggle status message."""
        return self.messages.format_toggle_message(feature_name, enabled)
    
    def format_summary_message(self, summary: dict) -> str:
        """Format a summary dictionary into a readable message."""
        return self.messages.format_summary_message(summary)
    
    def format_export_complete_message(self, filepath: str, count: int = None) -> str:
        """Format export completion message."""
        return self.messages.format_export_complete_message(filepath, count)
    
    def format_error_message(self, operation: str, error: str) -> str:
        """Format an error message for display."""
        return self.messages.format_error_message(operation, error)