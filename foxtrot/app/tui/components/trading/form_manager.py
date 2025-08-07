"""
Trading form state management and validation logic.

This module handles all form-related state management, validation,
and UI updates for the trading interface.
"""

from typing import Any, Dict, Optional
import logging
from decimal import Decimal

from textual.widgets import Input, Select, RadioSet, Button, Static

from foxtrot.app.tui.validation import (
    DirectionValidator,
    FormValidator,
    OrderTypeValidator,
    PriceValidator,
    SymbolValidator,
    ValidationErrorCollector,
    ValidationResult,
    VolumeValidator,
)
from .common import TradingConstants, TradingFormData
from .input_widgets import SymbolInput

# Set up logging
logger = logging.getLogger(__name__)


class TradingFormManager:
    """
    Manages form state, validation, and UI state for trading panel.
    
    Features:
    - Complete form validation with cross-field rules
    - Real-time UI state management
    - Error collection and display
    - Form data extraction and validation
    - Input state management based on order type
    
    This class encapsulates all form-related logic to maintain
    single responsibility and improve testability.
    """
    
    def __init__(self):
        # Validators
        self.form_validator = FormValidator()
        self.symbol_validator = SymbolValidator()
        self.price_validator = PriceValidator()
        self.volume_validator = VolumeValidator()
        self.order_type_validator = OrderTypeValidator()
        self.direction_validator = DirectionValidator()
        
        # Form validators dictionary for easy access
        self._form_validators = {
            'symbol': self.symbol_validator,
            'price': self.price_validator,
            'volume': self.volume_validator,
            'order_type': self.order_type_validator,
            'direction': self.direction_validator
        }
        
        # Form state
        self.current_contract_info = None
        self.validation_errors = ValidationErrorCollector()
        
        # UI Component references (set by main trading panel)
        self.symbol_input: Optional[SymbolInput] = None
        self.exchange_select: Optional[Select] = None
        self.direction_radio: Optional[RadioSet] = None
        self.order_type_select: Optional[Select] = None
        self.price_input: Optional[Input] = None
        self.volume_input: Optional[Input] = None
        self.submit_button: Optional[Button] = None
        self.error_display: Optional[Static] = None
    
    def set_ui_components(
        self,
        symbol_input: SymbolInput,
        exchange_select: Select,
        direction_radio: RadioSet,
        order_type_select: Select,
        price_input: Input,
        volume_input: Input,
        submit_button: Button,
        error_display: Static
    ) -> None:
        """Set UI component references for form management."""
        self.symbol_input = symbol_input
        self.exchange_select = exchange_select
        self.direction_radio = direction_radio
        self.order_type_select = order_type_select
        self.price_input = price_input
        self.volume_input = volume_input
        self.submit_button = submit_button
        self.error_display = error_display
    
    async def setup_validation(self) -> None:
        """Set up form validators and validation rules."""
        self.form_validator.add_field_validator("symbol", self.symbol_validator)
        self.form_validator.add_field_validator("price", self.price_validator)
        self.form_validator.add_field_validator("volume", self.volume_validator)
        self.form_validator.add_field_validator("order_type", self.order_type_validator)
        self.form_validator.add_field_validator("direction", self.direction_validator)
        
        # Add cross-field validation rules
        self.form_validator.add_cross_field_rule(self._validate_price_required)
        self.form_validator.add_cross_field_rule(self._validate_sufficient_funds)
    
    async def validate_form(self) -> bool:
        """
        Validate the entire form and return validation status.
        
        Returns:
            True if form is valid, False otherwise
            
        Note:
            This method performs comprehensive validation including
            individual field validation and cross-field business rules.
        """
        try:
            # Clear previous errors
            self.validation_errors.clear_errors()
            
            # Get current form data
            form_data = await self.get_form_data()
            
            # Perform comprehensive validation
            validation_result = await self.form_validator.validate_form(form_data)
            
            # Collect any validation errors
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    self.validation_errors.add_error("form", error)
            
            # Update error display
            await self.update_error_display()
            
            # Update UI state based on validation
            await self.update_ui_state()
            
            return validation_result.is_valid
            
        except Exception as e:
            logger.error(f"Form validation error: {e}")
            self.validation_errors.add_error("system", "Validation error occurred")
            await self.update_error_display()
            return False
    
    def _validate_price_required(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Cross-field validation: Price required for limit orders.
        
        Args:
            data: Form data dictionary
            
        Returns:
            ValidationResult indicating if price requirement is satisfied
        """
        order_type = data.get("order_type", "")
        price = data.get("price", "")
        
        if order_type in ["LIMIT", "STOP_LIMIT"] and not price.strip():
            return ValidationResult(
                is_valid=False,
                errors=["Price is required for limit orders"]
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_sufficient_funds(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Cross-field validation: Check sufficient funds for order.
        
        Args:
            data: Form data dictionary
            
        Returns:
            ValidationResult indicating if funds are sufficient
            
        Note:
            In production, this would integrate with account management
            to verify real-time account balance and buying power.
        """
        # TODO: Integrate with real account balance checking
        # For now, assume sufficient funds (mock validation)
        return ValidationResult(is_valid=True)
    
    async def get_form_data(self) -> Dict[str, Any]:
        """
        Extract current form data from UI components.
        
        Returns:
            Dictionary containing all form field values
            
        Raises:
            ValueError: If required UI components are not initialized
        """
        if not all([self.symbol_input, self.direction_radio, 
                   self.order_type_select, self.volume_input]):
            raise ValueError("UI components not properly initialized")
        
        # Get symbol and exchange
        symbol = self.symbol_input.value.strip().upper() if self.symbol_input.value else ""
        exchange = ""
        if self.exchange_select and hasattr(self.exchange_select, 'value'):
            exchange = str(self.exchange_select.value)
        
        # Get direction
        direction = "BUY"  # Default
        if self.direction_radio.pressed:
            direction = str(self.direction_radio.pressed.label).upper()
        
        # Get order type
        order_type = "MARKET"  # Default
        if self.order_type_select.value:
            order_type = str(self.order_type_select.value)
        
        # Get price (only for limit orders)
        price_str = ""
        if self.price_input and self.price_input.value:
            price_str = self.price_input.value.strip()
        
        # Get volume
        volume_str = ""
        if self.volume_input and self.volume_input.value:
            volume_str = self.volume_input.value.strip()
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "direction": direction,
            "order_type": order_type,
            "price": price_str,
            "volume": volume_str
        }
    
    async def update_ui_state(self) -> None:
        """Update UI state based on current form values and validation."""
        await self._update_price_input_state()
        await self._update_submit_button_state()
    
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
    
    async def _update_submit_button_state(self) -> None:
        """Enable/disable submit button based on form validation."""
        if not self.submit_button:
            return
            
        # Quick validation check for button state
        form_data = await self.get_form_data()
        has_required_fields = (
            form_data.get("symbol", "").strip() and 
            form_data.get("volume", "").strip()
        )
        
        self.submit_button.disabled = not has_required_fields
    
    async def update_error_display(self) -> None:
        """Update error display with current validation errors."""
        if not self.error_display:
            return
        
        errors = self.validation_errors.get_all_errors()
        
        if errors:
            # Show first few errors to avoid overwhelming UI
            max_errors = 3
            error_messages = errors[:max_errors]
            error_text = "; ".join(error_messages)
            
            if len(errors) > max_errors:
                error_text += f" (and {len(errors) - max_errors} more)"
                
            self.error_display.update(f"⚠️ {error_text}")
            self.error_display.add_class("error-visible")
        else:
            self.error_display.update("")
            self.error_display.remove_class("error-visible")
    
    async def reset_form(self) -> None:
        """Reset form to default state."""
        if self.symbol_input:
            self.symbol_input.value = ""
            
        if self.exchange_select:
            # Reset to first option or default
            pass  # Exchange select handling
            
        if self.direction_radio:
            # Reset to BUY (first option)
            self.direction_radio.pressed = None
            
        if self.order_type_select:
            self.order_type_select.value = "MARKET"
            
        if self.price_input:
            self.price_input.value = ""
            
        if self.volume_input:
            self.volume_input.value = ""
        
        # Clear validation errors and update UI
        self.validation_errors.clear_errors()
        await self.update_error_display()
        await self.update_ui_state()
    
    def create_form_data_object(self, form_data: Dict[str, Any]) -> TradingFormData:
        """
        Create a TradingFormData object from form data dictionary.
        
        Args:
            form_data: Raw form data dictionary
            
        Returns:
            TradingFormData object with validated and converted values
        """
        # Convert price and volume to Decimal if provided
        price = None
        if form_data.get("price", "").strip():
            try:
                price = Decimal(form_data["price"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid price format: {form_data.get('price')}")
        
        volume = None
        if form_data.get("volume", "").strip():
            try:
                volume = Decimal(form_data["volume"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid volume format: {form_data.get('volume')}")
        
        return TradingFormData(
            symbol=form_data.get("symbol", ""),
            exchange=form_data.get("exchange", ""),
            direction=form_data.get("direction", TradingConstants.DEFAULT_DIRECTION),
            order_type=form_data.get("order_type", TradingConstants.DEFAULT_ORDER_TYPE),
            price=price,
            volume=volume
        )
    
    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return self.validation_errors.has_errors()
    
    def get_validation_errors(self) -> list[str]:
        """Get all current validation errors."""
        return self.validation_errors.get_all_errors()
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear_errors()