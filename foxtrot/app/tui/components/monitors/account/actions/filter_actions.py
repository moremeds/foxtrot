"""
Account monitor filter actions.

Handles all filter-related actions and user interface interactions
for the account monitor filter functionality.
"""

import asyncio
from typing import Callable, Optional

from ..filtering import AccountFilterManager
from ..messages import AccountFilterChanged


class AccountFilterActions:
    """Handles filter-related actions for account monitor."""
    
    def __init__(self, filter_manager: AccountFilterManager):
        """Initialize filter actions handler."""
        self.filter_manager = filter_manager
        
        # Callback functions
        self._message_callback: Optional[Callable] = None
        self._update_callback: Optional[Callable] = None
        self._refresh_callback: Optional[Callable] = None
        
        # Action tracking
        self._action_history: list[str] = []
    
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
    
    def _track_action(self, action_name: str) -> None:
        """Track action for history."""
        self._action_history.append(action_name)
        if len(self._action_history) > 50:  # Keep last 50 actions
            self._action_history.pop(0)
    
    # Filter Actions
    async def action_filter_usd(self) -> None:
        """Filter accounts to show only USD currency."""
        try:
            self.filter_manager.set_currency_filter("USD")
            await self._add_system_message("Applied USD filter")
            await self._trigger_refresh()
            self._track_action("filter_usd")
            
        except Exception as e:
            await self._add_system_message(f"Error applying USD filter: {e}")
    
    async def action_filter_zero(self) -> None:
        """Toggle filter to show/hide zero balance accounts."""
        try:
            current_setting = self.filter_manager.display_settings.show_zero_balances
            self.filter_manager.display_settings.show_zero_balances = not current_setting
            
            status = "showing" if not current_setting else "hiding"
            await self._add_system_message(f"Now {status} zero balance accounts")
            await self._trigger_refresh()
            self._track_action("filter_zero")
            
        except Exception as e:
            await self._add_system_message(f"Error toggling zero balance filter: {e}")
    
    async def action_filter_margin(self) -> None:
        """Filter accounts to show only those with margin usage."""
        try:
            self.filter_manager.set_min_balance_filter(1000.0)  # Minimum balance for margin
            await self._add_system_message("Applied margin filter (min $1000 balance)")
            await self._trigger_refresh()
            self._track_action("filter_margin")
            
        except Exception as e:
            await self._add_system_message(f"Error applying margin filter: {e}")
    
    async def action_clear_filters(self) -> None:
        """Clear all active filters."""
        try:
            self.filter_manager.clear_all_filters()
            await self._add_system_message("All filters cleared")
            await self._trigger_refresh()
            self._track_action("clear_filters")
            
        except Exception as e:
            await self._add_system_message(f"Error clearing filters: {e}")
    
    async def action_filter_by_currency(self, currency: str) -> None:
        """
        Filter accounts by specific currency.
        
        Args:
            currency: Currency code (e.g., 'USD', 'HKD', 'CNY')
        """
        try:
            self.filter_manager.set_currency_filter(currency.upper())
            await self._add_system_message(f"Applied {currency} currency filter")
            await self._trigger_refresh()
            self._track_action(f"filter_currency_{currency}")
            
        except Exception as e:
            await self._add_system_message(f"Error applying {currency} filter: {e}")
    
    async def action_filter_by_gateway(self, gateway: str) -> None:
        """
        Filter accounts by specific gateway.
        
        Args:
            gateway: Gateway name (e.g., 'BINANCE', 'FUTU', 'IB')
        """
        try:
            self.filter_manager.set_gateway_filter(gateway.upper())
            await self._add_system_message(f"Applied {gateway} gateway filter")
            await self._trigger_refresh()
            self._track_action(f"filter_gateway_{gateway}")
            
        except Exception as e:
            await self._add_system_message(f"Error applying {gateway} filter: {e}")
    
    async def action_filter_by_balance_range(self, min_balance: float, max_balance: float = None) -> None:
        """
        Filter accounts by balance range.
        
        Args:
            min_balance: Minimum balance threshold
            max_balance: Maximum balance threshold (optional)
        """
        try:
            self.filter_manager.set_min_balance_filter(min_balance)
            if max_balance:
                self.filter_manager.set_max_balance_filter(max_balance)
                await self._add_system_message(
                    f"Applied balance filter: ${min_balance:,.2f} - ${max_balance:,.2f}"
                )
            else:
                await self._add_system_message(f"Applied minimum balance filter: ${min_balance:,.2f}")
            
            await self._trigger_refresh()
            self._track_action("filter_balance_range")
            
        except Exception as e:
            await self._add_system_message(f"Error applying balance filter: {e}")
    
    async def action_filter_high_risk(self) -> None:
        """Filter to show only high-risk accounts."""
        try:
            # Set filter for accounts with margin ratio > 0.7
            self.filter_manager.set_risk_filter("HIGH")
            await self._add_system_message("Applied high-risk accounts filter")
            await self._trigger_refresh()
            self._track_action("filter_high_risk")
            
        except Exception as e:
            await self._add_system_message(f"Error applying high-risk filter: {e}")
    
    async def action_filter_profitable(self) -> None:
        """Filter to show only profitable accounts."""
        try:
            # Set filter for accounts with positive P&L
            self.filter_manager.set_pnl_filter("POSITIVE")
            await self._add_system_message("Applied profitable accounts filter")
            await self._trigger_refresh()
            self._track_action("filter_profitable")
            
        except Exception as e:
            await self._add_system_message(f"Error applying profitable filter: {e}")
    
    async def action_filter_losing(self) -> None:
        """Filter to show only losing accounts."""
        try:
            # Set filter for accounts with negative P&L
            self.filter_manager.set_pnl_filter("NEGATIVE")
            await self._add_system_message("Applied losing accounts filter")
            await self._trigger_refresh()
            self._track_action("filter_losing")
            
        except Exception as e:
            await self._add_system_message(f"Error applying losing filter: {e}")
    
    # Filter Management Methods
    def get_active_filters(self) -> dict[str, str]:
        """Get summary of currently active filters."""
        return {
            "currency": self.filter_manager.currency_filter or "None",
            "gateway": self.filter_manager.gateway_filter or "None", 
            "min_balance": str(self.filter_manager.min_balance_filter) if self.filter_manager.min_balance_filter else "None",
            "show_zero": str(self.filter_manager.display_settings.show_zero_balances)
        }
    
    def get_filter_count(self) -> int:
        """Get number of active filters."""
        count = 0
        if self.filter_manager.currency_filter:
            count += 1
        if self.filter_manager.gateway_filter:
            count += 1
        if self.filter_manager.min_balance_filter is not None:
            count += 1
        if not self.filter_manager.display_settings.show_zero_balances:
            count += 1
        return count
    
    def get_action_history(self, limit: int = 10) -> list[str]:
        """Get recent action history."""
        return self._action_history[-limit:]