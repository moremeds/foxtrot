"""
Account monitor action coordinator.

Handles delegation of action methods to specialized components
and manages action method routing.
"""

from typing import Any, Callable, Dict, Optional

from foxtrot.util.object import AccountData

from .filter_actions import AccountFilterActions
from .display_actions import AccountDisplayActions
from .data_actions import AccountDataActions
from .system_actions import AccountSystemActions


class AccountActionCoordinator:
    """Coordinates and delegates actions to specialized components."""
    
    def __init__(
        self,
        filter_actions: AccountFilterActions,
        display_actions: AccountDisplayActions, 
        data_actions: AccountDataActions,
        system_actions: AccountSystemActions
    ):
        """Initialize action coordinator."""
        self.filter_actions = filter_actions
        self.display_actions = display_actions
        self.data_actions = data_actions
        self.system_actions = system_actions

    # Filter Action Delegates
    async def action_filter_usd(self) -> None:
        """Filter accounts to show only USD currency."""
        await self.filter_actions.action_filter_usd()

    async def action_filter_zero(self) -> None:
        """Toggle filter to show/hide zero balance accounts."""
        await self.filter_actions.action_filter_zero()

    async def action_filter_margin(self) -> None:
        """Filter accounts to show only those with margin usage."""
        await self.filter_actions.action_filter_margin()

    async def action_clear_filters(self) -> None:
        """Clear all active filters."""
        await self.filter_actions.action_clear_filters()

    async def action_filter_by_currency(self, currency: str) -> None:
        """Filter accounts by specific currency."""
        await self.filter_actions.action_filter_by_currency(currency)

    async def action_filter_by_gateway(self, gateway: str) -> None:
        """Filter accounts by specific gateway."""
        await self.filter_actions.action_filter_by_gateway(gateway)

    async def action_filter_high_risk(self) -> None:
        """Filter to show only high-risk accounts."""
        await self.filter_actions.action_filter_high_risk()

    async def action_filter_profitable(self) -> None:
        """Filter to show only profitable accounts."""
        await self.filter_actions.action_filter_profitable()

    async def action_filter_losing(self) -> None:
        """Filter to show only losing accounts."""
        await self.filter_actions.action_filter_losing()

    # Display Action Delegates
    async def action_toggle_percentage(self) -> None:
        """Toggle percentage change display."""
        await self.display_actions.action_toggle_percentage()

    async def action_toggle_margin_warnings(self) -> None:
        """Toggle margin warning highlights."""
        await self.display_actions.action_toggle_margin_warnings()

    async def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to updates."""
        await self.display_actions.action_toggle_auto_scroll()

    async def action_toggle_currency_grouping(self) -> None:
        """Toggle currency grouping display."""
        await self.display_actions.action_toggle_currency_grouping()

    async def action_toggle_compact_view(self) -> None:
        """Toggle compact view mode."""
        await self.display_actions.action_toggle_compact_view()

    async def action_toggle_detailed_view(self) -> None:
        """Toggle detailed view mode."""
        await self.display_actions.action_toggle_detailed_view()

    async def action_toggle_color_coding(self) -> None:
        """Toggle color coding for profit/loss."""
        await self.display_actions.action_toggle_color_coding()

    async def action_cycle_sort_order(self) -> None:
        """Cycle through different sort orders."""
        await self.display_actions.action_cycle_sort_order()

    # Data Display Action Delegates
    async def action_show_risk(self, risk_metrics: Dict[str, Any]) -> None:
        """Display risk metrics summary."""
        await self.data_actions.action_show_risk(risk_metrics)

    async def action_show_currency_breakdown(self, currency_data: Dict[str, Dict[str, float]]) -> None:
        """Display currency breakdown information."""
        await self.data_actions.action_show_currency_breakdown(currency_data)

    async def action_show_balance_history(self, summary: Dict[str, Any]) -> None:
        """Display balance history summary."""
        await self.data_actions.action_show_balance_history(summary)

    async def action_show_performance_summary(self, performance_data: Dict[str, Any]) -> None:
        """Display performance summary."""
        await self.data_actions.action_show_performance_summary(performance_data)

    async def action_select_account(self, account_data: AccountData) -> None:
        """Handle account selection action."""
        await self.data_actions.action_select_account(account_data)

    async def action_analyze_risk_trends(self, risk_history: list[Dict[str, Any]]) -> None:
        """Analyze and display risk trends."""
        await self.data_actions.action_analyze_risk_trends(risk_history)

    # System Action Delegates
    async def action_refresh_data(self) -> None:
        """Refresh all account data."""
        await self.system_actions.action_refresh_data()

    async def action_reset_view(self, clear_filters_callback=None, reset_display_callback=None) -> None:
        """Reset view to default state."""
        await self.system_actions.action_reset_view(
            clear_filters_callback=clear_filters_callback or self.action_clear_filters,
            reset_display_callback=reset_display_callback or self.display_actions.action_reset_display_settings
        )

    async def action_export_summary(self) -> None:
        """Export account summary data."""
        await self.system_actions.action_export_summary()

    # Action Information Methods
    def get_available_actions(self) -> Dict[str, str]:
        """Get all available actions from components."""
        actions = {}
        
        # Get actions from each component
        filter_actions = getattr(self.filter_actions, 'get_available_filters', lambda: {})()
        display_actions = self.display_actions.get_available_display_actions()
        data_actions = self.data_actions.get_available_data_actions()
        system_actions = self.system_actions.get_available_system_actions()
        
        # Combine all actions
        actions.update(filter_actions or {})
        actions.update(display_actions)
        actions.update(data_actions)
        actions.update(system_actions)
        
        return actions

    def get_action_history(self, limit: int = 10) -> list[str]:
        """Get recent action history from system component."""
        return self.system_actions.get_action_history(limit)

    # Component Access Methods
    def get_filter_actions(self) -> AccountFilterActions:
        """Get filter actions component."""
        return self.filter_actions

    def get_display_actions(self) -> AccountDisplayActions:
        """Get display actions component."""
        return self.display_actions

    def get_data_actions(self) -> AccountDataActions:
        """Get data actions component."""
        return self.data_actions

    def get_system_actions(self) -> AccountSystemActions:
        """Get system actions component."""
        return self.system_actions