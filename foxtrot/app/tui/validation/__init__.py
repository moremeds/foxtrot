"""
TUI Validation Framework

This module provides a comprehensive validation system for the Foxtrot TUI,
with specialized support for trading operations and real-time data validation.

Core Components:
- FieldValidator: Base validation for individual fields
- FormValidator: Multi-field validation with cross-field rules
- ValidationResult: Structured validation outcomes
- ValidatorChain: Sequential validation pipeline

Trading Validators:
- PriceValidator: Price format and market-specific validation
- VolumeValidator: Position size and fund availability validation
- SymbolValidator: Contract existence and trading permissions
- OrderTypeValidator: Valid order types for symbol/exchange pairs

Usage:
    from foxtrot.app.tui.validation import (
        FieldValidator, FormValidator, ValidationResult,
        PriceValidator, VolumeValidator, SymbolValidator
    )
"""

from .base import (
    FieldValidator,
    FormValidator,
    ValidationResult,
    ValidatorChain,
    ValidationError
)

from .trading import (
    PriceValidator,
    VolumeValidator,
    SymbolValidator,
    OrderTypeValidator,
    DirectionValidator,
    ExchangeValidator
)

from .errors import (
    ValidationException,
    TradingValidationError,
    ValidationErrorCollector,
    format_error_message
)

from .utils import (
    validate_numeric_range,
    validate_symbol_format,
    validate_price_precision,
    sanitize_input
)

__all__ = [
    # Base validation
    "FieldValidator",
    "FormValidator", 
    "ValidationResult",
    "ValidatorChain",
    "ValidationError",
    
    # Trading validators
    "PriceValidator",
    "VolumeValidator",
    "SymbolValidator",
    "OrderTypeValidator",
    "DirectionValidator",
    "ExchangeValidator",
    
    # Error handling
    "ValidationException",
    "TradingValidationError",
    "ValidationErrorCollector",
    "format_error_message",
    
    # Utilities
    "validate_numeric_range",
    "validate_symbol_format",
    "validate_price_precision",
    "sanitize_input"
]