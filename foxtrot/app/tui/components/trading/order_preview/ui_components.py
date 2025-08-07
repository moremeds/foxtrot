"""
Order preview UI components and display management.

This module handles all UI rendering, styling, and display updates
for the order preview panel.
"""

from typing import Any, Dict, Optional
from textual.containers import Vertical
from textual.widgets import Static

from foxtrot.app.tui.utils.formatters import format_currency


class OrderPreviewUIManager:
    """
    Manages UI components and display updates for order preview.
    
    This class contains only presentation logic with no business
    calculations or data processing.
    """

    def __init__(self):
        # UI component references
        self.order_value_label: Optional[Static] = None
        self.funds_check_label: Optional[Static] = None
        self.commission_label: Optional[Static] = None
        self.risk_label: Optional[Static] = None

    def compose(self):
        """Create the preview panel layout with styled components."""
        with Vertical(classes="order-preview"):
            yield Static("Order Preview", classes="preview-title")

            with Vertical(classes="preview-content"):
                self.order_value_label = Static(
                    "Order Value: -", 
                    classes="preview-item"
                )
                yield self.order_value_label

                self.funds_check_label = Static(
                    "Available Funds: -", 
                    classes="preview-item"
                )
                yield self.funds_check_label

                self.commission_label = Static(
                    "Est. Commission: -", 
                    classes="preview-item"
                )
                yield self.commission_label

                self.risk_label = Static(
                    "Position Impact: -", 
                    classes="preview-item"
                )
                yield self.risk_label

    async def update_display_with_calculations(
        self, 
        calculations: Dict[str, Any]
    ) -> None:
        """
        Update all display components with calculated values.
        
        Args:
            calculations: Dictionary containing calculated values
        """
        # Update order value
        if self.order_value_label:
            order_value = calculations["order_value"]
            self.order_value_label.update(
                f"Order Value: {format_currency(order_value)}"
            )

        # Update commission
        if self.commission_label:
            commission = calculations["commission"]
            self.commission_label.update(
                f"Est. Commission: {format_currency(commission)}"
            )

        # Update funds check with status indicator
        await self.update_funds_display(calculations)

        # Update position impact
        if self.risk_label:
            impact = calculations["position_impact"]
            self.risk_label.update(f"Impact: {impact}")

    async def update_funds_display(self, calculations: Dict[str, Any]) -> None:
        """
        Update funds display with availability check and visual indicators.
        
        Args:
            calculations: Dictionary containing calculated values
        """
        if not self.funds_check_label:
            return
            
        available_funds = calculations.get("available_funds")
        
        if available_funds is None:
            self.funds_check_label.update("Available: Checking...")
            return
            
        total_cost = calculations["total_cost"]
        sufficient_funds = available_funds >= total_cost
        status_icon = "✓" if sufficient_funds else "✗"
        
        # Update display with status
        self.funds_check_label.update(
            f"Available: {format_currency(available_funds)} {status_icon}"
        )
        
        # Apply appropriate styling
        if sufficient_funds:
            self.funds_check_label.remove_class("insufficient-funds")
            self.funds_check_label.add_class("sufficient-funds")
        else:
            self.funds_check_label.remove_class("sufficient-funds")
            self.funds_check_label.add_class("insufficient-funds")

    def show_calculation_error(self, message: str) -> None:
        """Display calculation error in the preview."""
        if self.order_value_label:
            self.order_value_label.update(f"Error: {message}")
            
        # Clear other fields to avoid confusion
        self.clear_other_fields()

    def show_price_unavailable(self) -> None:
        """Display message when market price is unavailable."""
        if self.order_value_label:
            self.order_value_label.update("Market price unavailable")
            
        self.clear_other_fields()

    def clear_preview(self) -> None:
        """Clear all preview values to default state."""
        if self.order_value_label:
            self.order_value_label.update("Order Value: -")
        if self.funds_check_label:
            self.funds_check_label.update("Available Funds: -")
        if self.commission_label:
            self.commission_label.update("Est. Commission: -")
        if self.risk_label:
            self.risk_label.update("Position Impact: -")

    def clear_other_fields(self) -> None:
        """Clear secondary fields while keeping error message visible."""
        if self.funds_check_label:
            self.funds_check_label.update("Available Funds: -")
        if self.commission_label:
            self.commission_label.update("Est. Commission: -")
        if self.risk_label:
            self.risk_label.update("Position Impact: -")