"""
Error handling and messaging system for TUI validation.

This module provides structured error handling, user-friendly error
message formatting, and specialized trading validation exceptions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation messages."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationMessage:
    """
    Structured validation message with severity and context.
    
    Attributes:
        message: Human-readable error message
        severity: Severity level of the message
        field_name: Field that caused the error (if applicable)
        error_code: Machine-readable error code
        context: Additional context for error handling
    """
    message: str
    severity: ValidationSeverity
    field_name: Optional[str] = None
    error_code: Optional[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ValidationException(Exception):
    """
    Base exception for validation errors with structured error information.
    
    Provides detailed error context for debugging and user-friendly
    error message generation.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.field_name = field_name
        self.error_code = error_code
        self.context = context or {}


class TradingValidationError(ValidationException):
    """
    Specialized exception for trading-related validation errors.
    
    Includes trading-specific context like symbol information,
    market status, and regulatory constraints.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        error_code: Optional[str] = None,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        order_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        trading_context = context or {}
        trading_context.update({
            "symbol": symbol,
            "exchange": exchange,
            "order_type": order_type
        })
        
        super().__init__(message, field_name, error_code, trading_context)
        self.symbol = symbol
        self.exchange = exchange
        self.order_type = order_type


# Common trading validation error codes
class TradingErrorCodes:
    """Standard error codes for trading validation."""
    
    # Symbol/Contract errors
    INVALID_SYMBOL = "INVALID_SYMBOL"
    SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND" 
    SYMBOL_NOT_TRADEABLE = "SYMBOL_NOT_TRADEABLE"
    MARKET_CLOSED = "MARKET_CLOSED"
    
    # Price errors
    INVALID_PRICE = "INVALID_PRICE"
    PRICE_OUT_OF_RANGE = "PRICE_OUT_OF_RANGE"
    INVALID_TICK_SIZE = "INVALID_TICK_SIZE"
    
    # Volume errors
    INVALID_VOLUME = "INVALID_VOLUME"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    POSITION_LIMIT_EXCEEDED = "POSITION_LIMIT_EXCEEDED"
    MIN_LOT_SIZE_VIOLATION = "MIN_LOT_SIZE_VIOLATION"
    
    # Order type errors
    INVALID_ORDER_TYPE = "INVALID_ORDER_TYPE"
    ORDER_TYPE_NOT_SUPPORTED = "ORDER_TYPE_NOT_SUPPORTED"
    
    # Account errors
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"


def format_error_message(
    message: str,
    field_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format validation error message for user display.
    
    Args:
        message: Base error message
        field_name: Field that caused the error
        context: Additional context for formatting
        
    Returns:
        Formatted user-friendly error message
    """
    if not field_name:
        return message
    
    # Capitalize field name for display
    display_field = field_name.replace("_", " ").title()
    
    # Add context if available
    if context:
        symbol = context.get("symbol")
        exchange = context.get("exchange")
        
        if symbol and exchange:
            return f"{display_field}: {message} (Symbol: {symbol}.{exchange})"
        elif symbol:
            return f"{display_field}: {message} (Symbol: {symbol})"
    
    return f"{display_field}: {message}"


def format_validation_messages(messages: List[ValidationMessage]) -> List[str]:
    """
    Format list of validation messages for display.
    
    Args:
        messages: List of validation messages
        
    Returns:
        List of formatted error messages
    """
    formatted_messages = []
    
    for msg in messages:
        if msg.severity == ValidationSeverity.ERROR:
            prefix = "❌"
        elif msg.severity == ValidationSeverity.WARNING:
            prefix = "⚠️"
        else:
            prefix = "ℹ️"
        
        formatted_msg = format_error_message(
            msg.message,
            msg.field_name,
            msg.context
        )
        
        formatted_messages.append(f"{prefix} {formatted_msg}")
    
    return formatted_messages


