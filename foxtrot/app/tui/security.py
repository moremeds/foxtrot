"""
Security-Aware Error Handling System for Foxtrot TUI

This module provides secure error handling that prevents information disclosure
and injection attacks through exception messages and user input.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import re
import traceback
from typing import Any

logger = logging.getLogger(__name__)


class SecurityErrorCode(Enum):
    """Secure error codes that don't expose sensitive information."""

    # Validation errors
    INVALID_SYMBOL = "VALIDATION_001"
    INVALID_PRICE = "VALIDATION_002"
    INVALID_VOLUME = "VALIDATION_003"
    INVALID_ORDER_TYPE = "VALIDATION_004"
    INVALID_DIRECTION = "VALIDATION_005"

    # System errors
    SYSTEM_UNAVAILABLE = "SYSTEM_001"
    NETWORK_ERROR = "SYSTEM_002"
    TIMEOUT_ERROR = "SYSTEM_003"
    CONFIGURATION_ERROR = "SYSTEM_004"

    # Trading errors
    INSUFFICIENT_FUNDS = "TRADING_001"
    MARKET_CLOSED = "TRADING_002"
    ORDER_REJECTED = "TRADING_003"
    POSITION_LIMIT = "TRADING_004"

    # Authentication/Authorization
    ACCESS_DENIED = "AUTH_001"
    SESSION_EXPIRED = "AUTH_002"
    PERMISSION_DENIED = "AUTH_003"

    # Generic fallback
    UNKNOWN_ERROR = "UNKNOWN_001"


@dataclass
class SecureErrorMessage:
    """Container for secure error messages with different detail levels."""

    code: SecurityErrorCode
    user_message: str
    debug_message: str
    log_details: dict[str, Any] | None = None


