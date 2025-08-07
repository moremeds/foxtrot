"""
Market data display manager for UI updates and formatting.

This module handles display updates, styling, and data presentation
for the market data panel.
"""

from decimal import Decimal
from typing import Any, Dict, Optional, List
from textual.widgets import Static

from foxtrot.app.tui.utils.formatters import format_currency, format_number
from .ui_layout import MarketDataUILayout


class MarketDataDisplayManager:
    """
    Manages UI updates and display formatting for market data.
    
    This class focuses on data presentation and styling,
    delegating layout creation to MarketDataUILayout.
    """

    def __init__(self):
        # UI layout manager
        self.ui_layout = MarketDataUILayout()
        
        # Get component references from layout
        self._ui_components = {}

    def initialize_components(self):
        """Initialize UI component references from layout."""
        self._ui_components = self.ui_layout.get_ui_components()

    @property
    def bid_ask_label(self) -> Optional[Static]:
        return self._ui_components.get('bid_ask_label')

    @property
    def last_price_label(self) -> Optional[Static]:
        return self._ui_components.get('last_price_label')

    @property
    def volume_label(self) -> Optional[Static]:
        return self._ui_components.get('volume_label')

    @property
    def status_label(self) -> Optional[Static]:
        return self._ui_components.get('status_label')

    @property
    def depth_levels(self) -> List[Static]:
        return self._ui_components.get('depth_levels', [])

    async def update_all_displays(self, market_data: Dict[str, Any]) -> None:
        """Update all display components with current market data."""
        if not market_data:
            return
        
        await self.update_price_display(market_data)
        await self.update_volume_display(market_data)
        await self.update_depth_display(market_data)

    async def update_price_display(self, market_data: Dict[str, Any]) -> None:
        """Update bid/ask and last price displays."""
        # Update bid/ask
        if self.bid_ask_label:
            bid = market_data.get("bid")
            ask = market_data.get("ask")
            
            if bid and ask:
                spread = ask - bid
                spread_bps = (spread / ask * 10000) if ask > 0 else 0
                
                self.bid_ask_label.update(
                    f"Bid/Ask: {format_currency(bid)} / {format_currency(ask)} "
                    f"(Spread: {spread_bps:.1f}bps)"
                )

        # Update last price with change indicators
        if self.last_price_label:
            last = market_data.get("last")
            change = market_data.get("change")
            change_percent = market_data.get("change_percent")

            if last and change is not None and change_percent is not None:
                change_sign = "+" if change > 0 else ""
                change_indicator = "↑" if change > 0 else "↓" if change < 0 else "→"
                
                self.last_price_label.update(
                    f"Last: {format_currency(last)} "
                    f"{change_indicator} {change_sign}{format_currency(change)} "
                    f"({change_sign}{change_percent:.2f}%)"
                )
                
                # Apply color styling based on change
                self.apply_price_change_styling(change)

    async def update_volume_display(self, market_data: Dict[str, Any]) -> None:
        """Update volume and daily statistics display."""
        if not self.volume_label:
            return
            
        volume = market_data.get("volume", 0)
        high = market_data.get("high")
        low = market_data.get("low")
        
        volume_text = f"Volume: {format_number(volume)}"
        
        if high and low:
            volume_text += f" | Range: {format_currency(low)} - {format_currency(high)}"
            
        self.volume_label.update(volume_text)

    async def update_depth_display(self, market_data: Dict[str, Any]) -> None:
        """Update market depth display with bid/ask levels."""
        depth_data = market_data.get("depth", {})
        bids = depth_data.get("bids", [])
        asks = depth_data.get("asks", [])
        
        # Update depth level widgets
        for i, depth_widget in enumerate(self.depth_levels):
            if i < len(bids) and i < len(asks):
                bid_level = bids[i]
                ask_level = asks[i]
                
                depth_text = (
                    f"L{i+1}: {format_currency(bid_level['price'])} "
                    f"({format_number(bid_level['size'])}) | "
                    f"{format_currency(ask_level['price'])} "
                    f"({format_number(ask_level['size'])})"
                )
                depth_widget.update(depth_text)
            else:
                depth_widget.update(f"Level {i+1}: -")

    def apply_price_change_styling(self, change: Decimal) -> None:
        """Apply color styling based on price change direction."""
        if not self.last_price_label:
            return
            
        # Remove existing styling
        self.last_price_label.remove_class("price-up")
        self.last_price_label.remove_class("price-down")
        self.last_price_label.remove_class("price-unchanged")
        
        # Apply new styling
        if change > 0:
            self.last_price_label.add_class("price-up")
        elif change < 0:
            self.last_price_label.add_class("price-down")
        else:
            self.last_price_label.add_class("price-unchanged")

    def update_status(self, status: str) -> None:
        """Update connection status display."""
        if not self.status_label:
            return
            
        self.status_label.update(status)
        
        # Update status styling
        self.status_label.remove_class("status-connected")
        self.status_label.remove_class("status-disconnected")
        self.status_label.remove_class("status-error")
        
        if "Connected" in status:
            self.status_label.add_class("status-connected")
        elif "Error" in status or "Failed" in status:
            self.status_label.add_class("status-error")
        else:
            self.status_label.add_class("status-disconnected")

    def show_error(self, message: str) -> None:
        """Display error message in the market data panel."""
        if self.bid_ask_label:
            self.bid_ask_label.update(f"Error: {message}")
            
        self.update_status(f"Error: {message}")
        self.clear_secondary_data()

    def clear_market_data(self) -> None:
        """Clear all market data displays to default state."""
        if self.bid_ask_label:
            self.bid_ask_label.update("Bid/Ask: -")
        if self.last_price_label:
            self.last_price_label.update("Last: -")
        if self.volume_label:
            self.volume_label.update("Volume: -")
            
        # Clear depth levels
        for i, depth_widget in enumerate(self.depth_levels):
            depth_widget.update(f"Level {i+1}: -")

    def clear_secondary_data(self) -> None:
        """Clear secondary data while keeping error message visible."""
        if self.last_price_label:
            self.last_price_label.update("Last: -")
        if self.volume_label:
            self.volume_label.update("Volume: -")
            
        # Clear depth levels
        for i, depth_widget in enumerate(self.depth_levels):
            depth_widget.update(f"Level {i+1}: -")