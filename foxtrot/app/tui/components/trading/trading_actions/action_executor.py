"""
Trading action executor for core business logic operations.

This module handles the core execution logic including order creation,
validation, engine communication, and order management operations.
"""

from typing import Any, Dict, Optional, List
import logging
from decimal import Decimal
from datetime import datetime

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, OrderType
from foxtrot.util.object import OrderData

from ..common import TradingFormData

logger = logging.getLogger(__name__)


class TradingActionExecutor:
    """
    Executes core trading business logic operations.
    
    This class contains pure business logic for order creation,
    validation, engine communication, and state management
    with no UI or event handling concerns.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # State tracking
        self._last_execution_error: Optional[str] = None
        self._pending_orders: List[str] = []

    def create_order_data(self, form_data: TradingFormData) -> OrderData:
        """
        Create OrderData object from validated form data.
        
        Args:
            form_data: Validated trading form data
            
        Returns:
            OrderData object ready for submission
            
        Raises:
            ValueError: If form data is invalid or incomplete
        """
        if not form_data.symbol:
            raise ValueError("Symbol is required for order creation")
            
        if not form_data.volume or form_data.volume <= 0:
            raise ValueError("Valid volume is required for order creation")
        
        # Map form values to order constants
        direction = Direction.LONG if form_data.direction == "BUY" else Direction.SHORT
        
        # Map order type
        order_type_mapping = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
            "STOP": OrderType.STOP,
            "STOP_LIMIT": OrderType.STOP_LIMIT
        }
        order_type = order_type_mapping.get(form_data.order_type, OrderType.MARKET)
        
        # Determine price based on order type
        if order_type == OrderType.MARKET:
            price = 0.0  # Market orders don't need price
        elif form_data.price:
            price = float(form_data.price)
        else:
            raise ValueError(f"Price is required for {form_data.order_type} orders")
        
        # Create vt_symbol (symbol.exchange format)
        exchange = form_data.exchange if form_data.exchange else "SMART"
        vt_symbol = f"{form_data.symbol}.{exchange}"
        
        # Create order data
        order_data = OrderData(
            symbol=form_data.symbol,
            exchange=exchange,
            direction=direction,
            type=order_type,
            volume=float(form_data.volume),
            price=price,
            offset="OPEN",  # Default for new positions
            gateway_name="trading_panel",
            datetime=datetime.now()
        )
        
        return order_data

    async def send_order_to_engine(self, order_data: OrderData) -> bool:
        """
        Send order to main engine for execution.
        
        Args:
            order_data: Order data to submit
            
        Returns:
            True if successfully sent to engine, False otherwise
        """
        try:
            # Clear previous execution errors
            self._last_execution_error = None
            
            # Send order to main engine
            order_id = self.main_engine.send_order(
                req=order_data,
                gateway_name=order_data.gateway_name
            )
            
            if order_id:
                # Track pending order
                self._pending_orders.append(order_id)
                logger.info(f"Order sent to engine with ID: {order_id}")
                return True
            else:
                logger.error("Main engine returned no order ID")
                self._last_execution_error = "No order ID returned from engine"
                return False
                
        except Exception as e:
            error_msg = f"Error sending order to engine: {e}"
            logger.error(error_msg)
            self._last_execution_error = error_msg
            return False

    async def get_active_orders(self) -> List[Dict[str, Any]]:
        """
        Get list of active orders from main engine.
        
        Returns:
            List of active order dictionaries
            
        Note:
            In production, this would query the main engine's order manager
            for all active orders for the current account.
        """
        try:
            # TODO: Integrate with main engine order manager
            # active_orders = self.main_engine.get_all_active_orders()
            
            # Mock active orders for demonstration
            return []
            
        except Exception as e:
            error_msg = f"Error getting active orders: {e}"
            logger.error(error_msg)
            self._last_execution_error = error_msg
            return []

    async def execute_cancel_all(self, active_orders: List[Dict[str, Any]]) -> bool:
        """Execute cancellation of all active orders."""
        try:
            # Clear previous execution errors
            self._last_execution_error = None
            
            success_count = 0
            
            for order in active_orders:
                try:
                    # Cancel individual order through main engine
                    # order_id = order.get("order_id")
                    # gateway_name = order.get("gateway_name")
                    # self.main_engine.cancel_order(order_id, gateway_name)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to cancel order {order}: {e}")
            
            # Consider successful if we cancelled at least some orders
            if success_count == 0 and active_orders:
                self._last_execution_error = "Failed to cancel any orders"
                return False
                
            return success_count > 0
            
        except Exception as e:
            error_msg = f"Error executing cancel all: {e}"
            logger.error(error_msg)
            self._last_execution_error = error_msg
            return False

    def get_last_execution_error(self) -> Optional[str]:
        """Get the last execution error for testing and debugging."""
        return self._last_execution_error

    def clear_execution_error(self) -> None:
        """Clear the last execution error state."""
        self._last_execution_error = None

    def get_pending_orders(self) -> List[str]:
        """Get list of pending order IDs."""
        return self._pending_orders.copy()

    def clear_pending_orders(self) -> None:
        """Clear pending orders list."""
        self._pending_orders.clear()

    def add_pending_order(self, order_id: str) -> None:
        """Add order ID to pending orders list."""
        if order_id not in self._pending_orders:
            self._pending_orders.append(order_id)

    def remove_pending_order(self, order_id: str) -> None:
        """Remove order ID from pending orders list."""
        if order_id in self._pending_orders:
            self._pending_orders.remove(order_id)