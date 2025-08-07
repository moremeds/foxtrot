"""
Action delegation for trade controller.

Handles delegation of UI actions to appropriate components.
"""

import asyncio
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .trade_controller import TradeController


class ActionDelegates:
    """Handles action delegation for the trade controller."""
    
    def __init__(self, controller):
        """
        Initialize with controller reference.
        
        Args:
            controller: TradeController instance
        """
        self.controller = controller
    
    def handle_action_filter_session(self) -> None:
        """Handle session filter action."""
        self.controller.filters_actions.handle_filter_session()
    
    def handle_action_filter_long(self) -> None:
        """Handle long trades filter action."""
        self.controller.filters_actions.handle_filter_long()
    
    def handle_action_filter_short(self) -> None:
        """Handle short trades filter action."""
        self.controller.filters_actions.handle_filter_short()
    
    def handle_action_toggle_large(self) -> None:
        """Handle large trade highlighting toggle."""
        self.controller.filters_actions.handle_toggle_large()
    
    def handle_action_toggle_auto_scroll(self) -> None:
        """Handle auto-scroll toggle."""
        self.controller.filters_actions.handle_toggle_auto_scroll()
    
    def handle_action_clear_filters(self) -> None:
        """Handle clear all filters action."""
        self.controller.filters_actions.handle_clear_filters()
    
    def handle_action_show_daily_summary(self) -> None:
        """Handle show daily summary action."""
        summary_msg = self.controller.statistics.get_formatted_summary_message()
        monitor = self.controller.monitor
        asyncio.create_task(monitor._add_system_message(summary_msg))
    
    async def handle_action_save_csv(self) -> None:
        """Handle CSV export action."""
        await self.controller.export.save_csv()
    
    # Utility method delegation
    
    def get_status_info(self) -> str:
        """Get status information for display."""
        return self.controller.ui_components.get_status_bar_info()
    
    def format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """Format cell content using UI components."""
        return self.controller.ui_components.format_cell_content(content, config)
    
    def get_daily_summary(self) -> dict[str, Any]:
        """Get daily summary from statistics."""
        return self.controller.statistics.get_daily_summary()