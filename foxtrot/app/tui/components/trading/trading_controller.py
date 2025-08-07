"""
Trading controller for business logic and state management.

This module provides the TradingController class that handles
business logic, order management, and state coordination for trading panels.
"""

from typing import Any, Dict, Optional
from decimal import Decimal
import logging

from foxtrot.core.event_engine import Event, EventEngine  
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_TICK, EVENT_ORDER, EVENT_ACCOUNT
from foxtrot.util.object import OrderData
from foxtrot.util.constants import Direction, OrderType

# Set up logging
logger = logging.getLogger(__name__)


class TradingController:
    """
    Controller class for trading business logic.
    
    This controller handles:
    - Order validation and processing
    - State management for trading operations  
    - Integration with MainEngine for order execution
    - Business rules and calculations
    - Event processing for trading operations
    """
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """Initialize the trading controller."""
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # State management
        self.current_symbol = ""
        self.current_exchange = ""
        self.current_order_data: Dict[str, Any] = {}
        
        # Settings
        self.settings = {}
        
    def validate_order_data(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate order data before submission.
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        symbol = order_data.get("symbol", "")
        if not symbol:
            return False, "Symbol is required"
            
        volume = order_data.get("volume")
        if not volume or volume <= 0:
            return False, "Volume must be greater than 0"
            
        price = order_data.get("price")
        order_type = order_data.get("order_type", "MARKET")
        
        if order_type == "LIMIT" and (not price or price <= 0):
            return False, "Price is required for limit orders"
            
        return True, ""
        
    def submit_order(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Submit an order through the main engine.
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Tuple of (success, error_message_or_order_id)
        """
        # Validate first
        is_valid, error = self.validate_order_data(order_data)
        if not is_valid:
            return False, error
            
        try:
            # Create OrderData object
            order = OrderData(
                symbol=order_data["symbol"],
                exchange=order_data.get("exchange", "SMART"),
                direction=Direction(order_data["direction"]),
                type=OrderType(order_data["order_type"]),
                volume=float(order_data["volume"]),
                price=float(order_data.get("price", 0)) if order_data.get("price") else 0,
                gateway_name="mock"  # This would be determined by the adapter
            )
            
            # Submit through main engine
            # Note: This would normally call main_engine.send_order(order)
            # For now, return success with mock order ID
            order_id = f"ORDER_{order.symbol}_{int(order.volume)}"
            logger.info(f"Order submitted: {order_id}")
            
            return True, order_id
            
        except Exception as e:
            error_msg = f"Order submission failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def cancel_all_orders(self) -> tuple[bool, str]:
        """
        Cancel all active orders.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # This would normally call main_engine.cancel_all_orders()
            # For now, return mock success
            logger.info("Cancel all orders requested")
            return True, "All orders cancelled"
            
        except Exception as e:
            error_msg = f"Cancel all failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def get_account_balance(self) -> Decimal:
        """Get current account balance."""
        # This would normally query the main engine for account info
        # For now, return mock balance
        return Decimal("10000.00")
        
    def get_market_price(self, symbol: str) -> Optional[Decimal]:
        """Get current market price for symbol."""
        # This would normally query market data
        # For now, return mock price
        if symbol:
            return Decimal("150.00")
        return None
        
    def calculate_order_value(self, volume: Decimal, price: Decimal) -> Decimal:
        """Calculate total order value."""
        return volume * price
        
    def calculate_commission(self, volume: Decimal, price: Decimal) -> Decimal:
        """Calculate estimated commission."""
        order_value = volume * price
        commission_rate = Decimal("0.005")  # 0.5%
        return order_value * commission_rate
        
    def update_current_symbol(self, symbol: str, exchange: str = ""):
        """Update current symbol for market data tracking."""
        self.current_symbol = symbol
        self.current_exchange = exchange
        
    def get_position_impact(self, volume: Decimal, direction: str) -> str:
        """Calculate position impact description."""
        action = "increase" if direction == "BUY" else "decrease"
        return f"Will {action} position by {volume} shares"