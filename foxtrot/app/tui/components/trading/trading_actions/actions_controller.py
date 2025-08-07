"""
Trading actions controller for orchestrating events and execution.

This module provides the main orchestration logic for trading actions,
coordinating between event handlers and action executor components.
"""

from typing import Optional
import logging

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine

from ..common import TradingFormData
from ..form import TradingFormManager
from .event_handlers import TradingEventHandler
from .action_executor import TradingActionExecutor

logger = logging.getLogger(__name__)


class TradingActionHandler:
    """
    Handles trading actions for order submission and management.
    
    Features:
    - Order creation and validation
    - Order submission to main engine
    - Order confirmation dialogs
    - Bulk order cancellation
    - Integration with modal dialogs
    - Security-aware order processing
    
    This class coordinates with the main engine to execute trading
    operations while maintaining proper validation and user feedback.
    """
    
    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        form_manager: TradingFormManager
    ):
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.form_manager = form_manager
        
        # Modular components
        self.event_handler = TradingEventHandler()
        self.action_executor = TradingActionExecutor(main_engine, event_engine)
        
        # Settings reference (set by controller)
        self.settings = None
        
        # State tracking
        self._last_submission_error: Optional[str] = None

    def set_modal_manager(self, modal_manager) -> None:
        """Set modal manager for confirmation dialogs."""
        self.event_handler.set_modal_manager(modal_manager)

    def set_settings(self, settings) -> None:
        """Set settings reference for configuration."""
        self.settings = settings
        self.event_handler.set_settings(settings)

    async def submit_order(self) -> bool:
        """
        Submit order after validation and confirmation.
        
        Returns:
            True if order was successfully submitted, False otherwise
            
        Note:
            This method performs complete validation, user confirmation,
            and secure order submission with comprehensive error handling.
        """
        try:
            # Clear any previous errors
            self._last_submission_error = None
            self.action_executor.clear_execution_error()
            
            # Validate form before proceeding
            if not await self.form_manager.validate_form():
                self._last_submission_error = "Form validation failed"
                logger.warning("Order submission failed: form validation errors")
                return False
            
            # Get validated form data
            form_data_dict = await self.form_manager.get_form_data()
            form_data = self.form_manager.create_form_data_object(form_data_dict)
            
            # Create order data
            order_data = self.action_executor.create_order_data(form_data)
            
            # Confirm order with user if required
            if self.settings and self.settings.confirm_orders:
                if not await self.event_handler.confirm_order(order_data):
                    logger.info("Order submission cancelled by user")
                    return False
            
            # Submit order to engine
            success = await self.action_executor.send_order_to_engine(order_data)
            
            if success:
                logger.info(f"Order submitted successfully: {order_data.vt_symbol}")
                await self.event_handler.show_success_message("Order submitted successfully")
            else:
                logger.error(f"Order submission failed: {order_data.vt_symbol}")
                execution_error = self.action_executor.get_last_execution_error()
                if execution_error:
                    self._last_submission_error = execution_error
                
            return success
            
        except Exception as e:
            error_msg = f"Order submission error: {str(e)}"
            self._last_submission_error = error_msg
            logger.error(error_msg)
            await self.event_handler.show_error_message("Order submission failed")
            return False

    async def cancel_all_orders(self) -> bool:
        """
        Cancel all pending orders after confirmation.
        
        Returns:
            True if cancellation was initiated, False otherwise
        """
        try:
            # Clear any previous errors
            self.action_executor.clear_execution_error()
            
            # Check if there are any orders to cancel
            active_orders = await self.action_executor.get_active_orders()
            
            if not active_orders:
                await self.event_handler.show_info_message("No active orders to cancel")
                return True
            
            # Confirm bulk cancellation
            if self.settings and self.settings.confirm_orders:
                confirmed = await self.event_handler.confirm_cancel_all(active_orders)
                if not confirmed:
                    logger.info("Cancel all orders cancelled by user")
                    return False
            
            # Execute cancellation
            success = await self.action_executor.execute_cancel_all(active_orders)
            
            if success:
                await self.event_handler.show_success_message(f"Cancelled {len(active_orders)} orders")
            else:
                await self.event_handler.show_error_message("Failed to cancel some orders")
                
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            await self.event_handler.show_error_message("Error cancelling orders")
            return False

    def get_last_submission_error(self) -> Optional[str]:
        """Get the last order submission error for testing."""
        return self._last_submission_error

    def get_pending_orders(self) -> list[str]:
        """Get list of pending order IDs."""
        return self.action_executor.get_pending_orders()

    def clear_pending_orders(self) -> None:
        """Clear pending orders list."""
        self.action_executor.clear_pending_orders()