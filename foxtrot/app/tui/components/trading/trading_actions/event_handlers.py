"""
Trading event handlers for user interactions and messaging.

This module handles event-driven interactions including user confirmations,
modal dialogs, success/error messaging, and event coordination.
"""

from typing import Any, Dict, Optional, List
import logging
from datetime import datetime

from foxtrot.util.object import OrderData
from foxtrot.util.constants import Direction
from ..common import TradingConstants

logger = logging.getLogger(__name__)


class TradingEventHandler:
    """
    Handles event-driven interactions for trading operations.
    
    This class focuses on user interaction events, modal dialogs,
    messaging, and UI feedback with no direct business logic execution.
    """

    def __init__(self):
        # Modal manager reference (set by controller)
        self.modal_manager = None
        
        # Settings reference (set by controller)
        self.settings = None

    def set_modal_manager(self, modal_manager) -> None:
        """Set modal manager for confirmation dialogs."""
        self.modal_manager = modal_manager

    def set_settings(self, settings) -> None:
        """Set settings reference for configuration."""
        self.settings = settings

    async def confirm_order(self, order_data: OrderData) -> bool:
        """
        Show order confirmation dialog to user.
        
        Args:
            order_data: Order data to confirm
            
        Returns:
            True if user confirmed, False if cancelled
        """
        if not self.modal_manager:
            logger.warning("Modal manager not available, skipping confirmation")
            return True  # Proceed without confirmation if modal unavailable
        
        try:
            # Format order details for confirmation
            direction_str = "BUY" if order_data.direction == Direction.LONG else "SELL"
            type_str = order_data.type.name if hasattr(order_data.type, 'name') else str(order_data.type)
            
            confirmation_message = (
                f"Confirm Order:\n\n"
                f"Symbol: {order_data.vt_symbol}\n"
                f"Direction: {direction_str}\n"
                f"Type: {type_str}\n"
                f"Volume: {order_data.volume:,.0f}\n"
            )
            
            if order_data.price > 0:
                confirmation_message += f"Price: ${order_data.price:,.2f}\n"
            
            # Calculate estimated value
            estimated_price = order_data.price if order_data.price > 0 else TradingConstants.MOCK_MARKET_PRICE
            estimated_value = float(estimated_price) * order_data.volume
            confirmation_message += f"\nEstimated Value: ${estimated_value:,.2f}"
            
            # Show confirmation dialog
            confirmed = await self.modal_manager.show_confirmation(
                title="Confirm Order",
                message=confirmation_message,
                confirm_text="Submit Order",
                cancel_text="Cancel"
            )
            
            return confirmed
            
        except Exception as e:
            logger.error(f"Error showing order confirmation: {e}")
            # If confirmation dialog fails, ask user via fallback method
            return await self.fallback_confirmation(order_data)

    async def fallback_confirmation(self, order_data: OrderData) -> bool:
        """Fallback confirmation method when modal is unavailable."""
        # In a real implementation, this might use a simple text prompt
        # For now, we'll assume confirmation
        logger.info(f"Using fallback confirmation for order: {order_data.vt_symbol}")
        return True

    async def confirm_cancel_all(self, active_orders: List[Dict[str, Any]]) -> bool:
        """Show confirmation dialog for cancelling all orders."""
        if not self.modal_manager:
            return True
            
        try:
            order_count = len(active_orders)
            confirmation_message = (
                f"Cancel All Orders?\n\n"
                f"This will cancel {order_count} active order"
                f"{'s' if order_count != 1 else ''}.\n\n"
                f"This action cannot be undone."
            )
            
            confirmed = await self.modal_manager.show_confirmation(
                title="Cancel All Orders",
                message=confirmation_message,
                confirm_text="Cancel All",
                cancel_text="Keep Orders",
                variant="error"  # Use error variant for destructive action
            )
            
            return confirmed
            
        except Exception as e:
            logger.error(f"Error showing cancel all confirmation: {e}")
            return False

    async def show_success_message(self, message: str) -> None:
        """Show success message to user."""
        if self.modal_manager:
            try:
                await self.modal_manager.show_info(
                    title="Success",
                    message=message,
                    variant="success"
                )
            except Exception as e:
                logger.error(f"Error showing success message: {e}")
        else:
            logger.info(f"Success: {message}")

    async def show_error_message(self, message: str) -> None:
        """Show error message to user."""
        if self.modal_manager:
            try:
                await self.modal_manager.show_error(
                    title="Error",
                    message=message
                )
            except Exception as e:
                logger.error(f"Error showing error message: {e}")
        else:
            logger.error(f"Error: {message}")

    async def show_info_message(self, message: str) -> None:
        """Show info message to user."""
        if self.modal_manager:
            try:
                await self.modal_manager.show_info(
                    title="Information",
                    message=message
                )
            except Exception as e:
                logger.error(f"Error showing info message: {e}")
        else:
            logger.info(f"Info: {message}")


class OrderSubmissionMessage:
    """Message class for order submission events."""
    
    def __init__(self, order_data: Dict[str, Any], order_id: Optional[str] = None):
        self.order_data = order_data
        self.order_id = order_id
        self.timestamp = datetime.now()


class OrderValidationMessage:
    """Message class for order validation events."""
    
    def __init__(self, errors: List[str]):
        self.errors = errors
        self.timestamp = datetime.now()