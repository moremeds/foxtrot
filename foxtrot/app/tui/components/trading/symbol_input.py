"""
Symbol Input Widget for Trading Panel

This module provides a specialized input widget for entering trading symbols
with validation, auto-completion, and contract information display.
"""

from typing import Optional

from textual.widgets import Input

from foxtrot.app.tui.validation import SymbolValidator, ValidationResult


class SymbolInput(Input):
    """
    Enhanced input widget for symbol entry with auto-completion.

    Features:
    - Real-time symbol validation
    - Auto-completion based on available contracts
    - Contract information display
    """

    def __init__(
        self,
        contract_manager=None,
        placeholder: str = "Enter symbol (e.g., AAPL, BTCUSDT)",
        **kwargs
    ):
        """
        Initialize the symbol input widget.

        Args:
            contract_manager: Manager for contract information
            placeholder: Placeholder text for the input
            **kwargs: Additional arguments passed to Input widget
        """
        super().__init__(placeholder=placeholder, **kwargs)
        self.contract_manager = contract_manager
        self.validator = SymbolValidator(contract_manager=contract_manager)
        self.suggestions: list[str] = []
        self._last_validation_result: Optional[ValidationResult] = None

    async def validate_symbol(self, value: str) -> ValidationResult:
        """
        Validate symbol and return result.

        Args:
            value: Symbol string to validate

        Returns:
            ValidationResult with validity status and any error messages
        """
        result = self.validator.validate(value)
        self._last_validation_result = result
        return result

    async def get_suggestions(self, partial: str) -> list[str]:
        """
        Get symbol suggestions for auto-completion.

        Args:
            partial: Partial symbol string to search

        Returns:
            List of suggested symbols matching the partial input
        """
        if not self.contract_manager or len(partial) < 2:
            return []

        # TODO: Integrate with actual contract manager
        # For now, return mock suggestions for testing
        mock_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "SPY", "QQQ",
            "EUR", "GBP", "JPY", "AUD", "CAD"
        ]

        # Filter and return top 5 matches
        suggestions = [
            symbol for symbol in mock_symbols
            if symbol.startswith(partial.upper())
        ]
        
        self.suggestions = suggestions[:5]
        return self.suggestions

    async def on_input_changed(self, event) -> None:
        """
        Handle input change events for real-time validation.

        Args:
            event: Input change event
        """
        value = self.value
        if value:
            # Trigger validation on each change
            await self.validate_symbol(value)
            
            # Update suggestions if length is sufficient
            if len(value) >= 2:
                await self.get_suggestions(value)

    @property
    def is_valid(self) -> bool:
        """
        Check if the current input is valid.

        Returns:
            True if the input is valid, False otherwise
        """
        if not self._last_validation_result:
            return False
        return self._last_validation_result.is_valid

    @property
    def validation_errors(self) -> list[str]:
        """
        Get validation errors for the current input.

        Returns:
            List of validation error messages
        """
        if not self._last_validation_result:
            return []
        return self._last_validation_result.errors

    def clear_validation(self) -> None:
        """Clear the validation state."""
        self._last_validation_result = None
        self.suggestions = []

    async def set_symbol(self, symbol: str) -> None:
        """
        Set the symbol value and trigger validation.

        Args:
            symbol: Symbol to set
        """
        self.value = symbol
        await self.validate_symbol(symbol)