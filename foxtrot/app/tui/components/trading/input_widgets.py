"""
Enhanced input widgets for trading forms.

This module provides specialized input widgets with validation,
auto-completion, and security features for trading interfaces.
"""

from typing import List, Optional
import logging

from textual.widgets import Input

from foxtrot.app.tui.validation import SymbolValidator, ValidationResult
from .common import get_symbol_suggestions

# Set up logging
logger = logging.getLogger(__name__)


class SymbolInput(Input):
    """
    Enhanced input widget for symbol entry with auto-completion and validation.

    Features:
    - Real-time symbol validation using SymbolValidator
    - Auto-completion based on available contracts
    - Contract information display
    - Security-aware input handling
    - Type-safe validation results

    Args:
        contract_manager: Optional contract manager for real symbol validation
        placeholder: Placeholder text for the input field
        **kwargs: Additional arguments passed to Input widget
    """

    def __init__(
        self,
        contract_manager=None,
        placeholder: str = "Enter symbol (e.g., AAPL, BTCUSDT)",
        **kwargs
    ):
        super().__init__(placeholder=placeholder, **kwargs)
        self.contract_manager = contract_manager
        self.validator = SymbolValidator(contract_manager=contract_manager)
        self.suggestions: List[str] = []
        self._last_validation_result: Optional[ValidationResult] = None
    
    @property
    def last_validation_result(self) -> Optional[ValidationResult]:
        """Get the last validation result for testing and debugging."""
        return self._last_validation_result

    async def validate_symbol(self, value: str) -> ValidationResult:
        """
        Validate symbol and return result.
        
        Args:
            value: Symbol string to validate
            
        Returns:
            ValidationResult with validation status and any errors
            
        Raises:
            ValidationError: If validation fails with security implications
        """
        try:
            result = self.validator.validate(value)
            self._last_validation_result = result
            
            # Log validation attempts for security monitoring
            if not result.is_valid:
                logger.debug(f"Symbol validation failed for '{value}': {result.errors}")
            
            return result
            
        except Exception as e:
            logger.warning(f"Symbol validation error for '{value}': {e}")
            error_result = ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
            self._last_validation_result = error_result
            return error_result

    async def get_suggestions(self, partial: str) -> List[str]:
        """
        Get symbol suggestions for auto-completion.
        
        Args:
            partial: Partial symbol string to match against
            
        Returns:
            List of matching symbols, limited to 5 results
            
        Note:
            In production, this would integrate with the contract manager
            to provide real symbol suggestions from available contracts.
        """
        if not partial or len(partial) < 2:
            return []

        try:
            # Use real contract manager if available
            if self.contract_manager and hasattr(self.contract_manager, 'search_symbols'):
                suggestions = await self.contract_manager.search_symbols(partial)
                return suggestions[:5]
            
            # Fallback to mock suggestions
            suggestions = get_symbol_suggestions(partial, max_results=5)
            
            # Cache suggestions for potential reuse
            self.suggestions = suggestions
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"Error getting symbol suggestions for '{partial}': {e}")
            return []

    def clear_suggestions(self) -> None:
        """Clear cached suggestions."""
        self.suggestions.clear()
        
    def has_valid_value(self) -> bool:
        """Check if current value is valid based on last validation."""
        return (
            self._last_validation_result is not None and 
            self._last_validation_result.is_valid
        )


class PriceInput(Input):
    """
    Enhanced input widget for price entry with decimal validation.
    
    Features:
    - Decimal precision validation
    - Range checking
    - Security-aware input handling
    - Auto-formatting for display
    """
    
    def __init__(
        self,
        min_price: float = 0.0,
        max_price: float = 1000000.0,
        precision: int = 8,
        placeholder: str = "Enter price",
        **kwargs
    ):
        super().__init__(placeholder=placeholder, **kwargs)
        self.min_price = min_price
        self.max_price = max_price
        self.precision = precision
        
    async def validate_price(self, value: str) -> ValidationResult:
        """Validate price input with range and precision checking."""
        if not value:
            return ValidationResult(is_valid=True)  # Empty is valid for market orders
            
        try:
            from foxtrot.app.tui.security import SecureInputValidator
            
            is_valid, decimal_value, error = SecureInputValidator.validate_decimal_input(
                value,
                "price",
                min_value=self.min_price,
                max_value=self.max_price,
                max_precision=self.precision
            )
            
            if is_valid:
                return ValidationResult(is_valid=True)
            else:
                error_msg = error.user_message if error else "Invalid price format"
                return ValidationResult(
                    is_valid=False,
                    errors=[error_msg]
                )
                
        except Exception as e:
            logger.warning(f"Price validation error for '{value}': {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Price validation error: {str(e)}"]
            )


class VolumeInput(Input):
    """
    Enhanced input widget for volume entry with validation.
    
    Features:
    - Volume range validation
    - Integer or decimal support based on asset type
    - Security-aware input handling
    """
    
    def __init__(
        self,
        min_volume: float = 0.0,
        max_volume: float = 1000000.0,
        precision: int = 8,
        placeholder: str = "Number of shares/units",
        **kwargs
    ):
        super().__init__(placeholder=placeholder, **kwargs)
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.precision = precision
        
    async def validate_volume(self, value: str) -> ValidationResult:
        """Validate volume input with range checking."""
        if not value:
            return ValidationResult(
                is_valid=False,
                errors=["Volume is required"]
            )
            
        try:
            from foxtrot.app.tui.security import SecureInputValidator
            
            is_valid, decimal_value, error = SecureInputValidator.validate_decimal_input(
                value,
                "volume",
                min_value=self.min_volume,
                max_value=self.max_volume,
                max_precision=self.precision
            )
            
            if is_valid:
                return ValidationResult(is_valid=True)
            else:
                error_msg = error.user_message if error else "Invalid volume format"
                return ValidationResult(
                    is_valid=False,
                    errors=[error_msg]
                )
                
        except Exception as e:
            logger.warning(f"Volume validation error for '{value}': {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Volume validation error: {str(e)}"]
            )