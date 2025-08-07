"""
Trade controller and business logic coordination - Simplified.

Coordinates between UI components, statistics, filtering, and export functionality.
"""

import asyncio
import weakref
from typing import Any, TYPE_CHECKING

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_TRADE
from foxtrot.util.object import TradeData

from .trade_filters_actions import TradeFiltersActions
from .trade_statistics import TradeStatistics
from .trade_export import TradeExport
from .trade_ui_components import TradeUIComponents
from .action_delegates import ActionDelegates

if TYPE_CHECKING:
    from ..trade_monitor import TUITradeMonitor


class TradeController:
    """
    Coordinates trade monitor components and business logic.
    
    Acts as the central coordinator for all trade monitor functionality,
    managing the interaction between UI, statistics, filtering, and export.
    """
    
    def __init__(self, monitor_ref, main_engine: MainEngine, event_engine: EventEngine):
        """
        Initialize the trade controller.
        
        Args:
            monitor_ref: Weak reference to the monitor
            main_engine: The main trading engine
            event_engine: The event engine
        """
        self._monitor_ref = monitor_ref
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # Initialize component modules
        self.filters_actions = TradeFiltersActions(monitor_ref)
        self.statistics = TradeStatistics(monitor_ref)
        self.export = TradeExport(monitor_ref)
        self.ui_components = TradeUIComponents(monitor_ref)
        
        # Initialize action delegates
        self.action_delegates = ActionDelegates(self)
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    def initialize_components(self) -> None:
        """Initialize all controller components."""
        # Initialize filters
        self.filters_actions.initialize_filters()
        
        # Set up monitor with component references
        monitor = self.monitor
        monitor.trade_statistics = self.statistics
        monitor.trade_filters_actions = self.filters_actions
        monitor.trade_export = self.export
        monitor.trade_ui_components = self.ui_components
        
        # Configure headers from UI components
        monitor.headers = self.ui_components.get_headers_config()
    
    async def initialize_monitor(self) -> None:
        """Initialize the monitor asynchronously."""
        monitor = self.monitor
        
        # Add welcome message
        welcome_msg = self.ui_components.create_welcome_message()
        await monitor._add_system_message(welcome_msg)
    
    def process_trade_event(self, event) -> None:
        """
        Process a trade event from the event engine.
        
        Args:
            event: Trade event to process
        """
        if event.type != EVENT_TRADE:
            return
        
        trade_data = event.data
        if not isinstance(trade_data, TradeData):
            return
        
        # Check if trade should be displayed (filtering)
        if not self.filters_actions.should_show_trade(trade_data):
            return
        
        # Process trade for statistics
        self.statistics.process_trade_for_statistics(trade_data)
        
        # Add to display (delegated to monitor's base functionality)
        asyncio.create_task(self._add_trade_to_display(trade_data))
    
    async def _add_trade_to_display(self, trade_data: TradeData) -> None:
        """Add trade to the monitor display."""
        monitor = self.monitor
        
        # Format trade data for display
        formatted_data = self._format_trade_for_display(trade_data)
        
        # Add to data table (using monitor's base functionality)
        if hasattr(monitor, 'add_data'):
            await monitor.add_data(formatted_data)
        
        # Auto-scroll to new trade if enabled
        if monitor.auto_scroll_to_new_trades:
            asyncio.create_task(self._scroll_to_latest())
        
        # Log trade summary
        summary = self.ui_components.format_trade_summary_line(trade_data)
        await monitor._add_system_message(f"Trade executed: {summary}")
    
    def _format_trade_for_display(self, trade_data: TradeData) -> dict[str, Any]:
        """Format trade data for display in the table."""
        return {
            "tradeid": trade_data.tradeid,
            "orderid": trade_data.orderid,
            "symbol": trade_data.symbol,
            "exchange": trade_data.exchange,
            "direction": trade_data.direction,
            "offset": trade_data.offset,
            "price": trade_data.price,
            "volume": trade_data.volume,
            "datetime": trade_data.datetime,
            "gateway_name": trade_data.gateway_name,
        }
    
    async def _scroll_to_latest(self) -> None:
        """Scroll to the latest trade in the display."""
        # Implementation depends on the monitor's scrolling mechanism
        pass
    
    # Action delegation methods - delegate to ActionDelegates
    
    def handle_action_filter_session(self) -> None:
        """Handle session filter action."""
        self.action_delegates.handle_action_filter_session()
    
    def handle_action_filter_long(self) -> None:
        """Handle long trades filter action."""
        self.action_delegates.handle_action_filter_long()
    
    def handle_action_filter_short(self) -> None:
        """Handle short trades filter action."""
        self.action_delegates.handle_action_filter_short()
    
    def handle_action_toggle_large(self) -> None:
        """Handle large trade highlighting toggle."""
        self.action_delegates.handle_action_toggle_large()
    
    def handle_action_toggle_auto_scroll(self) -> None:
        """Handle auto-scroll toggle."""
        self.action_delegates.handle_action_toggle_auto_scroll()
    
    def handle_action_clear_filters(self) -> None:
        """Handle clear all filters action."""
        self.action_delegates.handle_action_clear_filters()
    
    def handle_action_show_daily_summary(self) -> None:
        """Handle show daily summary action."""
        self.action_delegates.handle_action_show_daily_summary()
    
    async def handle_action_save_csv(self) -> None:
        """Handle CSV export action."""
        await self.action_delegates.handle_action_save_csv()
    
    # Utility methods - delegate to ActionDelegates
    
    def get_status_info(self) -> str:
        """Get status information for display."""
        return self.action_delegates.get_status_info()
    
    def format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """Format cell content using UI components."""
        return self.action_delegates.format_cell_content(content, config)
    
    def get_daily_summary(self) -> dict[str, Any]:
        """Get daily summary from statistics."""
        return self.action_delegates.get_daily_summary()
    
    def cleanup(self) -> None:
        """Cleanup controller resources."""
        # Reset statistics
        self.statistics.reset_statistics()