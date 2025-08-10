"""
Futu callback handler manager for SDK callback lifecycle management.

This module manages the creation, registration, and cleanup of Futu SDK
callback handlers for real-time quote and trade data processing.
"""

import weakref
from typing import Dict, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from foxtrot.adapter.futu.futu_callbacks import FutuQuoteHandler, FutuTradeHandler
    from foxtrot.adapter.futu.api_client import FutuApiClient


class FutuCallbackHandlerManager:
    """
    Manager for Futu SDK callback handler lifecycle operations.
    
    This class handles the creation, registration, and cleanup of
    callback handlers for real-time data processing.
    """

    def __init__(self, api_client_ref: 'weakref.ref[FutuApiClient]') -> None:
        """
        Initialize callback handler manager.
        
        Args:
            api_client_ref: Weak reference to FutuApiClient instance
        """
        self._api_client_ref = api_client_ref
        
        # Handler instances
        self._quote_handler: Optional['FutuQuoteHandler'] = None
        self._trade_handler: Optional['FutuTradeHandler'] = None
        self._handlers_registered = False

    def setup_callback_handlers(self) -> bool:
        """
        Create and register SDK callback handlers for real-time data.
        
        Returns:
            True if setup successful, False otherwise
        """
        api_client = self._api_client_ref()
        if not api_client:
            return False

        if self._handlers_registered:
            self._log_info("Callback handlers already registered")
            return True

        try:
            # Import callback handlers locally to avoid circular imports
            from foxtrot.adapter.futu.futu_callbacks import FutuQuoteHandler, FutuTradeHandler

            # Create callback handlers
            self._quote_handler = FutuQuoteHandler(api_client)
            self._trade_handler = FutuTradeHandler(api_client)

            # Set handler references in API client for backward compatibility
            api_client.quote_handler = self._quote_handler
            api_client.trade_handler = self._trade_handler

            # Register quote handler with quote context
            if hasattr(api_client, 'quote_ctx') and api_client.quote_ctx:
                api_client.quote_ctx.set_handler(self._quote_handler)
                self._log_info("Quote callback handler registered")

            # Register trade handler with HK trade context
            if hasattr(api_client, 'trade_ctx_hk') and api_client.trade_ctx_hk:
                api_client.trade_ctx_hk.set_handler(self._trade_handler)
                self._log_info("HK trade callback handler registered")

            # Register trade handler with US trade context
            if hasattr(api_client, 'trade_ctx_us') and api_client.trade_ctx_us:
                api_client.trade_ctx_us.set_handler(self._trade_handler)
                self._log_info("US trade callback handler registered")

            self._handlers_registered = True
            self._log_info("All callback handlers setup completed")
            return True

        except (ImportError, AttributeError) as e:
            self._log_error(f"Callback handler setup failed: {e}")
            return False
        except Exception as e:
            self._log_error(f"Unexpected error during callback handler setup: {e}")
            return False

    def cleanup_handlers(self) -> None:
        """
        Clean up all callback handlers and clear references.
        """
        api_client = self._api_client_ref()
        
        try:
            # Clear handler references in API client
            if api_client:
                api_client.quote_handler = None
                api_client.trade_handler = None

            # Clear local handler references
            self._quote_handler = None
            self._trade_handler = None
            self._handlers_registered = False

            self._log_info("All callback handlers cleaned up")

        except Exception as e:
            self._log_error(f"Unexpected error during callback handler cleanup: {e}")

    def get_quote_handler(self) -> Optional['FutuQuoteHandler']:
        """
        Get the quote callback handler instance.
        
        Returns:
            Quote handler instance or None if not initialized
        """
        return self._quote_handler

    def get_trade_handler(self) -> Optional['FutuTradeHandler']:
        """
        Get the trade callback handler instance.
        
        Returns:
            Trade handler instance or None if not initialized
        """
        return self._trade_handler

    def is_registered(self) -> bool:
        """
        Check if callback handlers are registered.
        
        Returns:
            True if handlers are registered, False otherwise
        """
        return self._handlers_registered

    def get_handler_status(self) -> Dict[str, Union[bool, Dict[str, Union[bool, Optional[str], Dict[str, bool]]]]]:
        """
        Get status information for all callback handlers.
        
        Returns:
            Dictionary with handler status information
        """
        api_client = self._api_client_ref()
        
        status = {
            "api_client_alive": api_client is not None,
            "handlers_registered": self._handlers_registered,
            "handlers": {
                "quote_handler": {
                    "initialized": self._quote_handler is not None,
                    "type": type(self._quote_handler).__name__ if self._quote_handler else None
                },
                "trade_handler": {
                    "initialized": self._trade_handler is not None,
                    "type": type(self._trade_handler).__name__ if self._trade_handler else None
                }
            }
        }

        # Check handler registration status with contexts
        if api_client:
            status["context_registrations"] = {
                "quote_context": (hasattr(api_client, 'quote_ctx') and 
                                api_client.quote_ctx is not None),
                "hk_trade_context": (hasattr(api_client, 'trade_ctx_hk') and 
                                   api_client.trade_ctx_hk is not None),
                "us_trade_context": (hasattr(api_client, 'trade_ctx_us') and 
                                   api_client.trade_ctx_us is not None)
            }

        return status

    def reinitialize_handlers(self) -> bool:
        """
        Reinitialize all callback handlers (cleanup and setup).
        
        Returns:
            True if reinitialization successful, False otherwise
        """
        self._log_info("Reinitializing callback handlers")
        self.cleanup_handlers()
        return self.setup_callback_handlers()

    def _log_info(self, msg: str) -> None:
        """Log info message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_info'):
            api_client._log_info(f"CallbackHandlerManager: {msg}")

    def _log_error(self, msg: str) -> None:
        """Log error message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_error'):
            api_client._log_error(f"CallbackHandlerManager: {msg}")