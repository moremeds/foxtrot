"""
Validation utility functions for the Foxtrot TUI.

This module provides common validation utilities that can be reused
across different validators and components.
"""

from decimal import Decimal, InvalidOperation
import re
import string
from typing import Any


def validate_numeric_range(
    value: str | int | float | Decimal,
    min_value: int | float | Decimal | None = None,
    max_value: int | float | Decimal | None = None,
    decimal_places: int | None = None
) -> tuple[bool, Decimal | None, str | None]:
    """
    Validate numeric value within specified range and precision.

    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        decimal_places: Maximum allowed decimal places

    Returns:
        Tuple of (is_valid, decimal_value, error_message)
    """
    try:
        if isinstance(value, str):
            value = value.strip()
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False, None, "Must be a valid number"

    # Check range
    if min_value is not None and decimal_value < Decimal(str(min_value)):
        return False, None, f"Must be at least {min_value}"

    if max_value is not None and decimal_value > Decimal(str(max_value)):
        return False, None, f"Must be at most {max_value}"

    # Check decimal places
    if decimal_places is not None and decimal_value.as_tuple().exponent < -decimal_places:
        return False, None, f"Cannot have more than {decimal_places} decimal places"

    return True, decimal_value, None


def validate_symbol_format(symbol: str, exchange: str | None = None) -> tuple[bool, str | None]:
    """
    Validate trading symbol format.

    Supports formats like:
    - "AAPL" (simple symbol)
    - "AAPL.SMART" (symbol with exchange)
    - "BTC-USD" (crypto pair)
    - "ES2212" (futures contract)

    Args:
        symbol: Symbol to validate
        exchange: Optional exchange to validate against

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symbol or not isinstance(symbol, str):
        return False, "Symbol cannot be empty"

    symbol = symbol.strip().upper()

    # Basic symbol format validation
    if not symbol:
        return False, "Symbol cannot be empty"

    # Check for valid characters (alphanumeric, dash, dot, underscore)
    if not re.match(r'^[A-Z0-9._-]+$', symbol):
        return False, "Symbol contains invalid characters"

    # Check length constraints
    if len(symbol) < 1:
        return False, "Symbol too short"

    if len(symbol) > 20:
        return False, "Symbol too long (max 20 characters)"

    # Split on dot if exchange is included
    symbol_parts = symbol.split('.')
    if len(symbol_parts) > 2:
        return False, "Invalid symbol format (too many dots)"

    if len(symbol_parts) == 2:
        symbol_part, exchange_part = symbol_parts
        if not symbol_part or not exchange_part:
            return False, "Invalid symbol.exchange format"

        # Validate exchange part if provided
        if exchange and exchange.upper() != exchange_part:
            return False, f"Exchange mismatch: expected {exchange}, got {exchange_part}"

    return True, None


def validate_price_precision(
    price: str | float | Decimal,
    tick_size: Decimal | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None
) -> tuple[bool, Decimal | None, str | None]:
    """
    Validate price with tick size and range constraints.

    Args:
        price: Price to validate
        tick_size: Minimum price increment (e.g., 0.01 for stocks)
        min_price: Minimum allowed price
        max_price: Maximum allowed price

    Returns:
        Tuple of (is_valid, decimal_price, error_message)
    """
    # First validate as numeric
    is_valid, decimal_price, error = validate_numeric_range(
        price, min_price, max_price
    )

    if not is_valid:
        return is_valid, decimal_price, error

    # Check tick size if provided
    if tick_size is not None and tick_size > 0:
        remainder = decimal_price % tick_size
        if remainder != 0:
            # Calculate nearest valid prices
            lower_price = decimal_price - remainder
            higher_price = lower_price + tick_size

            return False, None, f"Price must be in increments of {tick_size} (nearest: {lower_price} or {higher_price})"

    return True, decimal_price, None


def sanitize_input(value: Any, max_length: int | None = None) -> str:
    """
    Sanitize user input for safe processing.

    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string value
    """
    if value is None:
        return ""

    # Convert to string and strip whitespace
    sanitized = str(value).strip()

    # Remove control characters except common whitespace
    sanitized = ''.join(
        char for char in sanitized
        if char in string.printable and char not in string.digits[10:]
    )

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_positive_integer(value: Any) -> tuple[bool, int | None, str | None]:
    """
    Validate value is a positive integer.

    Args:
        value: Value to validate

    Returns:
        Tuple of (is_valid, integer_value, error_message)
    """
    try:
        if isinstance(value, str):
            value = value.strip()

        # Try to convert to integer
        int_value = int(value)

        if int_value <= 0:
            return False, None, "Must be a positive integer"

        return True, int_value, None

    except (ValueError, TypeError):
        return False, None, "Must be a valid integer"


def validate_percentage(value: Any) -> tuple[bool, Decimal | None, str | None]:
    """
    Validate percentage value (0-100).

    Args:
        value: Value to validate

    Returns:
        Tuple of (is_valid, decimal_value, error_message)
    """
    return validate_numeric_range(value, min_value=0, max_value=100, decimal_places=2)


def format_currency(amount: Decimal | float, currency: str = "USD") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))

    # Format with 2 decimal places
    formatted = f"{amount:.2f}"

    return f"{formatted} {currency}"


def parse_symbol_exchange(symbol_str: str) -> tuple[str, str | None]:
    """
    Parse symbol string into symbol and exchange components.

    Args:
        symbol_str: Symbol string (e.g., "AAPL.SMART" or "AAPL")

    Returns:
        Tuple of (symbol, exchange) where exchange may be None
    """
    if not symbol_str:
        return "", None

    parts = symbol_str.strip().upper().split('.')

    if len(parts) == 1:
        return parts[0], None
    if len(parts) == 2:
        return parts[0], parts[1]
    # Take first two parts if multiple dots
    return parts[0], parts[1]


def validate_order_quantity(
    quantity: Any,
    min_lot_size: Decimal | None = None,
    lot_size_increment: Decimal | None = None
) -> tuple[bool, Decimal | None, str | None]:
    """
    Validate order quantity with lot size constraints.

    Args:
        quantity: Quantity to validate
        min_lot_size: Minimum lot size
        lot_size_increment: Lot size increment

    Returns:
        Tuple of (is_valid, decimal_quantity, error_message)
    """
    # Validate as positive number
    is_valid, decimal_quantity, error = validate_numeric_range(
        quantity, min_value=0
    )

    if not is_valid:
        return is_valid, decimal_quantity, error

    if decimal_quantity == 0:
        return False, None, "Quantity must be greater than zero"

    # Check minimum lot size
    if min_lot_size is not None and decimal_quantity < min_lot_size:
        return False, None, f"Quantity must be at least {min_lot_size}"

    # Check lot size increment
    if lot_size_increment is not None and lot_size_increment > 0:
        remainder = decimal_quantity % lot_size_increment
        if remainder != 0:
            nearest_valid = decimal_quantity - remainder
            if nearest_valid < (min_lot_size or Decimal('0')):
                nearest_valid += lot_size_increment

            return False, None, f"Quantity must be in increments of {lot_size_increment} (nearest: {nearest_valid})"

    return True, decimal_quantity, None


def is_market_hours(exchange: str) -> bool:
    """
    Check if market is currently open for trading.

    This is a simplified implementation - in practice, this would
    integrate with real market hours data.

    Args:
        exchange: Exchange identifier

    Returns:
        True if market is open, False otherwise
    """
    # Simplified implementation - always return True for now
    # In practice, this would check actual market hours
    return True


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol format for consistent processing.

    Args:
        symbol: Raw symbol string

    Returns:
        Normalized symbol string
    """
    if not symbol:
        return ""

    # Convert to uppercase and strip whitespace
    normalized = symbol.strip().upper()

    # Remove any extra whitespace within the symbol
    return re.sub(r'\s+', '', normalized)
