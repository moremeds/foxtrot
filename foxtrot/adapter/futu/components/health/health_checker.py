"""
Health checking logic for Futu connections.

This module provides health validation algorithms for Futu OpenD 
gateway connections including quote and trade context checks.
"""

import weakref
from typing import Any

import futu as ft


class HealthChecker:
    """Health checking functionality for Futu connections."""

    def __init__(self, api_client_ref: weakref.ref, logger_ref):
        """Initialize health checker."""
        self._api_client_ref = api_client_ref
        self._logger_ref = logger_ref

    def check_connection_health(self) -> bool:
        """
        Check if connections are healthy.

        Returns:
            True if all connections are healthy, False otherwise
        """
        api_client = self._api_client_ref()
        if not api_client:
            return False

        try:
            # Check quote context
            if not api_client.quote_ctx:
                return False

            ret, data = api_client.quote_ctx.get_global_state()
            if ret != ft.RET_OK:
                self._log_error(f"Quote context health check failed: {data}")
                return False

            # Check HK trade context if enabled
            if (hasattr(api_client, 'hk_access') and api_client.hk_access and 
                api_client.trade_ctx_hk):
                if not self._check_trade_context_health(api_client.trade_ctx_hk, "HK"):
                    return False

            # Check US trade context if enabled  
            if (hasattr(api_client, 'us_access') and api_client.us_access and
                api_client.trade_ctx_us):
                if not self._check_trade_context_health(api_client.trade_ctx_us, "US"):
                    return False

            return True

        except Exception as e:
            self._log_error(f"Connection health check error: {e}")
            return False

    def _check_trade_context_health(self, trade_ctx: Any, market: str) -> bool:
        """
        Check health of a specific trade context.
        
        Args:
            trade_ctx: Trade context to check
            market: Market identifier for logging
            
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check for trade context
            ret, _ = trade_ctx.get_acc_list()
            if ret != ft.RET_OK:
                self._log_error(f"{market} trade context health check failed")
                return False
            return True
        except Exception as e:
            self._log_error(f"{market} trade context health check error: {e}")
            # Don't fail health check for trade context errors if not critical
            return True

    def force_health_check(self) -> bool:
        """
        Force an immediate health check.
        
        Returns:
            True if connections are healthy, False otherwise
        """
        return self.check_connection_health()

    def _log_error(self, msg: str) -> None:
        """Log error message through logger."""
        logger = self._logger_ref()
        if logger:
            logger.log_error(msg)