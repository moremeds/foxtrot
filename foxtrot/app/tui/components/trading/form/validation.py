"""
Form validation logic and cross-field validation rules.

This module handles all validation operations for trading forms,
including individual field validation and cross-field business rules.
"""

from typing import Any, Dict, Optional
import logging

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

# Set up logging
logger = logging.getLogger(__name__)


class TradingFormValidator:
    """
    Centralized validation logic for trading forms.
    
    Features:
    - Individual field validation
    - Cross-field validation rules
    - Business logic validation
    - Error collection and management
    """
    
    def __init__(self):
        """Initialize all validators."""
        # Individual field validators
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
        
        # Error collection
        self.validation_errors = ValidationErrorCollector()
    
    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Validate individual field value.
        
        Args:
            field_name: Name of the field to validate
            value: Field value to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        validator = self._form_validators.get(field_name)
        if not validator:
            logger.warning(f"No validator found for field: {field_name}")
            return ValidationResult(is_valid=True)
        
        return validator.validate(value)
    
    def validate_price_required(self, data: Dict[str, Any]) -> ValidationResult:
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
    
    def validate_sufficient_funds(self, data: Dict[str, Any]) -> ValidationResult:
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
    
    def validate_all_fields(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate all form fields and cross-field rules.
        
        Args:
            data: Form data dictionary
            
        Returns:
            ValidationResult with overall validation status
        """
        self.validation_errors.clear()
        
        # Validate individual fields
        for field_name, value in data.items():
            result = self.validate_field(field_name, value)
            if not result.is_valid:
                self.validation_errors.add_errors(result.errors)
        
        # Validate cross-field rules
        price_result = self.validate_price_required(data)
        if not price_result.is_valid:
            self.validation_errors.add_errors(price_result.errors)
        
        funds_result = self.validate_sufficient_funds(data)
        if not funds_result.is_valid:
            self.validation_errors.add_errors(funds_result.errors)
        
        return ValidationResult(
            is_valid=not self.validation_errors.has_errors(),
            errors=self.validation_errors.get_all_errors()
        )
    
    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return self.validation_errors.has_errors()
    
    def get_validation_errors(self) -> list[str]:
        """Get all current validation errors."""
        return self.validation_errors.get_all_errors()
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()