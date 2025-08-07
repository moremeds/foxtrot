"""
Futu context initialization module.

This module handles the initialization of Futu SDK contexts including
quote context and trade contexts for different markets.
"""

import time
from typing import Any, Dict

import futu as ft


class FutuContextInitializer:
    """Handles initialization of Futu SDK contexts."""

    def __init__(self, api_client_ref):
        """Initialize with weak reference to API client."""
        self._api_client_ref = api_client_ref

    def initialize_all_contexts(self, host: str, port: int, settings: Dict[str, Any]) -> bool:
        """Initialize all OpenD contexts with proper error handling."""
        api_client = self._api_client_ref()
        if not api_client:
            return False

        try:
            # Initialize quote context first
            if not self.initialize_quote_context(api_client, host, port):
                return False

            # Initialize HK trade context if enabled
            if settings.get("enable_hk_trading", False):
                if not self.initialize_hk_trade_context(api_client, host, port, settings):
                    api_client._log_error("Failed to initialize HK trade context")
                    return False

            # Initialize US trade context if enabled
            if settings.get("enable_us_trading", False):
                if not self.initialize_us_trade_context(api_client, host, port, settings):
                    api_client._log_error("Failed to initialize US trade context")
                    return False

            api_client._log_info("All contexts initialized successfully")
            return True

        except Exception as e:
            api_client._log_error(f"Context initialization failed: {e}")
            return False

    def initialize_quote_context(self, api_client: Any, host: str, port: int) -> bool:
        """Initialize quote context for market data."""
        try:
            api_client.quote_ctx = ft.OpenQuoteContext(host=host, port=port)
            
            # Test connection
            ret, data = api_client.quote_ctx.get_global_state()
            if ret != ft.RET_OK:
                api_client._log_error(f"Quote context connection test failed: {data}")
                return False

            api_client._log_info("Quote context initialized successfully")
            return True

        except Exception as e:
            api_client._log_error(f"Quote context initialization failed: {e}")
            return False

    def initialize_hk_trade_context(
        self, api_client: Any, host: str, port: int, settings: Dict[str, Any]
    ) -> bool:
        """Initialize Hong Kong trade context."""
        try:
            trd_env = settings.get("hk_trade_env", ft.TrdEnv.SIMULATE)
            api_client.hk_trade_ctx = ft.OpenHKTradeContext(host=host, port=port, trd_env=trd_env)
            
            # Test connection with account info
            ret, data = api_client.hk_trade_ctx.get_acc_info()
            if ret != ft.RET_OK:
                api_client._log_error(f"HK trade context test failed: {data}")
                return False

            api_client._log_info(f"HK trade context initialized (env: {trd_env.name})")
            return True

        except Exception as e:
            api_client._log_error(f"HK trade context initialization failed: {e}")
            return False

    def initialize_us_trade_context(
        self, api_client: Any, host: str, port: int, settings: Dict[str, Any]
    ) -> bool:
        """Initialize US trade context."""
        try:
            trd_env = settings.get("us_trade_env", ft.TrdEnv.SIMULATE)
            api_client.us_trade_ctx = ft.OpenUSTradeContext(host=host, port=port, trd_env=trd_env)
            
            # Test connection with account info
            ret, data = api_client.us_trade_ctx.get_acc_info()
            if ret != ft.RET_OK:
                api_client._log_error(f"US trade context test failed: {data}")
                return False

            api_client._log_info(f"US trade context initialized (env: {trd_env.name})")
            return True

        except Exception as e:
            api_client._log_error(f"US trade context initialization failed: {e}")
            return False