def create_trading_error(
    error_code: str,
    field_name: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    **kwargs
) -> TradingValidationError:
    """
    Create standardized trading validation error.
    
    Args:
        error_code: Standard error code from TradingErrorCodes
        field_name: Field that caused the error
        symbol: Trading symbol
        exchange: Exchange name
        **kwargs: Additional context
        
    Returns:
        TradingValidationError with standardized message
    """
    error_messages = {
        TradingErrorCodes.INVALID_SYMBOL: "Invalid symbol format",
        TradingErrorCodes.SYMBOL_NOT_FOUND: "Symbol not found",
        TradingErrorCodes.SYMBOL_NOT_TRADEABLE: "Symbol is not tradeable",
        TradingErrorCodes.MARKET_CLOSED: "Market is currently closed",
        
        TradingErrorCodes.INVALID_PRICE: "Invalid price format",
        TradingErrorCodes.PRICE_OUT_OF_RANGE: "Price is outside allowed range",
        TradingErrorCodes.INVALID_TICK_SIZE: "Price does not conform to minimum tick size",
        
        TradingErrorCodes.INVALID_VOLUME: "Invalid volume format",
        TradingErrorCodes.INSUFFICIENT_FUNDS: "Insufficient funds for this order",
        TradingErrorCodes.POSITION_LIMIT_EXCEEDED: "Order would exceed position limits",
        TradingErrorCodes.MIN_LOT_SIZE_VIOLATION: "Volume is below minimum lot size",
        
        TradingErrorCodes.INVALID_ORDER_TYPE: "Invalid order type",
        TradingErrorCodes.ORDER_TYPE_NOT_SUPPORTED: "Order type not supported for this symbol",
        
        TradingErrorCodes.ACCOUNT_NOT_FOUND: "Trading account not found",
        TradingErrorCodes.INSUFFICIENT_PERMISSIONS: "Insufficient trading permissions",
        TradingErrorCodes.ACCOUNT_SUSPENDED: "Trading account is suspended"
    }
    
    message = error_messages.get(error_code, f"Trading validation error: {error_code}")
    
    return TradingValidationError(
        message=message,
        field_name=field_name,
        error_code=error_code,
        symbol=symbol,
        exchange=exchange,
        context=kwargs
    )


class ValidationErrorCollector:
    """
    Utility class to collect and format validation errors.
    
    Provides a convenient way to accumulate validation errors
    from multiple sources and format them for display.
    """
    
    def __init__(self):
        self.messages: List[ValidationMessage] = []
    
    def add_error(
        self,
        message: str,
        field_name: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an error message."""
        self.messages.append(ValidationMessage(
            message=message,
            severity=ValidationSeverity.ERROR,
            field_name=field_name,
            error_code=error_code,
            context=context
        ))
    
    def add_warning(
        self,
        message: str,
        field_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a warning message."""
        self.messages.append(ValidationMessage(
            message=message,
            severity=ValidationSeverity.WARNING,
            field_name=field_name,
            context=context
        ))
    
    def add_info(
        self,
        message: str,
        field_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an info message."""
        self.messages.append(ValidationMessage(
            message=message,
            severity=ValidationSeverity.INFO,
            field_name=field_name,
            context=context
        ))
    
    def has_errors(self) -> bool:
        """Check if any error messages exist."""
        return any(msg.severity == ValidationSeverity.ERROR for msg in self.messages)
    
    def has_warnings(self) -> bool:
        """Check if any warning messages exist."""
        return any(msg.severity == ValidationSeverity.WARNING for msg in self.messages)
    
    def get_error_messages(self) -> List[str]:
        """Get formatted error messages."""
        error_messages = [
            msg for msg in self.messages 
            if msg.severity == ValidationSeverity.ERROR
        ]
        return format_validation_messages(error_messages)
    
    def get_warning_messages(self) -> List[str]:
        """Get formatted warning messages."""
        warning_messages = [
            msg for msg in self.messages 
            if msg.severity == ValidationSeverity.WARNING
        ]
        return format_validation_messages(warning_messages)
    
    def get_all_messages(self) -> List[str]:
        """Get all formatted messages."""
        return format_validation_messages(self.messages)
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()