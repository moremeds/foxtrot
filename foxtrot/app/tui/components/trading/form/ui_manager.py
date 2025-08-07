"""
Form UI component management and state updates.

This module handles UI component state management, interaction updates,
and visual feedback for form validation and user actions.
"""

from typing import Any, Dict, Optional
import logging

from textual.widgets import Input, Select, RadioSet, Button, Static

from foxtrot.app.tui.components.trading.input_widgets import SymbolInput

# Set up logging
logger = logging.getLogger(__name__)


class TradingFormUIManager:
    """
    Manages UI component state and interactions for trading forms.
    
    Features:
    - UI component reference management
    - Dynamic UI state updates
    - Input field enable/disable logic
    - Button state management
    - Error display handling
    """
    
    def __init__(self):
        """Initialize UI manager."""
        # UI Component references (set by main trading panel)
        self.symbol_input: Optional[SymbolInput] = None
        self.exchange_select: Optional[Select] = None
        self.direction_radio: Optional[RadioSet] = None
        self.order_type_select: Optional[Select] = None
        self.price_input: Optional[Input] = None
        self.volume_input: Optional[Input] = None
        self.submit_button: Optional[Button] = None
        self.error_display: Optional[Static] = None
        
        # Form state
        self.current_contract_info = None
    
    def set_ui_components(
        self,
        symbol_input: SymbolInput,
        exchange_select: Select,
        direction_radio: RadioSet,
        order_type_select: Select,
        price_input: Input,
        volume_input: Input,
        submit_button: Button,
        error_display: Static,
    ) -> None:
        """
        Set references to all UI components.
        
        This method is called by the main trading panel to provide
        access to all form UI components for state management.
        
        Args:
            symbol_input: Symbol input widget
            exchange_select: Exchange selection widget
            direction_radio: Direction radio button set
            order_type_select: Order type selection widget
            price_input: Price input widget
            volume_input: Volume input widget
            submit_button: Form submit button
            error_display: Error message display widget
        """
        self.symbol_input = symbol_input
        self.exchange_select = exchange_select
        self.direction_radio = direction_radio
        self.order_type_select = order_type_select
        self.price_input = price_input
        self.volume_input = volume_input
        self.submit_button = submit_button
        self.error_display = error_display
    
    async def update_ui_state(self, form_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Update UI state based on current form values and validation.
        
        Args:
            form_data: Optional form data for state decisions
        """
        await self._update_price_input_state()
        await self._update_submit_button_state(form_data)
    
    async def _update_price_input_state(self) -> None:
        """Enable/disable price input based on order type."""
        if not self.order_type_select or not self.price_input:
            return
            
        order_type = self.order_type_select.value
        
        # Enable price input for limit orders, disable for market orders
        if order_type in ["LIMIT", "STOP", "STOP_LIMIT"]:
            self.price_input.disabled = False
            self.price_input.placeholder = "Enter price"
        else:
            self.price_input.disabled = True
            self.price_input.placeholder = "Price not required for market orders"
            self.price_input.value = ""
    
    async def _update_submit_button_state(self, form_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Enable/disable submit button based on form validation.
        
        Args:
            form_data: Optional pre-extracted form data
        """
        if not self.submit_button:
            return
        
        # Quick validation check for button state
        if form_data is None:
            # If no form data provided, we can't validate, so disable
            self.submit_button.disabled = True
            return
        
        has_required_fields = (
            form_data.get("symbol", "").strip() and 
            form_data.get("volume", "").strip()
        )
        
        # Enable button only if basic required fields are present
        self.submit_button.disabled = not has_required_fields
    
    async def update_error_display(self, errors: Optional[list[str]] = None) -> None:
        """
        Update error display with validation errors.
        
        Args:
            errors: List of error messages to display, or None to clear
        """
        if not self.error_display:
            return
        
        if errors and len(errors) > 0:
            # Show first error (or combine multiple errors)
            error_message = errors[0] if len(errors) == 1 else f"{len(errors)} validation errors"
            self.error_display.update(error_message)
            self.error_display.add_class("error")
        else:
            # Clear error display
            self.error_display.update("")
            self.error_display.remove_class("error")
    
    async def set_contract_info(self, contract_info: Any) -> None:
        """
        Set current contract information and update related UI.
        
        Args:
            contract_info: Contract information object
        """
        self.current_contract_info = contract_info
        # Could update exchange select or other UI based on contract
    
    def get_contract_info(self) -> Any:
        """Get current contract information."""
        return self.current_contract_info
    
    async def reset_form_ui(self) -> None:
        """Reset all form UI components to their default states."""
        if self.symbol_input:
            self.symbol_input.value = ""
        if self.price_input:
            self.price_input.value = ""
            self.price_input.disabled = True
        if self.volume_input:
            self.volume_input.value = ""
        if self.submit_button:
            self.submit_button.disabled = True
        
        await self.update_error_display()
    
    def get_ui_components(self) -> Dict[str, Any]:
        """
        Get dictionary of UI component references.
        
        Returns:
            Dictionary mapping component names to widget instances
        """
        return {
            "symbol_input": self.symbol_input,
            "exchange_select": self.exchange_select,
            "direction_radio": self.direction_radio,
            "order_type_select": self.order_type_select,
            "price_input": self.price_input,
            "volume_input": self.volume_input,
            "submit_button": self.submit_button,
            "error_display": self.error_display,
        }