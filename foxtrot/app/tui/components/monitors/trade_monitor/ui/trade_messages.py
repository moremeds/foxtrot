"""
Trade message formatting and status information.

Handles status messages, notifications, and UI text generation.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction
from ....utils.formatters import TUIFormatter

if TYPE_CHECKING:
    from ...trade_monitor import TUITradeMonitor


class TradeMessages:
    """Handles message formatting and status information for trades."""
    
    def __init__(self, monitor_ref=None):
        """
        Initialize with optional monitor reference.
        
        Args:
            monitor_ref: Weak reference to the monitor (optional)
        """
        self._monitor_ref = monitor_ref
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        if self._monitor_ref is None:
            raise RuntimeError("No monitor reference set")
        
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    def get_status_bar_info(self) -> str:
        """
        Get information for the status bar display.
        
        Returns:
            Formatted status bar information
        """
        if self._monitor_ref is None:
            return "Trade Monitor"
        
        monitor = self.monitor
        
        # Get statistics if available
        stats = {}
        if hasattr(monitor, 'trade_statistics') and monitor.trade_statistics:
            stats = monitor.trade_statistics.statistics
        
        # Build filter status
        filters = []
        if hasattr(monitor, 'symbol_filter') and monitor.symbol_filter:
            filters.append(f"Symbol:{monitor.symbol_filter}")
        if hasattr(monitor, 'direction_filter') and monitor.direction_filter:
            filters.append(f"Dir:{monitor.direction_filter.value}")
        if hasattr(monitor, 'show_session_only') and monitor.show_session_only:
            filters.append("Session")
        
        filter_str = f" | Filters: {', '.join(filters)}" if filters else ""
        
        # Build statistics summary
        trades_count = stats.get("total_trades", 0)
        total_volume = stats.get("total_volume", 0.0)
        volume_str = TUIFormatter.format_volume(total_volume)
        
        return f"Trades: {trades_count} | Volume: {volume_str}{filter_str}"
    
    @staticmethod
    def create_welcome_message() -> str:
        """
        Create the welcome message for the trade monitor.
        
        Returns:
            Welcome message text
        """
        return "Trade monitor ready for execution data"
    
    def format_filter_update_message(self) -> str:
        """
        Format a message describing current filter state.
        
        Returns:
            Filter status message
        """
        if self._monitor_ref is None:
            return "Filters updated"
        
        monitor = self.monitor
        active_filters = []
        
        if hasattr(monitor, 'symbol_filter') and monitor.symbol_filter:
            active_filters.append(f"Symbol: {monitor.symbol_filter}")
        if hasattr(monitor, 'direction_filter') and monitor.direction_filter:
            active_filters.append(f"Direction: {monitor.direction_filter.value}")
        if hasattr(monitor, 'exchange_filter') and monitor.exchange_filter:
            active_filters.append(f"Exchange: {monitor.exchange_filter.value}")
        if hasattr(monitor, 'show_session_only') and monitor.show_session_only:
            active_filters.append("Session only")
        
        if not active_filters:
            return "All filters cleared"
        
        return f"Active filters: {', '.join(active_filters)}"
    
    def get_export_filename_suggestion(self) -> str:
        """
        Get a suggested filename for trade export.
        
        Returns:
            Suggested filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self._monitor_ref is None:
            return f"trade_history_{timestamp}.csv"
        
        monitor = self.monitor
        
        if hasattr(monitor, 'symbol_filter') and monitor.symbol_filter:
            return f"trades_{monitor.symbol_filter}_{timestamp}.csv"
        elif hasattr(monitor, 'show_session_only') and monitor.show_session_only:
            return f"session_trades_{timestamp}.csv"
        else:
            return f"trade_history_{timestamp}.csv"
    
    @staticmethod
    def format_toggle_message(feature_name: str, enabled: bool) -> str:
        """
        Format a toggle status message.
        
        Args:
            feature_name: Name of the feature being toggled
            enabled: Whether the feature is now enabled
            
        Returns:
            Formatted toggle message
        """
        status = "ON" if enabled else "OFF"
        return f"{feature_name} {status}"
    
    @staticmethod
    def format_summary_message(summary: dict) -> str:
        """
        Format a summary dictionary into a readable message.
        
        Args:
            summary: Dictionary with summary data
            
        Returns:
            Formatted summary message
        """
        trades = summary.get("trades", 0)
        volume = summary.get("volume", 0.0)
        volume_str = TUIFormatter.format_volume(volume)
        
        if "avg_price" in summary:
            avg_price = TUIFormatter.format_price(summary["avg_price"], 2)
            return f"Today: {trades} trades, Vol: {volume_str}, Avg: {avg_price}"
        else:
            return f"Today: {trades} trades, Vol: {volume_str}"
    
    @staticmethod
    def format_export_complete_message(filepath: str, count: int = None) -> str:
        """
        Format export completion message.
        
        Args:
            filepath: Path where file was exported
            count: Optional count of exported records
            
        Returns:
            Export completion message
        """
        if count is not None:
            return f"Exported {count} trades to {filepath}"
        else:
            return f"Trade history exported to {filepath}"
    
    @staticmethod
    def format_error_message(operation: str, error: str) -> str:
        """
        Format an error message for display.
        
        Args:
            operation: Operation that failed
            error: Error description
            
        Returns:
            Formatted error message
        """
        return f"Failed to {operation}: {error}"