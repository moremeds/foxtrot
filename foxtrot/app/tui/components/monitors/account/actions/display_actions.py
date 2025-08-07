"""
Account monitor display actions.

Handles display toggle actions and view switching functionality
for the account monitor interface.
"""

from typing import Callable, Optional, Dict, Any

from ..config import AccountDisplaySettings


class AccountDisplayActions:
    """Handles display-related actions for account monitor."""
    
    def __init__(self, display_settings: AccountDisplaySettings):
        """Initialize display actions handler."""
        self.display_settings = display_settings
        
        # Callback functions
        self._message_callback: Optional[Callable] = None
        self._update_callback: Optional[Callable] = None
        self._refresh_callback: Optional[Callable] = None
    
    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for system messages."""
        self._message_callback = callback
    
    def set_update_callback(self, callback: Callable) -> None:
        """Set callback for triggering updates."""
        self._update_callback = callback
    
    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback for refreshing display."""
        self._refresh_callback = callback
    
    async def _add_system_message(self, message: str) -> None:
        """Add system message if callback is set."""
        if self._message_callback:
            await self._message_callback(message)
    
    async def _trigger_update(self) -> None:
        """Trigger update if callback is set."""
        if self._update_callback:
            await self._update_callback()
    
    async def _trigger_refresh(self) -> None:
        """Trigger refresh if callback is set."""
        if self._refresh_callback:
            await self._refresh_callback()
    
    # Display Toggle Actions
    async def action_toggle_percentage(self) -> None:
        """Toggle percentage change display."""
        try:
            current = self.display_settings.show_percentage_changes
            self.display_settings.show_percentage_changes = not current
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Percentage changes {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling percentage display: {e}")
    
    async def action_toggle_margin_warnings(self) -> None:
        """Toggle margin warning highlights."""
        try:
            current = self.display_settings.highlight_margin_warnings
            self.display_settings.highlight_margin_warnings = not current
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Margin warnings {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling margin warnings: {e}")
    
    async def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to updates."""
        try:
            current = self.display_settings.auto_scroll_to_updates
            self.display_settings.auto_scroll_to_updates = not current
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Auto-scroll {status}")
            
        except Exception as e:
            await self._add_system_message(f"Error toggling auto-scroll: {e}")
    
    async def action_toggle_currency_grouping(self) -> None:
        """Toggle currency grouping display."""
        try:
            current = self.display_settings.group_by_currency
            self.display_settings.group_by_currency = not current
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Currency grouping {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling currency grouping: {e}")
    
    async def action_toggle_compact_view(self) -> None:
        """Toggle compact view mode."""
        try:
            current = getattr(self.display_settings, 'compact_view', False)
            setattr(self.display_settings, 'compact_view', not current)
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Compact view {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling compact view: {e}")
    
    async def action_toggle_detailed_view(self) -> None:
        """Toggle detailed view mode."""
        try:
            current = getattr(self.display_settings, 'detailed_view', True)
            setattr(self.display_settings, 'detailed_view', not current)
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Detailed view {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling detailed view: {e}")
    
    async def action_toggle_color_coding(self) -> None:
        """Toggle color coding for profit/loss."""
        try:
            current = getattr(self.display_settings, 'color_coding', True)
            setattr(self.display_settings, 'color_coding', not current)
            
            status = "enabled" if not current else "disabled"
            await self._add_system_message(f"Color coding {status}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error toggling color coding: {e}")
    
    async def action_set_refresh_rate(self, rate_seconds: float) -> None:
        """
        Set refresh rate for data updates.
        
        Args:
            rate_seconds: Refresh interval in seconds
        """
        try:
            if rate_seconds < 0.1:
                await self._add_system_message("Minimum refresh rate is 0.1 seconds")
                return
            
            self.display_settings.refresh_rate = rate_seconds
            await self._add_system_message(f"Refresh rate set to {rate_seconds}s")
            
        except Exception as e:
            await self._add_system_message(f"Error setting refresh rate: {e}")
    
    async def action_cycle_sort_order(self) -> None:
        """Cycle through different sort orders."""
        try:
            sort_orders = ["balance", "net_pnl", "currency", "gateway_name", "accountid"]
            current_sort = getattr(self.display_settings, 'sort_column', 'balance')
            
            try:
                current_index = sort_orders.index(current_sort)
                next_index = (current_index + 1) % len(sort_orders)
            except ValueError:
                next_index = 0
            
            next_sort = sort_orders[next_index]
            setattr(self.display_settings, 'sort_column', next_sort)
            
            await self._add_system_message(f"Sorted by {next_sort}")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error cycling sort order: {e}")
    
    async def action_reset_display_settings(self) -> None:
        """Reset all display settings to defaults."""
        try:
            self.display_settings.reset_to_defaults()
            await self._add_system_message("Display settings reset to defaults")
            await self._trigger_refresh()
            
        except Exception as e:
            await self._add_system_message(f"Error resetting display settings: {e}")
    
    # View State Management
    def get_display_state(self) -> Dict[str, Any]:
        """Get current display state."""
        return {
            "show_percentage_changes": self.display_settings.show_percentage_changes,
            "highlight_margin_warnings": self.display_settings.highlight_margin_warnings,
            "auto_scroll_to_updates": self.display_settings.auto_scroll_to_updates,
            "group_by_currency": self.display_settings.group_by_currency,
            "show_zero_balances": self.display_settings.show_zero_balances,
            "refresh_rate": getattr(self.display_settings, 'refresh_rate', 1.0),
            "sort_column": getattr(self.display_settings, 'sort_column', 'balance'),
            "compact_view": getattr(self.display_settings, 'compact_view', False),
            "detailed_view": getattr(self.display_settings, 'detailed_view', True),
            "color_coding": getattr(self.display_settings, 'color_coding', True)
        }
    
    def set_display_state(self, state: Dict[str, Any]) -> None:
        """Set display state from dictionary."""
        for key, value in state.items():
            if hasattr(self.display_settings, key):
                setattr(self.display_settings, key, value)
    
    def get_available_display_actions(self) -> Dict[str, str]:
        """Get list of available display actions."""
        return {
            "toggle_percentage": "Toggle percentage change display",
            "toggle_margin_warnings": "Toggle margin warning highlights", 
            "toggle_auto_scroll": "Toggle automatic scrolling",
            "toggle_currency_grouping": "Toggle currency grouping",
            "toggle_compact_view": "Toggle compact view mode",
            "toggle_detailed_view": "Toggle detailed view mode",
            "toggle_color_coding": "Toggle color coding",
            "cycle_sort_order": "Cycle through sort orders",
            "reset_display_settings": "Reset to default settings"
        }