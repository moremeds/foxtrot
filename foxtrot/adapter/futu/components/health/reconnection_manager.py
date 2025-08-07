"""
Reconnection management for Futu connections.

This module handles connection recovery operations including cleanup,
reconnection attempts, and subscription restoration.
"""

import time
import weakref


class ReconnectionManager:
    """Reconnection and cleanup operations for Futu connections."""

    def __init__(self, api_client_ref: weakref.ref, logger_ref):
        """Initialize reconnection manager."""
        self._api_client_ref = api_client_ref
        self._logger_ref = logger_ref
        self._reconnect_attempts = 0

    def attempt_reconnection(self, max_attempts: int, reconnect_interval: int) -> None:
        """Attempt to reconnect to OpenD gateway."""
        if self._reconnect_attempts >= max_attempts:
            self._log_error(f"Max reconnection attempts ({max_attempts}) reached, giving up")
            return

        self._reconnect_attempts += 1
        self._log_info(f"Reconnection attempt {self._reconnect_attempts}/{max_attempts}")

        api_client = self._api_client_ref()
        if not api_client:
            self._log_error("Cannot reconnect: API client reference is dead")
            return

        try:
            # Clean up existing connections
            self._cleanup_connections()

            # Wait before reconnecting
            time.sleep(reconnect_interval)

            # Attempt reconnection using last settings
            if hasattr(api_client, 'last_settings') and api_client.last_settings:
                if api_client.connect(api_client.last_settings):
                    self._log_info("Reconnection successful")
                    self._reconnect_attempts = 0  # Reset counter on success

                    # Restore subscriptions if market data manager exists
                    if hasattr(api_client, 'market_data') and api_client.market_data:
                        try:
                            api_client.market_data.restore_subscriptions()
                        except Exception as e:
                            self._log_error(f"Failed to restore subscriptions after reconnection: {e}")

                else:
                    self._log_error(f"Reconnection attempt {self._reconnect_attempts} failed")
            else:
                self._log_error("Cannot reconnect: no previous connection settings available")

        except Exception as e:
            self._log_error(f"Reconnection error: {e}")

    def _cleanup_connections(self) -> None:
        """Clean up existing connections without full close."""
        api_client = self._api_client_ref()
        if not api_client:
            return

        try:
            if hasattr(api_client, 'quote_ctx') and api_client.quote_ctx:
                api_client.quote_ctx.close()
                api_client.quote_ctx = None

            if hasattr(api_client, 'trade_ctx_hk') and api_client.trade_ctx_hk:
                api_client.trade_ctx_hk.close()
                api_client.trade_ctx_hk = None

            if hasattr(api_client, 'trade_ctx_us') and api_client.trade_ctx_us:
                api_client.trade_ctx_us.close()
                api_client.trade_ctx_us = None

            self._log_info("Connections cleaned up for reconnection")

        except Exception as e:
            self._log_error(f"Connection cleanup error: {e}")

    def reset_reconnect_attempts(self) -> None:
        """Reset the reconnection attempt counter."""
        self._reconnect_attempts = 0
        self._log_info("Reconnection attempt counter reset")

    def get_reconnect_attempts(self) -> int:
        """Get current reconnection attempt count."""
        return self._reconnect_attempts

    def _log_info(self, msg: str) -> None:
        """Log info message through logger."""
        logger = self._logger_ref()
        if logger:
            logger.log_info(msg)

    def _log_error(self, msg: str) -> None:
        """Log error message through logger."""
        logger = self._logger_ref()
        if logger:
            logger.log_error(msg)