"""
Futu context utilities module.

This module provides utility functions for context management,
status checking, testing, and cleanup operations.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING, Union
import weakref

import futu as ft

if TYPE_CHECKING:
    from ...api_client import FutuApiClient


class FutuContextUtilities:
    """Provides utility functions for context management."""

    def __init__(self, api_client_ref: 'weakref.ref[FutuApiClient]') -> None:
        """Initialize with weak reference to API client."""
        self._api_client_ref = api_client_ref

    def setup_callback_handlers(self) -> None:
        """Setup callback handlers for all active contexts."""
        api_client = self._api_client_ref()
        if not api_client:
            return

        try:
            # Setup quote context callbacks
            if hasattr(api_client, 'quote_ctx') and api_client.quote_ctx:
                callback_manager = api_client.callback_handler_manager
                api_client.quote_ctx.set_handler(callback_manager.on_recv_rsp)

            # Setup trade context callbacks for HK
            if hasattr(api_client, 'hk_trade_ctx') and api_client.hk_trade_ctx:
                api_client.hk_trade_ctx.set_handler(callback_manager.on_order_update)

            # Setup trade context callbacks for US
            if hasattr(api_client, 'us_trade_ctx') and api_client.us_trade_ctx:
                api_client.us_trade_ctx.set_handler(callback_manager.on_order_update)

            api_client._log_info("Callback handlers setup completed")

        except (AttributeError, ImportError) as e:
            if api_client:
                api_client._log_error(f"Failed to setup callback handlers: {e}")
        except Exception as e:
            if api_client:
                api_client._log_error(f"Unexpected error during callback handler setup: {e}")

    def cleanup_contexts(self) -> None:
        """Clean up all active contexts and their connections."""
        api_client = self._api_client_ref()
        if not api_client:
            return

        try:
            contexts_cleaned = 0

            # Cleanup quote context
            if hasattr(api_client, 'quote_ctx') and api_client.quote_ctx:
                api_client.quote_ctx.close()
                api_client.quote_ctx = None
                contexts_cleaned += 1

            # Cleanup HK trade context
            if hasattr(api_client, 'hk_trade_ctx') and api_client.hk_trade_ctx:
                api_client.hk_trade_ctx.close()
                api_client.hk_trade_ctx = None
                contexts_cleaned += 1

            # Cleanup US trade context
            if hasattr(api_client, 'us_trade_ctx') and api_client.us_trade_ctx:
                api_client.us_trade_ctx.close()
                api_client.us_trade_ctx = None
                contexts_cleaned += 1

            api_client._log_info(f"Cleaned up {contexts_cleaned} contexts")

        except Exception as e:
            if api_client:
                api_client._log_error(f"Unexpected error during context cleanup: {e}")

    def get_context_status(self) -> Dict[str, Any]:
        """Get status information for all contexts."""
        api_client = self._api_client_ref()
        if not api_client:
            return {"error": "API client reference is dead"}

        status = {
            "quote_context": self._get_quote_context_status(api_client),
            "hk_trade_context": self._get_hk_trade_context_status(api_client),
            "us_trade_context": self._get_us_trade_context_status(api_client),
        }

        return status

    def get_trade_context(self, market: str) -> Optional[Any]:
        """Get trade context for specified market."""
        api_client = self._api_client_ref()
        if not api_client:
            return None

        if market.upper() == "HK":
            return getattr(api_client, 'hk_trade_ctx', None)
        elif market.upper() == "US":
            return getattr(api_client, 'us_trade_ctx', None)
        else:
            api_client._log_error(f"Unknown market: {market}")
            return None

    def test_contexts(self) -> Dict[str, Union[str, Dict[str, Union[str, Optional[Any]]]]]:
        """Test all active contexts to verify connectivity."""
        api_client = self._api_client_ref()
        if not api_client:
            return {"error": "API client reference is dead"}

        results = {}

        # Test quote context
        results["quote_context"] = self._test_quote_context(api_client)
        
        # Test HK trade context
        results["hk_trade_context"] = self._test_hk_trade_context(api_client)
        
        # Test US trade context
        results["us_trade_context"] = self._test_us_trade_context(api_client)

        return results

    def _get_quote_context_status(self, api_client: 'FutuApiClient') -> Dict[str, Union[bool, str, Any]]:
        """Get quote context status."""
        if not hasattr(api_client, 'quote_ctx') or not api_client.quote_ctx:
            return {"active": False, "error": "Not initialized"}
        try:
            ret, data = api_client.quote_ctx.get_global_state()
            return {"active": True, "connected": ret == ft.RET_OK, "global_state": data if ret == ft.RET_OK else f"Error: {data}"}
        except Exception as e:
            return {"active": True, "connected": False, "error": str(e)}

    def _get_hk_trade_context_status(self, api_client: 'FutuApiClient') -> Dict[str, Union[bool, str, Any]]:
        """Get HK trade context status."""
        if not hasattr(api_client, 'hk_trade_ctx') or not api_client.hk_trade_ctx:
            return {"active": False, "error": "Not initialized"}
        try:
            ret, data = api_client.hk_trade_ctx.get_acc_info()
            return {"active": True, "connected": ret == ft.RET_OK, "account_info": data if ret == ft.RET_OK else f"Error: {data}"}
        except Exception as e:
            return {"active": True, "connected": False, "error": str(e)}

    def _get_us_trade_context_status(self, api_client: 'FutuApiClient') -> Dict[str, Union[bool, str, Any]]:
        """Get US trade context status."""
        if not hasattr(api_client, 'us_trade_ctx') or not api_client.us_trade_ctx:
            return {"active": False, "error": "Not initialized"}
        try:
            ret, data = api_client.us_trade_ctx.get_acc_info()
            return {"active": True, "connected": ret == ft.RET_OK, "account_info": data if ret == ft.RET_OK else f"Error: {data}"}
        except Exception as e:
            return {"active": True, "connected": False, "error": str(e)}

    def _test_quote_context(self, api_client: 'FutuApiClient') -> Dict[str, Union[str, Optional[Any]]]:
        """Test quote context connectivity."""
        if not hasattr(api_client, 'quote_ctx') or not api_client.quote_ctx:
            return {"status": "not_available", "message": "Quote context not initialized"}
        try:
            ret, data = api_client.quote_ctx.get_global_state()
            return {"status": "success" if ret == ft.RET_OK else "error", "message": "Connection successful" if ret == ft.RET_OK else f"Error: {data}", "data": data if ret == ft.RET_OK else None}
        except Exception as e:
            return {"status": "error", "message": f"Test failed: {e}"}

    def _test_hk_trade_context(self, api_client: 'FutuApiClient') -> Dict[str, Union[str, Optional[Any]]]:
        """Test HK trade context connectivity."""
        if not hasattr(api_client, 'hk_trade_ctx') or not api_client.hk_trade_ctx:
            return {"status": "not_available", "message": "HK trade context not initialized"}
        try:
            ret, data = api_client.hk_trade_ctx.get_acc_info()
            return {"status": "success" if ret == ft.RET_OK else "error", "message": "Connection successful" if ret == ft.RET_OK else f"Error: {data}", "data": data if ret == ft.RET_OK else None}
        except Exception as e:
            return {"status": "error", "message": f"Test failed: {e}"}

    def _test_us_trade_context(self, api_client: 'FutuApiClient') -> Dict[str, Union[str, Optional[Any]]]:
        """Test US trade context connectivity."""
        if not hasattr(api_client, 'us_trade_ctx') or not api_client.us_trade_ctx:
            return {"status": "not_available", "message": "US trade context not initialized"}
        try:
            ret, data = api_client.us_trade_ctx.get_acc_info()
            return {"status": "success" if ret == ft.RET_OK else "error", "message": "Connection successful" if ret == ft.RET_OK else f"Error: {data}", "data": data if ret == ft.RET_OK else None}
        except Exception as e:
            return {"status": "error", "message": f"Test failed: {e}"}