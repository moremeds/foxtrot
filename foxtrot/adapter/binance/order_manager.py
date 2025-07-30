"""
Binance Order Manager - Handles order lifecycle management.

This module manages order operations including creation, tracking, cancellation,
and trade event generation.
"""

from datetime import datetime
import threading
from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import CancelRequest, OrderData, OrderRequest

# datetime import removed - using datetime.now() directly

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


class BinanceOrderManager:
    """
    Manager for Binance order operations.

    Handles order creation, tracking, cancellation, and status updates.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the order manager."""
        self.api_client = api_client
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()
        self._local_order_id = 0

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order to Binance.

        Args:
            req: Order request object

        Returns:
            Local order ID string
        """
        try:
            if not self.api_client.exchange:
                self.api_client._log_error("Exchange not connected")
                return ""

            # Generate local order ID
            with self._order_lock:
                self._local_order_id += 1
                local_orderid = f"{self.api_client.adapter_name}_{self._local_order_id}"

            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.symbol)
            if not ccxt_symbol:
                self.api_client._log_error(f"Invalid symbol: {req.symbol}")
                return ""

            # Convert order parameters
            side = "buy" if req.direction == Direction.LONG else "sell"
            order_type = self._convert_order_type_to_ccxt(req.type)

            # Create order data
            order = OrderData(
                adapter_name=self.api_client.adapter_name,
                symbol=req.symbol,
                exchange=Exchange.BINANCE,
                orderid=local_orderid,
                type=req.type,
                direction=req.direction,
                volume=req.volume,
                price=req.price,
                status=Status.SUBMITTING,
                datetime=datetime.now(),
            )

            # Store order locally
            with self._order_lock:
                self._orders[local_orderid] = order

            # Send order to exchange
            if order_type == "market":
                result = self.api_client.exchange.create_market_order(ccxt_symbol, side, req.volume)
            else:
                result = self.api_client.exchange.create_limit_order(
                    ccxt_symbol, side, req.volume, req.price
                )

            if result:
                # Update order with exchange information
                order.orderid = str(result.get("id", local_orderid))
                order.status = self._convert_status_from_ccxt(result.get("status", "open"))

                with self._order_lock:
                    self._orders[local_orderid] = order

                self.api_client._log_info(f"Order sent successfully: {local_orderid}")
                return local_orderid
            self.api_client._log_error("Failed to send order - no response")
            return ""

        except Exception as e:
            self.api_client._log_error(f"Failed to send order: {str(e)}")
            return ""

    def cancel_order(self, req: CancelRequest) -> bool:
        """
        Cancel an order.

        Args:
            req: Cancel request object

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            if not self.api_client.exchange:
                return False

            with self._order_lock:
                order = self._orders.get(req.orderid)

            if not order:
                self.api_client._log_error(f"Order not found: {req.orderid}")
                return False

            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(order.symbol)
            if not ccxt_symbol:
                return False

            # Cancel order on exchange
            result = self.api_client.exchange.cancel_order(order.orderid, ccxt_symbol)

            if result:
                # Update order status
                order.status = Status.CANCELLED
                with self._order_lock:
                    self._orders[req.orderid] = order

                self.api_client._log_info(f"Order cancelled: {req.orderid}")
                return True
            return False

        except Exception as e:
            self.api_client._log_error(f"Failed to cancel order: {str(e)}")
            return False

    def query_order(self, orderid: str) -> OrderData | None:
        """
        Query order status.

        Args:
            orderid: Order ID to query

        Returns:
            OrderData if found, None otherwise
        """
        with self._order_lock:
            return self._orders.get(orderid)

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """
        Convert VT symbol format to CCXT format.

        Args:
            vt_symbol: Symbol in VT format (e.g., "BTCUSDT.BINANCE")

        Returns:
            Symbol in CCXT format (e.g., "BTC/USDT")
        """
        try:
            # Must contain a dot for valid VT symbol format
            if "." not in vt_symbol:
                return ""

            symbol = vt_symbol.split(".")[0]

            # Validate minimum symbol length
            if len(symbol) < 3:
                return ""

            # Convert BTCUSDT to BTC/USDT format
            if symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            if symbol.endswith("BTC") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            if symbol.endswith("ETH") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            # Unknown format - default to USDT pair
            return f"{symbol}/USDT"
        except Exception:
            return ""

    def _convert_order_type_to_ccxt(self, order_type: OrderType) -> str:
        """Convert VT order type to CCXT format."""
        if order_type == OrderType.MARKET:
            return "market"
        if order_type == OrderType.LIMIT:
            return "limit"
        return "limit"  # Default to limit

    def _convert_status_from_ccxt(self, ccxt_status: str) -> Status:
        """Convert CCXT order status to VT format."""
        status_map = {
            "open": Status.NOTTRADED,
            "closed": Status.ALLTRADED,
            "canceled": Status.CANCELLED,
            "cancelled": Status.CANCELLED,
            "partial": Status.PARTTRADED,
            "expired": Status.CANCELLED,
        }
        return status_map.get(ccxt_status.lower(), Status.SUBMITTING)
