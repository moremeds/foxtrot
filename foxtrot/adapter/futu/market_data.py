"""
Futu market data manager for real-time market data subscriptions.

This module handles market data subscriptions via the Futu OpenD gateway,
managing WebSocket connections and processing real-time tick data.
"""

from typing import TYPE_CHECKING

from foxtrot.util.object import SubscribeRequest
import futu as ft

from .futu_mappings import convert_symbol_to_futu_market, validate_symbol_format

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuMarketData:
    """
    Market data manager for Futu OpenD gateway subscriptions.

    Handles real-time market data subscriptions across HK, US, and CN markets
    using the official Futu SDK callback system.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the market data manager."""
        self.api_client = api_client
        self.subscriptions: dict[str, dict] = {}  # Track active subscriptions

    def subscribe(self, req: SubscribeRequest) -> bool:
        """
        Subscribe to real-time market data via SDK.

        Args:
            req: Subscription request with VT symbol

        Returns:
            True if subscription successful, False otherwise
        """
        try:
            # Validate symbol format
            if not validate_symbol_format(req.vt_symbol):
                self.api_client._log_error(f"Invalid symbol format: {req.vt_symbol}")
                return False

            # Check if already subscribed
            if req.vt_symbol in self.subscriptions:
                self.api_client._log_info(f"Already subscribed to {req.vt_symbol}")
                return True

            # Convert VT symbol to Futu format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)

            # Subscribe via SDK quote context
            if not self.api_client.quote_ctx:
                self.api_client._log_error("Quote context not available")
                return False

            # Subscribe to multiple data types
            ret, data = self.api_client.quote_ctx.subscribe(
                code_list=[code],
                subtype_list=[
                    ft.SubType.QUOTE,      # Real-time quotes
                    ft.SubType.ORDER_BOOK, # Order book data
                    ft.SubType.TICKER,     # Tick-by-tick data
                ]
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Subscription failed for {req.vt_symbol}: {data}")
                return False

            # Track subscription
            self.subscriptions[req.vt_symbol] = {
                "market": market,
                "code": code,
                "subtypes": [ft.SubType.QUOTE, ft.SubType.ORDER_BOOK, ft.SubType.TICKER],
                "timestamp": None,  # Could add timestamp tracking if needed
            }

            self.api_client._log_info(f"Successfully subscribed to {req.vt_symbol}")
            return True

        except Exception as e:
            self.api_client._log_error(f"Subscription error for {req.vt_symbol}: {e}")
            return False

    def unsubscribe(self, req: SubscribeRequest) -> bool:
        """
        Unsubscribe from market data.

        Args:
            req: Subscription request

        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            if req.vt_symbol not in self.subscriptions:
                return True  # Already unsubscribed

            # Get subscription info
            subscription = self.subscriptions[req.vt_symbol]
            code = subscription["code"]

            # Unsubscribe via SDK
            if self.api_client.quote_ctx:
                ret, data = self.api_client.quote_ctx.unsubscribe(
                    code_list=[code],
                    subtype_list=subscription["subtypes"]
                )

                if ret != ft.RET_OK:
                    self.api_client._log_error(f"Unsubscription failed for {req.vt_symbol}: {data}")
                    return False

            # Remove from tracking
            del self.subscriptions[req.vt_symbol]
            self.api_client._log_info(f"Unsubscribed from {req.vt_symbol}")
            return True

        except Exception as e:
            self.api_client._log_error(f"Unsubscription error for {req.vt_symbol}: {e}")
            return False

    def restore_subscriptions(self) -> None:
        """
        Restore all subscriptions after reconnection with optimized batching.

        This method is called during connection recovery to resubscribe
        to all previously active market data feeds using efficient batch operations.
        """
        try:
            if not self.subscriptions:
                return

            self.api_client._log_info(f"Restoring {len(self.subscriptions)} subscriptions")

            # Collect all codes to resubscribe with batch size optimization
            codes_to_subscribe = []
            failed_symbols = []

            for _vt_symbol, subscription in self.subscriptions.items():
                codes_to_subscribe.append(subscription["code"])

            # Process in batches to avoid overwhelming the SDK
            batch_size = min(50, len(codes_to_subscribe))  # Optimal batch size

            for i in range(0, len(codes_to_subscribe), batch_size):
                batch_codes = codes_to_subscribe[i:i + batch_size]

                if batch_codes and self.api_client.quote_ctx:
                    ret, data = self.api_client.quote_ctx.subscribe(
                        code_list=batch_codes,
                        subtype_list=[ft.SubType.QUOTE, ft.SubType.ORDER_BOOK, ft.SubType.TICKER]
                    )

                    if ret != ft.RET_OK:
                        self.api_client._log_error(f"Batch {i//batch_size + 1} subscription restore failed: {data}")
                        # Track failed codes for individual retry
                        failed_symbols.extend(batch_codes)
                    else:
                        self.api_client._log_info(f"Batch {i//batch_size + 1} restored successfully ({len(batch_codes)} symbols)")

            # Retry failed subscriptions individually
            if failed_symbols:
                self.api_client._log_info(f"Retrying {len(failed_symbols)} failed subscriptions individually")
                self._retry_failed_subscriptions(failed_symbols)
            else:
                self.api_client._log_info("All subscriptions restored successfully")

        except Exception as e:
            self.api_client._log_error(f"Subscription restore error: {e}")

    def _retry_failed_subscriptions(self, failed_codes: list[str]) -> None:
        """
        Retry failed subscriptions individually with exponential backoff.

        Args:
            failed_codes: List of Futu codes that failed batch subscription
        """
        import time

        retry_delay = 1.0  # Start with 1 second delay
        max_delay = 30.0   # Maximum delay of 30 seconds

        for code in failed_codes:
            try:
                if self.api_client.quote_ctx:
                    ret, data = self.api_client.quote_ctx.subscribe(
                        code_list=[code],
                        subtype_list=[ft.SubType.QUOTE, ft.SubType.ORDER_BOOK, ft.SubType.TICKER]
                    )

                    if ret == ft.RET_OK:
                        self.api_client._log_info(f"Successfully restored subscription for {code}")
                        retry_delay = 1.0  # Reset delay on success
                    else:
                        self.api_client._log_error(f"Failed to restore subscription for {code}: {data}")
                        # Exponential backoff
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_delay)

            except Exception as e:
                self.api_client._log_error(f"Error retrying subscription for {code}: {e}")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    def get_subscription_count(self) -> int:
        """Get the number of active subscriptions."""
        return len(self.subscriptions)

    def get_subscribed_symbols(self) -> list[str]:
        """Get list of currently subscribed VT symbols."""
        return list(self.subscriptions.keys())
