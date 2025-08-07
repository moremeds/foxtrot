"""
Trading form controller that orchestrates all modular components.

This module provides the main TradingFormManager class that coordinates
all specialized components while maintaining backward compatibility.
"""

from typing import Any, Dict, Optional
import logging

from textual.widgets import Input, Select, RadioSet, Button, Static

from foxtrot.app.tui.components.trading.common import TradingFormData
from foxtrot.app.tui.components.trading.input_widgets import SymbolInput

from .validation import TradingFormValidator
from .data_binding import TradingFormDataBinder
from .ui_manager import TradingFormUIManager

# Set up logging
logger = logging.getLogger(__name__)


class TradingFormManager:
    """
    Main form controller that orchestrates all modular components.
    
    This class maintains the original interface while using the new modular
    architecture internally. It coordinates between:
    - Validation logic and cross-field rules
    - Data extraction and binding
    - UI component state management
    """
    
    def __init__(self):
        """Initialize form manager with all modular components."""
        # Initialize modular components
        self.validator = TradingFormValidator()
        self.data_binder = TradingFormDataBinder()
        self.ui_manager = TradingFormUIManager()
        
        logger.info("Trading form manager initialized with modular architecture")
    
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
        Set references to all UI components across modular components.
        
        This method distributes UI component references to all specialized
        components that need them for their specific responsibilities.
        
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
        # Set UI components for data binding
        self.data_binder.set_ui_components(
            symbol_input, exchange_select, direction_radio,
            order_type_select, price_input, volume_input
        )
        
        # Set UI components for UI management
        self.ui_manager.set_ui_components(
            symbol_input, exchange_select, direction_radio,
            order_type_select, price_input, volume_input,
            submit_button, error_display
        )
    
    async def get_form_data(self) -> Dict[str, Any]:
        """
        Extract current form data from UI components.
        
        Returns:
            Dictionary containing all form field values
            
        Raises:
            ValueError: If required UI components are not initialized
        """
        return await self.data_binder.get_form_data()
    
    async def validate_form(self, form_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate form data and update UI accordingly.
        
        Args:
            form_data: Optional pre-extracted form data
            
        Returns:
            True if form is valid, False otherwise
        """
        if form_data is None:
            form_data = await self.get_form_data()
        
        # Validate using the validator component
        validation_result = self.validator.validate_all_fields(form_data)
        
        # Update error display through UI manager
        errors = validation_result.errors if not validation_result.is_valid else None
        await self.ui_manager.update_error_display(errors)
        
        return validation_result.is_valid
    
    async def update_ui_state(self) -> None:
        """Update UI state based on current form values and validation."""
        form_data = await self.get_form_data()
        await self.ui_manager.update_ui_state(form_data)
    
    async def update_error_display(self) -> None:
        """Update error display with current validation errors."""
        errors = self.validator.get_validation_errors() if self.validator.has_validation_errors() else None
        await self.ui_manager.update_error_display(errors)
    
    def create_form_data_object(self, form_data: Dict[str, Any]) -> TradingFormData:
        """
        Create a TradingFormData object from form data dictionary.
        
        Args:
            form_data: Raw form data dictionary
            
        Returns:
            TradingFormData object with validated and converted values
        """
        return self.data_binder.create_form_data_object(form_data)
    
    # Backward compatibility methods (delegate to appropriate components)
    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return self.validator.has_validation_errors()
    
    def get_validation_errors(self) -> list[str]:
        """Get all current validation errors."""
        return self.validator.get_validation_errors()
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validator.clear_validation_errors()
    
    # Additional methods for backward compatibility and extended functionality
    async def set_contract_info(self, contract_info: Any) -> None:
        """Set current contract information."""
        await self.ui_manager.set_contract_info(contract_info)
    
    def get_contract_info(self) -> Any:
        """Get current contract information."""
        return self.ui_manager.get_contract_info()
    
    async def reset_form(self) -> None:
        """Reset form to default state."""
        await self.ui_manager.reset_form_ui()
        self.validator.clear_validation_errors()
    
    def get_components(self) -> Dict[str, Any]:
        """
        Get references to modular components for advanced usage.
        
        Returns:
            Dictionary containing modular component instances
        """
        return {
            "validator": self.validator,
            "data_binder": self.data_binder,
            "ui_manager": self.ui_manager,
        }