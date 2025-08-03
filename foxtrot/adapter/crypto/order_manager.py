"""
Crypto Order Manager - Handles order lifecycle management.
"""

from datetime import datetime
import threading
import traceback
from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import CancelRequest, OrderData, OrderRequest
from foxtrot.util.logger import get_adapter_logger

if TYPE_CHECKING:
    from .crypto_adapter import CryptoAdapter


class OrderManager:
    """
    Manager for Crypto order operations.
    """

    def __init__(self, adapter: "CryptoAdapter"):
        """Initialize the order manager."""
        self.adapter = adapter
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()
        self._local_order_id = 0
        
        # Adapter-specific logger
        self._logger = get_adapter_logger("CryptoOrder")

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order to the exchange.
        """
        try:
            if not self.adapter.exchange:
                # MIGRATION: Replace print with ERROR logging
                self._logger.error("Exchange not connected for order placement")
                return ""

            with self._order_lock:
                self._local_order_id += 1
                local_orderid = f"{self.adapter.adapter_name}_{self._local_order_id}"

            ccxt_symbol = self._convert_symbol_to_ccxt(req.symbol)
            if not ccxt_symbol:
                # MIGRATION: Replace print with WARNING logging
                self._logger.warning("Invalid symbol provided for order", extra={"symbol": req.symbol})
                return ""

            side = "buy" if req.direction == Direction.LONG else "sell"
            order_type = self._convert_order_type_to_ccxt(req.type)

            order = OrderData(
                adapter_name=self.adapter.adapter_name,
                symbol=req.symbol,
                exchange=Exchange[self.adapter.exchange_name.upper()],
                orderid=local_orderid,
                type=req.type,
                direction=req.direction,
                volume=req.volume,
                price=req.price,
                status=Status.SUBMITTING,
                datetime=datetime.now(),
            )

            with self._order_lock:
                self._orders[local_orderid] = order

            if order_type == "market":
                result = self.adapter.exchange.create_market_order(ccxt_symbol, side, req.volume)
            else:
                result = self.adapter.exchange.create_limit_order(
                    ccxt_symbol, side, req.volume, req.price
                )

            if result:
                order.orderid = str(result.get("id", local_orderid))
                order.status = self._convert_status_from_ccxt(result.get("status", "open"))

                with self._order_lock:
                    self._orders[local_orderid] = order

                # MIGRATION: Replace print with INFO logging
                self._logger.info("Order sent successfully", extra={"order_id": local_orderid})
                return local_orderid
            
            # MIGRATION: Replace print with ERROR logging
            self._logger.error("Failed to send order - no response from exchange")
            return ""

        except Exception as e:
            # MIGRATION: Replace print with ERROR logging
            self._logger.error(
                "Failed to send order",
                extra={
                    "symbol": req.symbol,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            traceback.print_exc()
            return ""

    def cancel_order(self, req: CancelRequest) -> bool:
        """
        Cancel an order.
        """
        try:
            if not self.adapter.exchange:
                return False

            with self._order_lock:
                order = self._orders.get(req.orderid)

            if not order:
                # MIGRATION: Replace print with WARNING logging
                self._logger.warning("Order not found for cancellation", extra={"order_id": req.orderid})
                return False

            ccxt_symbol = self._convert_symbol_to_ccxt(order.symbol)
            if not ccxt_symbol:
                return False

            result = self.adapter.exchange.cancel_order(order.orderid, ccxt_symbol)

            if result:
                order.status = Status.CANCELLED
                with self._order_lock:
                    self._orders[req.orderid] = order

                # MIGRATION: Replace print with INFO logging
                self._logger.info("Order cancelled successfully", extra={"order_id": req.orderid})
                return True
            return False

        except Exception as e:
            # MIGRATION: Replace print with ERROR logging
            self._logger.error(
                "Failed to cancel order",
                extra={
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            return False

    def query_order(self, orderid: str) -> OrderData | None:
        """
        Query order status.
        """
        with self._order_lock:
            return self._orders.get(orderid)

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """
        Convert VT symbol format to CCXT format.
        """
        try:
            if "." not in vt_symbol:
                return ""

            symbol = vt_symbol.split(".")[0]

            if len(symbol) < 3:
                return ""

            if symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            if symbol.endswith("BTC") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            if symbol.endswith("ETH") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            return f"{symbol}/USDT"
        except Exception:
            return ""

    def _convert_order_type_to_ccxt(self, order_type: OrderType) -> str:
        """
        Convert VT order type to CCXT format.
        """
        if order_type == OrderType.MARKET:
            return "market"
        if order_type == OrderType.LIMIT:
            return "limit"
        return "limit"

    def _convert_status_from_ccxt(self, ccxt_status: str) -> Status:
        """
        Convert CCXT order status to VT format.
        """
        status_map = {
            "open": Status.NOTTRADED,
            "closed": Status.ALLTRADED,
            "canceled": Status.CANCELLED,
            "cancelled": Status.CANCELLED,
            "partial": Status.PARTTRADED,
            "expired": Status.CANCELLED,
        }
        return status_map.get(ccxt_status.lower(), Status.SUBMITTING)
