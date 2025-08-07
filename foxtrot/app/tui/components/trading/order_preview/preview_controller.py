"""
Order preview controller for orchestrating calculations and UI updates.

This module provides the main orchestration logic for the order preview,
coordinating between calculation engine and UI components.
"""

from decimal import Decimal
from typing import Any, Dict, Optional
import logging

from textual.containers import Container

from foxtrot.app.tui.config.settings import get_settings
from ..common import TradingConstants
from .calculation_engine import OrderCalculationEngine
from .ui_components import OrderPreviewUIManager

logger = logging.getLogger(__name__)


class OrderPreviewPanel(Container):
    """
    Panel that displays order preview with calculations and risk metrics.

    Features:
    - Real-time order value calculations
    - Available funds verification with visual indicators
    - Commission estimation
    - Position impact analysis
    - Risk metrics display
    - Error handling with user-friendly messages

    The panel automatically updates when order parameters change and provides
    immediate feedback on order feasibility and financial impact.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Order data and market data storage
        self.order_data: Dict[str, Any] = {}
        self.market_data: Dict[str, Any] = {}

        # Modular components
        self.calculation_engine = OrderCalculationEngine()
        self.ui_manager = OrderPreviewUIManager()

        # Configuration
        self.settings = get_settings()
        
        # State tracking
        self._last_calculation_error: Optional[str] = None

    def compose(self):
        """Create the preview panel layout with styled components."""
        return self.ui_manager.compose()

    async def update_preview(
        self,
        symbol: str = "",
        price: Optional[Decimal] = None,
        volume: Optional[Decimal] = None,
        order_type: str = TradingConstants.DEFAULT_ORDER_TYPE,
        direction: str = TradingConstants.DEFAULT_DIRECTION
    ) -> None:
        """
        Update the order preview with current form data.
        
        Args:
            symbol: Trading symbol
            price: Order price (None for market orders)
            volume: Order volume
            order_type: Type of order (MARKET, LIMIT, etc.)
            direction: Order direction (BUY, SELL)
            
        Note:
            This method handles all validation and error states gracefully,
            ensuring the UI remains responsive even with invalid inputs.
        """
        # Store order data for calculations
        self.order_data = {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "order_type": order_type,
            "direction": direction
        }

        await self._calculate_and_display_preview()

    async def _calculate_and_display_preview(self) -> None:
        """
        Calculate and display order preview values with error handling.
        
        This method performs all necessary calculations and updates the UI
        components with the results, handling edge cases and errors gracefully.
        """
        # Clear any previous calculation errors
        self._last_calculation_error = None
        
        # Check if we have minimum required data
        if not self.calculation_engine.has_required_data(self.order_data):
            self.ui_manager.clear_preview()
            return

        try:
            # Get validated input values
            volume = self.order_data["volume"]
            price = self.order_data.get("price")
            order_type = self.order_data.get("order_type", TradingConstants.DEFAULT_ORDER_TYPE)
            direction = self.order_data.get("direction", TradingConstants.DEFAULT_DIRECTION)

            # Determine effective price for calculations
            effective_price = await self.calculation_engine.get_effective_price(price, order_type)
            
            if not effective_price:
                self.ui_manager.show_price_unavailable()
                return

            # Perform all calculations
            calculations = await self.calculation_engine.perform_calculations(
                volume, effective_price, direction
            )
            
            # Update UI with results
            await self.ui_manager.update_display_with_calculations(calculations)

        except Exception as e:
            await self._handle_calculation_error(e)

    async def _handle_calculation_error(self, error: Exception) -> None:
        """
        Handle calculation errors with secure error reporting.
        
        Args:
            error: Exception that occurred during calculation
        """
        try:
            from foxtrot.app.tui.security import SecurityAwareErrorHandler
            
            secure_error = SecurityAwareErrorHandler.handle_exception(
                error, "order_preview_calculation"
            )
            
            self._last_calculation_error = secure_error.user_message
            self.ui_manager.show_calculation_error(secure_error.user_message)
            
            # Log the full error for debugging
            logger.error(f"Order preview calculation error: {error}")
            
        except ImportError:
            # Fallback error handling if security module unavailable
            error_msg = "Calculation error occurred"
            self._last_calculation_error = error_msg
            self.ui_manager.show_calculation_error(error_msg)
            logger.error(f"Order preview calculation error: {error}")
    
    def get_last_calculation_error(self) -> Optional[str]:
        """Get the last calculation error for testing purposes."""
        return self._last_calculation_error

    def _has_required_data(self) -> bool:
        """
        Check if order_data contains required fields for calculations.
        
        Returns:
            True if required data is available, False otherwise
            
        Note:
            This method is maintained for backward compatibility with existing tests.
        """
        if not self.order_data:
            return False
            
        # Check for required fields
        required_fields = ["symbol", "volume"]
        
        for field in required_fields:
            if field not in self.order_data or not self.order_data[field]:
                return False
                
        # Volume must be positive
        try:
            volume = float(self.order_data.get("volume", 0))
            if volume <= 0:
                return False
        except (ValueError, TypeError):
            return False
            
        return True

    async def _get_effective_price(self, price: Optional[Decimal], order_type: str) -> Decimal:
        """
        Get effective price for order calculations.
        
        Args:
            price: Specified order price (can be None for market orders)
            order_type: Type of order (MARKET, LIMIT, etc.)
            
        Returns:
            Effective price to use for calculations
            
        Note:
            This method is maintained for backward compatibility with existing tests.
        """
        if price is not None and order_type != "MARKET":
            return price
            
        # Use market price for market orders or when no price specified
        return Decimal(str(TradingConstants.MOCK_MARKET_PRICE))