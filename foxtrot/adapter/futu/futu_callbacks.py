"""
Futu SDK callback handlers for real-time data processing.

This module implements the callback handlers required by the Futu SDK
to process real-time market data and trading events.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from foxtrot.util.constants import Exchange
from foxtrot.util.object import OrderData, TickData, TradeData
import futu as ft

from .futu_mappings import (
    convert_futu_order_status,
    convert_futu_to_vt_direction,
    convert_futu_to_vt_order_type,
    convert_futu_to_vt_symbol,
)

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuQuoteHandler(ft.StockQuoteHandlerBase):
    """
    SDK callback handler for market data quotes.

    This handler processes real-time market data updates from the Futu SDK
    and converts them to VT TickData objects for the event system.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the quote handler."""
        super().__init__()
        self.api_client = api_client

    def on_recv_rsp(self, rsp_pb) -> tuple[int, Any]:
        """
        Handle real-time quote data callbacks from SDK.

        Args:
            rsp_pb: Protobuf response from SDK

        Returns:
            Tuple of (return_code, content)
        """
        try:
            ret_code, content = super().on_recv_rsp(rsp_pb)
            if ret_code != ft.RET_OK:
                return ft.RET_ERROR, content

            # Process each quote data item
            if isinstance(content, list):
                for quote_data in content:
                    tick = self._convert_to_tick_data(quote_data)
                    if tick:
                        # Fire tick event through adapter
                        if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                            self.api_client.adapter.on_tick(tick)
            else:
                # Single quote data item
                tick = self._convert_to_tick_data(content)
                if tick:
                    if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                        self.api_client.adapter.on_tick(tick)

            return ft.RET_OK, content

        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Quote handler error: {e}")
            return ft.RET_ERROR, str(e)

    def _convert_to_tick_data(self, quote_data: dict) -> TickData | None:
        """
        Convert SDK quote data to VT TickData object.

        Args:
            quote_data: Quote data from SDK

        Returns:
            TickData object or None if conversion fails
        """
        try:
            # Extract basic info
            code = quote_data.get("code", "")
            if not code:
                return None

            # Determine market from code format
            if code.startswith("HK."):
                market = "HK"
            elif code.startswith("US."):
                market = "US"
            elif code.startswith("CN."):
                market = "CN"
            else:
                # Try to infer from code format
                if len(code) == 5 and code.isdigit():
                    market = "HK"  # Hong Kong stock
                else:
                    market = "US"  # Default to US

            # Convert to VT symbol format
            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")
            exchange = Exchange(exchange_str)

            # Create TickData object
            return TickData(
                symbol=symbol,
                exchange=exchange,
                datetime=datetime.now(),  # Use current time as SDK may not provide timestamp
                name=quote_data.get("name", ""),

                # Price data
                last_price=float(quote_data.get("last_price", 0)) or 0.0,
                open_price=float(quote_data.get("open_price", 0)) or 0.0,
                high_price=float(quote_data.get("high_price", 0)) or 0.0,
                low_price=float(quote_data.get("low_price", 0)) or 0.0,
                pre_close=float(quote_data.get("prev_close_price", 0)) or 0.0,

                # Volume data
                volume=float(quote_data.get("volume", 0)) or 0.0,
                turnover=float(quote_data.get("turnover", 0)) or 0.0,

                # Order book data (5 levels)
                bid_price_1=float(quote_data.get("bid_price_1", 0)) or 0.0,
                ask_price_1=float(quote_data.get("ask_price_1", 0)) or 0.0,
                bid_volume_1=float(quote_data.get("bid_volume_1", 0)) or 0.0,
                ask_volume_1=float(quote_data.get("ask_volume_1", 0)) or 0.0,

                bid_price_2=float(quote_data.get("bid_price_2", 0)) or 0.0,
                ask_price_2=float(quote_data.get("ask_price_2", 0)) or 0.0,
                bid_volume_2=float(quote_data.get("bid_volume_2", 0)) or 0.0,
                ask_volume_2=float(quote_data.get("ask_volume_2", 0)) or 0.0,

                bid_price_3=float(quote_data.get("bid_price_3", 0)) or 0.0,
                ask_price_3=float(quote_data.get("ask_price_3", 0)) or 0.0,
                bid_volume_3=float(quote_data.get("bid_volume_3", 0)) or 0.0,
                ask_volume_3=float(quote_data.get("ask_volume_3", 0)) or 0.0,

                bid_price_4=float(quote_data.get("bid_price_4", 0)) or 0.0,
                ask_price_4=float(quote_data.get("ask_price_4", 0)) or 0.0,
                bid_volume_4=float(quote_data.get("bid_volume_4", 0)) or 0.0,
                ask_volume_4=float(quote_data.get("ask_volume_4", 0)) or 0.0,

                bid_price_5=float(quote_data.get("bid_price_5", 0)) or 0.0,
                ask_price_5=float(quote_data.get("ask_price_5", 0)) or 0.0,
                bid_volume_5=float(quote_data.get("bid_volume_5", 0)) or 0.0,
                ask_volume_5=float(quote_data.get("ask_volume_5", 0)) or 0.0,

                # Additional fields
                adapter_name=self.api_client.adapter_name,
            )


        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Tick conversion failed: {e}")
            return None


class FutuTradeHandler(ft.TradeOrderHandlerBase):
    """
    SDK callback handler for trade and order updates.

    This handler processes real-time trading events from the Futu SDK
    and converts them to VT OrderData and TradeData objects.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the trade handler."""
        super().__init__()
        self.api_client = api_client

    def on_recv_rsp(self, rsp_pb) -> tuple[int, Any]:
        """
        Handle trade and order update callbacks from SDK.

        Args:
            rsp_pb: Protobuf response from SDK

        Returns:
            Tuple of (return_code, content)
        """
        try:
            ret_code, content = super().on_recv_rsp(rsp_pb)
            if ret_code != ft.RET_OK:
                return ft.RET_ERROR, content

            # Process order/trade updates
            if isinstance(content, list):
                for data_item in content:
                    self._process_trade_update(data_item)
            else:
                self._process_trade_update(content)

            return ft.RET_OK, content

        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Trade handler error: {e}")
            return ft.RET_ERROR, str(e)

    def _process_trade_update(self, update_data: dict) -> None:
        """
        Process individual trade/order update.

        Args:
            update_data: Update data from SDK
        """
        try:
            # Determine update type and process accordingly
            if "order_id" in update_data:
                self._process_order_update(update_data)
            elif "deal_id" in update_data:
                self._process_trade_update_data(update_data)

        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Trade update processing failed: {e}")

    def _process_order_update(self, order_data: dict) -> None:
        """
        Convert SDK order data to VT OrderData and fire events.

        Args:
            order_data: Order update data from SDK
        """
        try:
            # Extract code and determine market
            code = order_data.get("code", "")
            if not code:
                return

            # Determine market from code
            if code.startswith("HK."):
                market = "HK"
            elif code.startswith("US."):
                market = "US"
            elif code.startswith("CN."):
                market = "CN"
            else:
                # Default inference
                market = "HK" if len(code) == 5 and code.isdigit() else "US"

            # Convert to VT symbol
            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")

            # Create OrderData object
            order = OrderData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                orderid=str(order_data.get("order_id", "")),
                type=convert_futu_to_vt_order_type(order_data.get("order_type", ft.OrderType.NORMAL)),
                direction=convert_futu_to_vt_direction(order_data.get("trd_side", ft.TrdSide.BUY)),
                volume=float(order_data.get("qty", 0)),
                price=float(order_data.get("price", 0)),
                traded=float(order_data.get("dealt_qty", 0)),
                status=convert_futu_order_status(order_data.get("order_status", ft.OrderStatus.NONE)),
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )

            # Update order manager state if available
            if self.api_client.order_manager:
                self.api_client.order_manager.on_order_update(order)

            # Fire order event through adapter
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.on_order(order)

        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Order update processing failed: {e}")

    def _process_trade_update_data(self, trade_data: dict) -> None:
        """
        Convert SDK trade data to VT TradeData and fire events.

        Args:
            trade_data: Trade data from SDK
        """
        try:
            # Extract code and determine market
            code = trade_data.get("code", "")
            if not code:
                return

            # Determine market from code
            if code.startswith("HK."):
                market = "HK"
            elif code.startswith("US."):
                market = "US"
            elif code.startswith("CN."):
                market = "CN"
            else:
                market = "HK" if len(code) == 5 and code.isdigit() else "US"

            # Convert to VT symbol
            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")

            # Create TradeData object
            trade = TradeData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                orderid=str(trade_data.get("order_id", "")),
                tradeid=str(trade_data.get("deal_id", "")),
                direction=convert_futu_to_vt_direction(trade_data.get("trd_side", ft.TrdSide.BUY)),
                volume=float(trade_data.get("qty", 0)),
                price=float(trade_data.get("price", 0)),
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )

            # Fire trade event through adapter
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.on_trade(trade)

        except Exception as e:
            if hasattr(self.api_client, 'adapter') and self.api_client.adapter:
                self.api_client.adapter.write_log(f"Trade update processing failed: {e}")
