"""
Form data extraction and binding logic.

This module handles data extraction from UI components,
form data transformation, and TradingFormData object creation.
"""

from typing import Any, Dict, Optional
import logging
from decimal import Decimal

from textual.widgets import Input, Select, RadioSet, Button, Static

from foxtrot.app.tui.components.trading.common import TradingConstants, TradingFormData
from foxtrot.app.tui.components.trading.input_widgets import SymbolInput

# Set up logging
logger = logging.getLogger(__name__)


class TradingFormDataBinder:
    """
    Handles form data extraction and binding operations.
    
    Features:
    - UI component data extraction
    - Data type conversion and validation
    - TradingFormData object creation
    - Form data dictionary management
    """
    
    def __init__(self):
        """Initialize data binder."""
        # UI Component references (set by UI manager)
        self.symbol_input: Optional[SymbolInput] = None
        self.exchange_select: Optional[Select] = None
        self.direction_radio: Optional[RadioSet] = None
        self.order_type_select: Optional[Select] = None
        self.price_input: Optional[Input] = None
        self.volume_input: Optional[Input] = None
    
    def set_ui_components(
        self,
        symbol_input: SymbolInput,
        exchange_select: Select,
        direction_radio: RadioSet,
        order_type_select: Select,
        price_input: Input,
        volume_input: Input,
    ) -> None:
        """
        Set UI component references for data extraction.
        
        Args:
            symbol_input: Symbol input widget
            exchange_select: Exchange selection widget
            direction_radio: Direction radio button set
            order_type_select: Order type selection widget
            price_input: Price input widget
            volume_input: Volume input widget
        """
        self.symbol_input = symbol_input
        self.exchange_select = exchange_select
        self.direction_radio = direction_radio
        self.order_type_select = order_type_select
        self.price_input = price_input
        self.volume_input = volume_input
    
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
    
    def has_required_fields(self, form_data: Dict[str, Any]) -> bool:
        """
        Check if form data has required fields for basic validation.
        
        Args:
            form_data: Form data dictionary
            
        Returns:
            True if required fields are present and non-empty
        """
        return (
            form_data.get("symbol", "").strip() and 
            form_data.get("volume", "").strip()
        )
    
    def clear_form_data(self) -> None:
        """Clear all form input values."""
        if self.symbol_input:
            self.symbol_input.value = ""
        if self.price_input:
            self.price_input.value = ""
        if self.volume_input:
            self.volume_input.value = ""
        # Note: Radio buttons and selects typically reset to default, not cleared