class SecurityAwareErrorHandler:
    """
    Secure error handler that prevents information disclosure.

    Features:
    - Safe error message templates that don't expose internal details
    - Separate user-facing and debug information
    - Audit logging for security events
    - Input sanitization for error contexts
    """

    # Safe error message templates
    ERROR_TEMPLATES = {
        SecurityErrorCode.INVALID_SYMBOL: SecureErrorMessage(
            code=SecurityErrorCode.INVALID_SYMBOL,
            user_message="Invalid trading symbol. Please check the symbol format.",
            debug_message="Symbol validation failed",
        ),
        SecurityErrorCode.INVALID_PRICE: SecureErrorMessage(
            code=SecurityErrorCode.INVALID_PRICE,
            user_message="Invalid price format. Please enter a valid decimal number.",
            debug_message="Price validation failed",
        ),
        SecurityErrorCode.INVALID_VOLUME: SecureErrorMessage(
            code=SecurityErrorCode.INVALID_VOLUME,
            user_message="Invalid volume. Please enter a positive number.",
            debug_message="Volume validation failed",
        ),
        SecurityErrorCode.INVALID_ORDER_TYPE: SecureErrorMessage(
            code=SecurityErrorCode.INVALID_ORDER_TYPE,
            user_message="Invalid order type selected.",
            debug_message="Order type validation failed",
        ),
        SecurityErrorCode.INVALID_DIRECTION: SecureErrorMessage(
            code=SecurityErrorCode.INVALID_DIRECTION,
            user_message="Invalid order direction selected.",
            debug_message="Direction validation failed",
        ),
        SecurityErrorCode.SYSTEM_UNAVAILABLE: SecureErrorMessage(
            code=SecurityErrorCode.SYSTEM_UNAVAILABLE,
            user_message="System temporarily unavailable. Please try again later.",
            debug_message="System service unavailable",
        ),
        SecurityErrorCode.NETWORK_ERROR: SecureErrorMessage(
            code=SecurityErrorCode.NETWORK_ERROR,
            user_message="Network connection error. Please check your connection.",
            debug_message="Network communication failed",
        ),
        SecurityErrorCode.TIMEOUT_ERROR: SecureErrorMessage(
            code=SecurityErrorCode.TIMEOUT_ERROR,
            user_message="Request timed out. Please try again.",
            debug_message="Operation timeout exceeded",
        ),
        SecurityErrorCode.CONFIGURATION_ERROR: SecureErrorMessage(
            code=SecurityErrorCode.CONFIGURATION_ERROR,
            user_message="System configuration error. Please contact support.",
            debug_message="Configuration validation failed",
        ),
        SecurityErrorCode.INSUFFICIENT_FUNDS: SecureErrorMessage(
            code=SecurityErrorCode.INSUFFICIENT_FUNDS,
            user_message="Insufficient funds for this order.",
            debug_message="Account balance insufficient",
        ),
        SecurityErrorCode.MARKET_CLOSED: SecureErrorMessage(
            code=SecurityErrorCode.MARKET_CLOSED,
            user_message="Market is currently closed for trading.",
            debug_message="Market hours validation failed",
        ),
        SecurityErrorCode.ORDER_REJECTED: SecureErrorMessage(
            code=SecurityErrorCode.ORDER_REJECTED,
            user_message="Order was rejected. Please review your order details.",
            debug_message="Order validation failed",
        ),
        SecurityErrorCode.POSITION_LIMIT: SecureErrorMessage(
            code=SecurityErrorCode.POSITION_LIMIT,
            user_message="Position limit exceeded for this symbol.",
            debug_message="Position limit validation failed",
        ),
        SecurityErrorCode.ACCESS_DENIED: SecureErrorMessage(
            code=SecurityErrorCode.ACCESS_DENIED,
            user_message="Access denied. Please check your permissions.",
            debug_message="Authorization failed",
        ),
        SecurityErrorCode.SESSION_EXPIRED: SecureErrorMessage(
            code=SecurityErrorCode.SESSION_EXPIRED,
            user_message="Session expired. Please log in again.",
            debug_message="Session validation failed",
        ),
        SecurityErrorCode.PERMISSION_DENIED: SecureErrorMessage(
            code=SecurityErrorCode.PERMISSION_DENIED,
            user_message="Permission denied for this operation.",
            debug_message="Permission check failed",
        ),
        SecurityErrorCode.UNKNOWN_ERROR: SecureErrorMessage(
            code=SecurityErrorCode.UNKNOWN_ERROR,
            user_message="An unexpected error occurred. Please try again.",
            debug_message="Unhandled exception occurred",
        ),
    }

    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        context: str | None = None,
        user_data: dict[str, Any] | None = None
    ) -> SecureErrorMessage:
        """
        Handle an exception securely without exposing sensitive information.

        Args:
            exception: The exception that occurred
            context: Optional context description (will be sanitized)
            user_data: Optional user data context (will be sanitized)

        Returns:
            SecureErrorMessage with safe user-facing and debug information
        """
        # Map common exception types to secure error codes
        error_code = cls._map_exception_to_code(exception)
        error_template = cls.ERROR_TEMPLATES.get(error_code, cls.ERROR_TEMPLATES[SecurityErrorCode.UNKNOWN_ERROR])

        # Create secure error message
        secure_message = SecureErrorMessage(
            code=error_code,
            user_message=error_template.user_message,
            debug_message=error_template.debug_message,
            log_details={
                "context": cls._sanitize_context(context) if context else None,
                "user_data": cls._sanitize_user_data(user_data) if user_data else None,
                "exception_type": type(exception).__name__,
            }
        )

        # Log securely - separate user and debug information
        cls._log_security_event(exception, secure_message, context)

        return secure_message

    @classmethod
    def _map_exception_to_code(cls, exception: Exception) -> SecurityErrorCode:
        """Map exception types to secure error codes."""
        exception_type = type(exception).__name__

        mapping = {
            "ValueError": SecurityErrorCode.INVALID_SYMBOL,
            "TypeError": SecurityErrorCode.INVALID_PRICE,
            "ConnectionError": SecurityErrorCode.NETWORK_ERROR,
            "TimeoutError": SecurityErrorCode.TIMEOUT_ERROR,
            "PermissionError": SecurityErrorCode.PERMISSION_DENIED,
            "ConfigurationError": SecurityErrorCode.CONFIGURATION_ERROR,
        }

        return mapping.get(exception_type, SecurityErrorCode.UNKNOWN_ERROR)

    @classmethod
    def _sanitize_context(cls, context: str) -> str:
        """Sanitize context strings to prevent information disclosure."""
        if not context:
            return ""

        # Remove potential sensitive information patterns
        # Remove file paths
        context = re.sub(r'[/\\][\w/\\.-]+', '[PATH_REMOVED]', context)
        # Remove potential SQL or code snippets
        context = re.sub(r'(SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*', '[SQL_REMOVED]', context, flags=re.IGNORECASE)
        # Remove email addresses
        context = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REMOVED]', context)
        # Remove potential API keys or tokens (common patterns)
        context = re.sub(r'\b[A-Za-z0-9]{20,}\b', '[TOKEN_REMOVED]', context)

        # Truncate to prevent injection through length
        return context[:200]

    @classmethod
    def _sanitize_user_data(cls, user_data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize user data to prevent information disclosure."""
        if not user_data:
            return {}

        sanitized = {}
        for key, value in user_data.items():
            # Sanitize keys and values
            safe_key = cls._sanitize_context(str(key))

            if isinstance(value, str):
                safe_value = cls._sanitize_context(value)
            elif isinstance(value, int | float):
                # Limit numeric values to prevent memory exhaustion
                safe_value = str(value)[:50]
            else:
                safe_value = "[COMPLEX_TYPE_REMOVED]"

            sanitized[safe_key] = safe_value

            # Limit number of entries to prevent resource exhaustion
            if len(sanitized) >= 10:
                break

        return sanitized

    @classmethod
    def _log_security_event(
        cls,
        exception: Exception,
        secure_message: SecureErrorMessage,
        context: str | None
    ) -> None:
        """Log security events with appropriate detail levels."""
        # Log user-facing message at INFO level
        logger.info(
            f"Security event: {secure_message.code.value} - {secure_message.user_message}",
            extra={
                "security_event": True,
                "error_code": secure_message.code.value,
                "context": context,
            }
        )

        # Log debug details at DEBUG level with full traceback
        logger.debug(
            f"Security debug: {secure_message.debug_message}",
            extra={
                "security_debug": True,
                "error_code": secure_message.code.value,
                "exception_type": type(exception).__name__,
                "exception_details": str(exception),
                "traceback": traceback.format_exc(),
                "log_details": secure_message.log_details,
            }
        )

    @classmethod
    def create_validation_error(
        cls,
        field_name: str,
        error_code: SecurityErrorCode,
        user_input: str | None = None
    ) -> SecureErrorMessage:
        """
        Create a validation error message securely.

        Args:
            field_name: Name of the field being validated (will be sanitized)
            error_code: Security error code
            user_input: User input that failed validation (will be sanitized)

        Returns:
            SecureErrorMessage for the validation error
        """
        error_template = cls.ERROR_TEMPLATES.get(error_code, cls.ERROR_TEMPLATES[SecurityErrorCode.UNKNOWN_ERROR])

        # Sanitize field name and user input
        safe_field_name = cls._sanitize_context(field_name)
        safe_user_input = cls._sanitize_context(user_input) if user_input else None

        return SecureErrorMessage(
            code=error_code,
            user_message=error_template.user_message,
            debug_message=f"{error_template.debug_message} for field: {safe_field_name}",
            log_details={
                "field_name": safe_field_name,
                "user_input": safe_user_input,
                "validation_type": "field_validation",
            }
        )


class SecureInputValidator:
    """
    Secure input validation that prevents bypass and injection attacks.
    """

    @staticmethod
    def validate_decimal_input(
        value: str,
        field_name: str,
        min_value: float | None = None,
        max_value: float | None = None,
        max_precision: int = 8
    ) -> tuple[bool, float | None, SecureErrorMessage]:
        """
        Validate decimal input securely.

        Args:
            value: Input value to validate
            field_name: Name of the field being validated
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            max_precision: Maximum decimal precision

        Returns:
            Tuple of (is_valid, converted_value, error_message)
        """
        if not value or not isinstance(value, str):
            error = SecurityAwareErrorHandler.create_validation_error(
                field_name, SecurityErrorCode.INVALID_PRICE, value
            )
            return False, None, error

        # Check for basic injection patterns
        if any(char in value for char in ['<', '>', '&', '"', "'", '\\', ';']):
            error = SecurityAwareErrorHandler.create_validation_error(
                field_name, SecurityErrorCode.INVALID_PRICE, value
            )
            return False, None, error

        # Validate length to prevent memory exhaustion
        if len(value) > 50:
            error = SecurityAwareErrorHandler.create_validation_error(
                field_name, SecurityErrorCode.INVALID_PRICE, value
            )
            return False, None, error

        try:
            # Use specific exception handling instead of bare except
            decimal_value = float(value)

            # Check for special float values that could cause issues
            if decimal_value != decimal_value:  # NaN check
                error = SecurityAwareErrorHandler.create_validation_error(
                    field_name, SecurityErrorCode.INVALID_PRICE, value
                )
                return False, None, error

            if decimal_value == float('inf') or decimal_value == float('-inf'):
                error = SecurityAwareErrorHandler.create_validation_error(
                    field_name, SecurityErrorCode.INVALID_PRICE, value
                )
                return False, None, error

            # Range validation
            if min_value is not None and decimal_value < min_value:
                error = SecurityAwareErrorHandler.create_validation_error(
                    field_name, SecurityErrorCode.INVALID_PRICE, value
                )
                return False, None, error

            if max_value is not None and decimal_value > max_value:
                error = SecurityAwareErrorHandler.create_validation_error(
                    field_name, SecurityErrorCode.INVALID_PRICE, value
                )
                return False, None, error

            # Precision validation
            decimal_places = len(value.split('.')[-1]) if '.' in value else 0
            if decimal_places > max_precision:
                error = SecurityAwareErrorHandler.create_validation_error(
                    field_name, SecurityErrorCode.INVALID_PRICE, value
                )
                return False, None, error

            return True, decimal_value, None

        except (ValueError, OverflowError) as e:
            # Log the specific exception securely
            error = SecurityAwareErrorHandler.handle_exception(
                e, f"Decimal validation failed for field: {field_name}", {"user_input": value}
            )
            return False, None, error
        except Exception as e:
            # Catch any other unexpected exceptions
            error = SecurityAwareErrorHandler.handle_exception(
                e, f"Unexpected error in decimal validation for field: {field_name}", {"user_input": value}
            )
            return False, None, error


def get_secure_error_handler() -> SecurityAwareErrorHandler:
    """Get the global secure error handler instance."""
    return SecurityAwareErrorHandler()
